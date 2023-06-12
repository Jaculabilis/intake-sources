import hashlib
import json
import os
import sys
import time

import feedparser


def stderr(*args):
    print(*args, file=sys.stderr)


def main():
    feed_url = os.environ.get("FEED_URL")
    if not feed_url:
        stderr("No FEED_URL defined")
        return 1

    feed = feedparser.parse(feed_url)
    if feed.bozo:
        stderr("Failed to parse feed", feed_url)
        return 1

    feed_title = os.environ.get("FEED_TITLE") or feed.feed.get("title")

    for entry in feed.entries:
        item = {}

        entry_link = entry.get("link")
        id_basis = entry_link or entry.get("id") or str(entry)
        item["id"] = hashlib.md5(id_basis.encode("utf8")).hexdigest()

        entry_title = entry.get("title", "(No title)")
        if feed_title:
            item["title"] = f"{feed_title}: {entry_title}"
        else:
            item["title"] = entry_title

        if entry_pubparsed := entry.get("published_parsed"):
            item["time"] = int(time.mktime(entry_pubparsed))

        if entry_desc := entry.get("summary"):
            item["body"] = entry_desc

        if entry_link:
            item["link"] = entry_link

        print(json.dumps(item))
