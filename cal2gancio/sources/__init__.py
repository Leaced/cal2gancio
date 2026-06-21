"""
Source dispatcher — maps SourceType to a concrete fetch implementation.

Each fetcher must match the signature:
    (feed: FeedConfig, disclaimer: str) -> list[dict]

To add a new source type:
    1. Add a value to SourceType in config.py
    2. Implement a fetch function with the above signature
    3. Register it in _FETCHERS below
"""

from collections.abc import Callable

from ..config import FeedConfig, SourceType
from ..ical.fetch import fetch_events as _ical_fetch

FetchFn = Callable[[FeedConfig, str], list[dict]]

_FETCHERS: dict[SourceType, FetchFn] = {
    SourceType.ICAL: _ical_fetch,
}


def fetch_for_feed(feed: FeedConfig, disclaimer: str = "") -> list[dict]:
    fetcher = _FETCHERS.get(feed.source_type)
    if fetcher is None:
        raise ValueError(f"Unsupported source type: {feed.source_type!r}")
    return fetcher(feed, disclaimer)
