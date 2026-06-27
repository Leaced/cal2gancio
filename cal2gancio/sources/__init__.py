"""
Source dispatcher — maps SourceType to a concrete fetch implementation.

Each fetcher must match the FetchFn signature:
    (feed: FeedConfig, disclaimer: str, event_link_text: str) -> list[dict]

To add a new source type:
    1. Add a value to SourceType in config.py
    2. Implement a fetch function with the above signature
    3. Register it in _FETCHERS below

Post-processing (applied to all source types after fetching):
    - default_place_name / default_place_address fallbacks
    - Title filter (include / exclude)
    - Past-event filter (ignore_past_events)
    - Cancelled-event title prefix (cancelled_prefix from text config)
"""

import time
from collections.abc import Callable

from ..config import FeedConfig, FilterConfig, SourceType, TextConfig
from .ical.fetch import fetch_events as _ical_fetch
from .html.fetch import fetch_events as _html_fetch
from .ical.tags import hash_tag, content_hash, is_internal

FetchFn = Callable[[FeedConfig, str, str], list[dict]]

_FETCHERS: dict[SourceType, FetchFn] = {
    SourceType.ICAL: _ical_fetch,
    SourceType.HTML: _html_fetch,
}


def fetch_for_feed(
    feed: FeedConfig,
    disclaimer: str = "",
    event_link_text: str = "Event details",
    text: TextConfig | None = None,
) -> list[dict]:
    fetcher = _FETCHERS.get(feed.source_type)
    if fetcher is None:
        raise ValueError(f"Unsupported source type: {feed.source_type!r}")
    events = fetcher(feed, disclaimer, event_link_text)
    return _postprocess(events, feed, text or TextConfig())


def _postprocess(events: list[dict], feed: FeedConfig, text: TextConfig) -> list[dict]:
    events = _apply_place_defaults(events, feed)
    events = _apply_filter(events, feed.filter)
    events = _apply_past_filter(events, feed)
    events = _apply_cancelled(events, feed, text)
    events = _apply_content_hash(events)
    return events


def _apply_place_defaults(events: list[dict], feed: FeedConfig) -> list[dict]:
    if not feed.default_place_name and not feed.default_place_address:
        return events
    for event in events:
        if not event.get("place_name") and feed.default_place_name:
            event["place_name"] = feed.default_place_name
        if not event.get("place_address") and feed.default_place_address:
            event["place_address"] = feed.default_place_address
    return events


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


def _apply_past_filter(events: list[dict], feed: FeedConfig) -> list[dict]:
    if not feed.ignore_past_events:
        return events
    now = time.time()
    return [e for e in events if e.get("start_datetime", 0) >= now]


def _apply_content_hash(events: list[dict]) -> list[dict]:
    for event in events:
        user_tags = [t for t in (event.get("tags") or []) if not is_internal(t)]
        uid_tags  = [t for t in (event.get("tags") or []) if t.startswith("_ical_")]
        event["tags"] = user_tags  # strip any stale hash tag before computing
        _hash = hash_tag(content_hash(event))
        event["_hash_tag"] = _hash
        event["tags"] = user_tags + uid_tags + [_hash]
    return events


def _apply_cancelled(events: list[dict], feed: FeedConfig, text: TextConfig) -> list[dict]:
    if feed.delete_cancelled:
        return events
    prefix = text.cancelled
    for event in events:
        if event.get("_cancelled") and prefix:
            if not event["title"].startswith(prefix):
                event["title"] = prefix + event["title"]
    return events
