import json
import os
import sys
import time
import urllib.request


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
    # Get the front page
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = urlopen(top_stories_url)
    top_stories = json.load(response)

    # Decide how many to fetch (the API returns up to 500)
    fetch_limit = int(os.environ.get("FETCH_COUNT", "30"))
    to_fetch = top_stories[:fetch_limit]

    min_score = int(os.environ.get("MIN_SCORE", 0))
    for story_id in to_fetch:
        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        story_resp = urlopen(story_url)
        story = json.load(story_resp)

        if min_score:
            story_score = story.get("score", 0)
            if story_score < min_score:
                continue

        item = {}
        item["id"] = story["id"]

        if story_by := story.get("by"):
            item["author"] = story_by

        if story_time := story.get("time"):
            item["time"] = int(story_time)

        item["body"] = f'<p><a href="https://news.ycombinator.com/item?id={story["id"]}">Link to comments</a></p>'
        if story_text := story.get("text"):
            item["body"] = story_text + item["body"]

        if story_url := story.get("url"):
            item["link"] = story_url

        if story_title := story.get("title"):
            item["title"] = story_title

        item["ttl"] = 60 * 60 * 72  # 72 hours

        print(json.dumps(item))
