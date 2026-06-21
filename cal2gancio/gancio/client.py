"""
GancioClient – wraps the three API operations used by the sync:

  find_by_uid_tag(uid_tag)       GET  /api/events?tags[]=…
  create_event(event)            POST /api/event
  update_event(gancio_id, event) PUT  /api/event
"""

import requests

from .encoding import ApiResult, strip_meta, to_multipart


class GancioClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._base    = base_url
        self._headers = {"Authorization": f"Bearer {token}"}

    # ── Lookup ────────────────────────────────────────────────────────────

    def find_by_uid_tag(self, uid_tag: str) -> dict | None:
        """
        Search Gancio for an event carrying the given internal uid tag.
        Returns the first matching event dict or None.
        """
        try:
            resp = requests.get(
                f"{self._base}/api/events",
                params={"tags[]": uid_tag},
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            events = resp.json()
            if isinstance(events, list) and events:
                return events[0]
        except Exception:
            pass
        return None

    # ── Write ─────────────────────────────────────────────────────────────

    def create_event(self, event: dict) -> ApiResult:
        """POST /api/event – create a new event."""
        try:
            resp = requests.post(
                f"{self._base}/api/event",
                files=to_multipart(strip_meta(event)),
                headers=self._headers,
                timeout=20,
            )
        except requests.RequestException as e:
            return ApiResult(success=False, gancio_id=None, error=str(e))

        if resp.status_code in (200, 201):
            return ApiResult(success=True, gancio_id=_extract_id(resp))
        return ApiResult(
            success=False, gancio_id=None,
            error=f"HTTP {resp.status_code}: {resp.text[:200]}",
        )

    def update_event(self, gancio_id: int, event: dict) -> ApiResult:
        """
        PUT /api/event – update an existing event.
        Sends the full tag list, so stale internal tags are naturally replaced.
        """
        payload      = strip_meta(event)
        payload["id"] = gancio_id
        try:
            resp = requests.put(
                f"{self._base}/api/event",
                files=to_multipart(payload),
                headers=self._headers,
                timeout=20,
            )
        except requests.RequestException as e:
            return ApiResult(success=False, gancio_id=gancio_id, error=str(e))

        if resp.status_code in (200, 201):
            return ApiResult(success=True, gancio_id=gancio_id)
        return ApiResult(
            success=False, gancio_id=gancio_id,
            error=f"HTTP {resp.status_code}: {resp.text[:200]}",
        )


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _extract_id(resp: requests.Response) -> int | None:
    try:
        body = resp.json()
        for key in ("id", "event_id"):
            if key in body:
                return int(body[key])
    except Exception:
        pass
    return None
