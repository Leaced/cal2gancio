"""
Handles two kinds of tags:

User tags   – iCal CATEGORIES (visible in Gancio).
              additional_tags from config are applied later by the post-processor
              so that all source types benefit from the same logic.
Internal tags – two tags injected into every synced event for stateless tracking:

    _ical_{uid_hash12}    stable lookup key derived from the iCal UID
    _icalv_{hash8}        content fingerprint; changes when event fields change

The content fingerprint allows the sync logic to detect whether a PUT is needed
without keeping any local state file.
"""

import hashlib
import json

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

def parse_categories(component) -> list[str]:
    """Return iCal CATEGORIES as a list of strings. Deduplicates case-insensitively."""
    cats = component.get("CATEGORIES")
    if not cats:
        return []
    if hasattr(cats, "cats"):
        tags = [str(c) for c in cats.cats]
    elif isinstance(cats, list):
        tags = [str(c) for c in cats]
    else:
        tags = [str(cats)]
    seen: set[str] = set()
    result: list[str] = []
    for t in tags:
        if t.lower() not in seen:
            result.append(t)
            seen.add(t.lower())
    return result
