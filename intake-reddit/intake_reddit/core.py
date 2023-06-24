import json
import os
import sys
import time
import urllib.request


PAGE_SUFFIX = {
    "hot": "",
    "new": "new/",
    "rising": "rising/",
    "controversial": "controversial/",
    "top": "top/"
}

SORT_TTL = {
    "hour": 60 * 60,
    "day": 60 * 60 * 24,
    "week": 60 * 60 * 24 * 7,
    "month": 60 * 60 * 24 * 31,
    "year": 60 * 60 * 24 * 366,
    "all": 60 * 60 * 24 * 366,
}


def stderr(*args):
    print(*args, file=sys.stderr)


def urlopen(url):
    attempts = int(os.environ.get("REQUEST_RETRY", "6"))
    backoff = 20
    for attempt in range(attempts):
        try:
            return urllib.request.urlopen(url)
        except Exception as ex:
            stderr(f"[{attempt + 1}/{attempts}] Error fetching", url)
            stderr(ex)
            if attempt < attempts - 1:
                stderr("Retrying in", backoff, "seconds")
                time.sleep(backoff)
                backoff *= 2
    else:
        stderr("Failed to fetch in", attempts, "tries")
        return None


def main():
    # Get the subreddit name
    sub_name = os.environ.get("SUBREDDIT_NAME")
    if not sub_name:
        stderr("No SUBREDDIT_NAME defined")
        return 1

    # Fetch the subreddit page and sort type
    sub_page, sub_sort = os.environ.get("SUBREDDIT_PAGE", "hot"), ""
    if "_" in sub_page:
        sub_page, sub_sort = sub_page.split("_", 1)
    if sub_page not in PAGE_SUFFIX:
        stderr("Unknown subreddit page:", sub_page)
        return 1

    # Assemble and fetch the subreddit listing url
    sort_query = "?t=" + sub_sort if sub_sort else ""
    url = f"https://www.reddit.com/r/{sub_name}/{PAGE_SUFFIX[sub_page]}.json{sort_query}"
    stderr("Fetching", url)
    response = urlopen(url)
    if not response:
        stderr("Could not reach", url)
        return 1

    # Parse the reddit API data
    resp_data = response.read().decode("utf8")
    info = json.loads(resp_data)

    # Pull item configuration options from the environment
    filter_nsfw = os.environ.get("FILTER_NSFW", False)
    tag_nsfw = os.environ.get("TAG_NSFW", True)
    filter_spoiler = os.environ.get("FILTER_SPOILER", False)
    tag_spoiler = os.environ.get("TAG_SPOILER", True)
    min_score = int(os.environ.get("MIN_SCORE", 0))
    tags = [tag for tag in os.environ.get("TAGS", "").split(",") if tag]
    author_blocklist = [author for author in os.environ.get("AUTHOR_BLOCKLIST", "").split(",") if author]
    stderr("filter nsfw =", bool(filter_nsfw))
    stderr("tag nsfw =", bool(tag_nsfw))
    stderr("filter spoiler =", bool(filter_spoiler))
    stderr("tag spoiler =", bool(tag_spoiler))
    stderr("min score =", min_score)
    stderr("tags =", ", ".join(tags))
    stderr("author blocklist =", ", ".join(author_blocklist))

    for post in info["data"]["children"]:
        post_data = post["data"]

        # id and tags
        item = {}
        item["id"] = post_data["id"]
        item["tags"] = list(tags)

        # NSFW filter
        is_nsfw = post_data.get("over_18", False)
        if is_nsfw:
            if filter_nsfw:
                continue
            if tag_nsfw:
                item["tags"].append("nsfw")

        # Spoiler filter
        is_spoiler = post_data.get("spoiler", False)
        if is_spoiler:
            if filter_spoiler:
                continue
            if tag_spoiler:
                item["tags"].append("spoiler")

        # Score filter
        post_score = post_data.get("score", 0)
        if min_score and post_score < min_score:
            continue

        # Author filter
        post_author = post_data.get("author")
        if post_author in author_blocklist:
            continue

        # Title
        if post_title := post_data.get("title"):
            sub_prefixed = post_data.get("subreddit_name_prefixed") or f"r/{sub_name}"
            spoiler_part = "[S] " if is_spoiler else ""
            nsfw_part = "[NSFW] " if is_nsfw else ""
            item["title"] = f"{spoiler_part}{nsfw_part}/{sub_prefixed}: {post_title}"

        # Author
        if post_author:
            item["author"] = f"/u/{post_author}"

        # Time
        if post_created := post_data.get("created_utc"):
            item["time"] = int(post_created)

        # Body
        parts = []
        if not post_data.get("is_self"):
            parts.append(f'<i>link:</i> <a href="{post_data.get("url", "")}">{post_data.get("url", "(no url)")}</a>')
        if preview := post_data.get("preview"):
            try:
                previews = preview["images"][0]["resolutions"]
                small_previews = [p for p in previews if p["width"] < 800]
                preview = sorted(small_previews, key=lambda p: -p["width"])[0]
                parts.append(f'<img src="{preview["url"]}">')
            except:
                pass
        if post_data.get("is_gallery", False):
            try:
                for gallery_item in post_data["gallery_data"]["items"]:
                    media_id = gallery_item["media_id"]
                    metadata = post["media_metadata"][media_id]
                    small_previews = [p for p in metadata["p"] if p["x"] < 800]
                    preview = sorted(small_previews, key=lambda p: -p["x"])[0]
                    parts.append(
                        f'<i>link:</i> <a href="{metadata["s"]["u"]}">{metadata["s"]["u"]}</a>'
                    )
                    parts.append(f'<img src="{preview["u"]}">')
            except:
                pass
        if post_selftext := post_data.get("selftext"):
            limit = post_selftext[1024:].find(" ")
            preview_body = post_selftext[: 1024 + limit]
            if len(preview_body) < len(post_selftext):
                preview_body += "[...]"
            parts.append(f"<p>{preview_body}</p>")
        item["body"] = "<br><hr>".join(parts)

        # Link
        if post_link := post_data.get("permalink"):
            item["link"] = f"https://reddit.com{post_link}"

        # TTL
        item["ttl"] = SORT_TTL.get(sub_sort, 60 * 60 * 24 * 8)

        print(json.dumps(item))
