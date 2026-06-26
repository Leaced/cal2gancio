"""
Decides what to do with a single event: create, update, or skip.

Decision table (authenticated):
  ┌──────────────────────────────────────────────────┬─────────────────┐
  │ Lookup result                                    │ Action          │
  ├──────────────────────────────────────────────────┼─────────────────┤
  │ No Gancio event found for _uid_tag               │ create (POST)   │
  │ Found, _hash_tag matches → content unchanged     │ skip            │
  │ Found, _hash_tag differs  → content changed      │ update (PUT)    │
  │ Found, but gancio_id missing (corrupt response)  │ create (re-POST)│
  └──────────────────────────────────────────────────┴─────────────────┘

Anonymous mode: PUT requires auth, so content changes trigger a new POST
with a warning. Pending events are invisible to the lookup; only already-
published (approved) versions of the event can be detected.
Gancio rejects anonymous POSTs for past events (HTTP 400); the check is
done locally to avoid the failed request.
"""

import time

from ..gancio.client import GancioClient


def sync_event(event: dict, client: GancioClient) -> str:
    """
    Sync one event. Returns a short status string for logging:
    "erstellt" | "aktualisiert" | "unverändert" | "erstellt (Duplikat)" |
    "vergangen" | "Fehler: …"
    """
    uid_tag  = event["_uid_tag"]
    hash_tag = event["_hash_tag"]

    existing = client.find_by_uid_tag(uid_tag)

    # ── New ───────────────────────────────────────────────────────────────
    if existing is None:
        if client.is_anonymous and _is_past(event):
            return "vergangen"
        result = client.create_event(event)
        return "erstellt" if result.success else f"Fehler: {result.error}"

    # ── Unchanged? ────────────────────────────────────────────────────────
    existing_tags = _extract_tags(existing)
    if hash_tag in existing_tags:
        return "unverändert"

    # ── Content changed ───────────────────────────────────────────────────
    if client.is_anonymous:
        # PUT requires auth; past events can't be re-created either
        if _is_past(event):
            return "vergangen"
        result = client.create_event(event)
        return "erstellt (Duplikat)" if result.success else f"Fehler: {result.error}"

    gancio_id = existing.get("id")
    if not gancio_id:
        result = client.create_event(event)
        return "neu erstellt (ID fehlt)" if result.success else f"Fehler: {result.error}"

    result = client.update_event(gancio_id, event)
    return "aktualisiert" if result.success else f"Fehler: {result.error}"


def _is_past(event: dict) -> bool:
    return event.get("start_datetime", 0) < time.time()


def _extract_tags(gancio_event: dict) -> list[str]:
    """Normalize tag list from a Gancio event response (handles str or object)."""
    raw = gancio_event.get("Tags") or gancio_event.get("tags") or []
    return [t if isinstance(t, str) else t.get("tag", "") for t in raw]
