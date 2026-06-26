"""
Source dispatcher — maps SourceType to a concrete fetch implementation.

Each fetcher must match the signature:
    (feed: FeedConfig, disclaimer: str, event_link_text: str,
     cancelled_prefix: str | None) -> list[dict]

To add a new source type:
    1. Add a value to SourceType in config.py
    2. Implement a fetch function with the above signature
    3. Register it in _FETCHERS below
"""

from collections.abc import Callable

from ..config import FeedConfig, FilterConfig, SourceType
from .ical.fetch import fetch_events as _ical_fetch

FetchFn = Callable[[FeedConfig, str, str, "str | None"], list[dict]]

_FETCHERS: dict[SourceType, FetchFn] = {
    SourceType.ICAL: _ical_fetch,
}


def fetch_for_feed(
    feed: FeedConfig,
    disclaimer: str = "",
    event_link_text: str = "Event details",
    cancelled_prefix: str | None = "Cancelled: ",
) -> list[dict]:
    fetcher = _FETCHERS.get(feed.source_type)
    if fetcher is None:
        raise ValueError(f"Unsupported source type: {feed.source_type!r}")
    events = fetcher(feed, disclaimer, event_link_text, cancelled_prefix)
    return _apply_filter(events, feed.filter)


def _apply_filter(events: list[dict], f: FilterConfig) -> list[dict]:
    if f.include:
        events = [
            e for e in events
            if any(s.lower() in e.get("title", "").lower() for s in f.include)
        ]
    if f.exclude:
        events = [
            e for e in events
            if not any(s.lower() in e.get("title", "").lower() for s in f.exclude)
        ]
    return events
