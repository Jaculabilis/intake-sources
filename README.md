# intake-sources

This repo contains programs that act as `intake` feed sources.

## intake-rss

A feed source that wraps an RSS or Atom feed.

Supported `env`:

- `FEED_URL`: Required. The url of the RSS/Atom feed.
- `FEED_TITLE`: Override the feed `<title>`. Item titles are in the format "[feed title]: [item title]".

## intake-reddit

A feed source that fetches posts from a subreddit.

Supported `env`:

- `SUBREDDIT_NAME`: Required. The subreddit name with no `r/` prefix.
- `SUBREDDIT_PAGE`: The listing page to fetch posts from. Defaults to `hot`. Listings that support multiple time ranges can specify as e.g. `top_week`.
- `REQUEST_RETRY`: Attempt count for fetching posts. Retries are done with exponential backoff.
- `FILTER_NSFW`: By default, NSFW posts are included. Set to a truthy value to skip them.
- `TAG_NSFW`: By default, NSFW posts are tagged `nsfw`. Set to an empty string to suppress this.
- `FILTER_SPOILER`: As `FILTER_NSFW` for posts marked as spoilers.
- `TAG_SPOILER`: As `TAG_NSFW` for posts marked as spoilers.
- `MIN_SCORE`: Skip posts with scores below this number.
- `TAGS`: Comma-separated list of tags to add to all items.
- `AUTHOR_BLOCKLIST`: Comma-separated list of usernames. Posts by these users will be skipped.
