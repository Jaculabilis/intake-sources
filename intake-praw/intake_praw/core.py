import importlib.metadata
import json
import os
import re
import sys

import praw


SORT_TTL = {
    "hour": 60 * 60,
    "day": 60 * 60 * 24,
    "week": 60 * 60 * 24 * 7,
    "month": 60 * 60 * 24 * 31,
    "year": 60 * 60 * 24 * 366,
    "all": 60 * 60 * 24 * 366,
}

VERSION = importlib.metadata.version(__package__)


def stderr(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def main():
    # Get the reddit client
    client_id = os.environ.get("CLIENT_ID")
    if not client_id:
        stderr("CLIENT_ID required")
        return 1

    client_secret = os.environ.get("CLIENT_SECRET")
    if not client_secret:
        stderr("CLIENT_SECRET required")
        return 1

    user_agent = os.environ.get("USER_AGENT", f"nixos:{__package__}:{VERSION}")

    reddit = praw.Reddit(
        client_id=client_id, client_secret=client_secret, user_agent=user_agent
    )

    # Get the subreddit
    sub_name = os.environ.get("SUBREDDIT_NAME")
    if not sub_name:
        stderr("No SUBREDDIT_NAME defined")
        return 1
    subreddit = reddit.subreddit(sub_name)
    post_limit = int(os.environ.get("POST_LIMIT", "25"))

    # Get the listing page
    sub_page, sub_sort = os.environ.get("SUBREDDIT_PAGE", "hot"), ""
    if "_" in sub_page:
        sub_page, sub_sort = sub_page.split("_", 1)
    if sub_sort:
        stderr(f"Fetching {post_limit} posts from r/{sub_name}/{sub_page}?t={sub_sort}")
    else:
        stderr(f"Fetching {post_limit} posts from r/{sub_name}/{sub_page}")

    if sub_page == "hot":
        posts = subreddit.hot(limit=post_limit)
    elif sub_page == "new":
        posts = subreddit.new(limit=post_limit)
    elif sub_page == "top":
        posts = subreddit.top(limit=post_limit, time_filter=sub_sort)
    elif sub_page == "rising":
        posts = subreddit.top(limit=post_limit)
    elif sub_page == "controversial":
        posts = subreddit.top(limit=post_limit, time_filter=sub_sort)
    else:
        stderr("Invalid subreddit page", sub_page)
        return 1

    # Pull item configuration options from the environment
    filter_nsfw = os.environ.get("FILTER_NSFW", False)
    filter_spoiler = os.environ.get("FILTER_SPOILER", False)
    min_score = int(os.environ.get("MIN_SCORE", 0))
    tags = [tag for tag in os.environ.get("TAGS", "").split(",") if tag]
    no_video = os.environ.get("NO_VIDEO", False)

    stderr("filter nsfw =", bool(filter_nsfw))
    stderr("filter spoiler =", bool(filter_spoiler))
    stderr("min score =", min_score)
    stderr("tags =", ", ".join(tags))
    stderr("no video =", bool(no_video))

    for post in posts:
        # Fill in some basic tags
        item = {}
        item["id"] = post.id
        item["title"] = f"/{post.subreddit_name_prefixed}: {post.title}"
        item["author"] = f"/u/{post.author.name}" if post.author else "[deleted]"
        item["link"] = f"https://reddit.com{post.permalink:}"
        item["time"] = post.created_utc
        item["tags"] = list(tags)
        item["ttl"] = SORT_TTL.get(sub_sort, 60 * 60 * 24 * 8)

        # Special handling for native video posts
        if "v.redd" in post.url:
            if no_video:
                continue
            item["title"] = "[V] " + item["title"]

        # Special handling for NSFW
        if post.over_18:
            if filter_nsfw:
                continue
            item["title"] = "[NSFW] " + item["title"]
            item["tags"].append("nsfw")

        # Special handling for spoilers
        if post.spoiler:
            if filter_spoiler:
                continue
            item["title"] = "[S] " + item["title"]
            item["tags"].append("spoiler")

        # Post score
        if min_score and post.score < min_score:
            continue

        # Body
        parts = []
        if not post.is_self:
            parts.append(f'<i>link:</i> <a href="{post.url}">{post.url}</a>')
        if hasattr(post, "preview"):
            try:
                previews = post.preview["images"][0]["resolutions"]
                small_previews = [p for p in previews if p["width"] < 800]
                preview = sorted(small_previews, key=lambda p: -p["width"])[0]
                parts.append(f'<img src="{preview["url"]}">')
            except:
                pass
        if getattr(post, "is_gallery", False):
            try:
                for gallery_item in post.gallery_data["items"]:
                    media_id = gallery_item["media_id"]
                    metadata = post.media_metadata[media_id]
                    small_previews = [p for p in metadata["p"] if p["x"] < 800]
                    preview = sorted(small_previews, key=lambda p: -p["x"])[0]
                    preview_url = metadata["s"]["u"]
                    if match := re.search(r"redd\.it/([A-Za-z0-9]*\....)", preview_url):
                        preview_url = "https://i.redd.it/" + match.group(1)
                    parts.append(
                        f'<i>link:</i> <a href="{metadata["s"]["u"]}">{preview_url}</a>'
                    )
                    parts.append(f'<img src="{preview["u"]}">')
            except:
                pass
        if post.selftext:
            limit = post.selftext[1024:].find(" ")
            preview_body = post.selftext[: 1024 + limit]
            if len(preview_body) < len(post.selftext):
                preview_body += "[...]"
            parts.append(f"<p>{preview_body}</p>")
        item["body"] = "<br><hr>".join(parts)

        print(json.dumps(item))
