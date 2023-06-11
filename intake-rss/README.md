# intake-sources

This repo contains programs that act as `intake` feed sources.

## intake-rss

A feed source that wraps an RSS or Atom feed.

Supported `env`:

- `FEED_URL`: Required. The url of the RSS/Atom feed.
- `FEED_TITLE`: Override the feed `<title>`. Item titles are in the format "[feed title]: [item title]".

