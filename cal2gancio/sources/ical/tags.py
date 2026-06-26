"""
Handles two kinds of tags:

User tags   – iCal CATEGORIES + additional_tags from config (visible in Gancio)
Internal tags – two tags injected into every synced event for stateless tracking:

    _ical_{uid_hash12}    stable lookup key derived from the iCal UID
    _icalv_{hash8}        content fingerprint; changes when event fields change

The content fingerprint allows the sync logic to detect whether a PUT is needed
without keeping any local state file.
"""

import hashlib
import json

from ...config import FeedConfig

UID_PREFIX  = "_ical_"
HASH_PREFIX = "_icalv_"


# ---------------------------------------------------------------------------
# Internal tag construction
# ---------------------------------------------------------------------------

def uid_tag(uid: str) -> str:
    """Stable tag derived from the iCal UID. Never changes for a given event."""
    return UID_PREFIX + hashlib.sha256(uid.encode()).hexdigest()[:12]


def hash_tag(content_hash: str) -> str:
    """Content-fingerprint tag. Changes whenever any event field changes."""
    return HASH_PREFIX + content_hash[:8]


def is_internal(tag: str) -> bool:
    return tag.startswith(UID_PREFIX) or tag.startswith(HASH_PREFIX)


def content_hash(event: dict) -> str:
    """
    SHA-256 of all Gancio-relevant event fields (internal tags excluded).
    Used to detect whether an update is needed.
    """
    stable = {k: event.get(k) for k in [
        "title", "description", "start_datetime", "multidate",
        "place_name", "place_address", "place_latitude", "place_longitude",
        "image_url",
    ]}
    stable["tags"] = sorted(
        t for t in (event.get("tags") or []) if not is_internal(t)
    )
    stable["exdates"] = event.get("_exdates") or []
    raw = json.dumps(stable, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()[:8]


# ---------------------------------------------------------------------------
# User tag parsing
# ---------------------------------------------------------------------------

def parse_categories(component, feed: FeedConfig) -> list[str]:
    """
    Merge iCal CATEGORIES with additional_tags from the feed config.
    Deduplicates case-insensitively; preserves order.
    """
    cats = component.get("CATEGORIES")
    tags: list[str] = []

    if cats:
        if hasattr(cats, "cats"):
            tags = [str(c) for c in cats.cats]
        elif isinstance(cats, list):
            tags = [str(c) for c in cats]
        else:
            tags = [str(cats)]

    seen = {t.lower() for t in tags}
    for t in feed.additional_tags:
        if t.lower() not in seen:
            tags.append(t)
            seen.add(t.lower())

    return tags
