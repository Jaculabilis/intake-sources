import hashlib
import json
import os
import random


def main():
    item = {}

    title = os.environ.get("TITLE", "Hello, world!")

    if os.environ.get("UNIQUE"):
        item["id"] = hashlib.md5(title.encode("utf8")).hexdigest()
    else:
        item["id"] = "{:x}".format(random.getrandbits(16 * 4))

    item["title"] = title

    if body := os.environ.get("BODY"):
        item["body"] = body

    print(json.dumps(item))
