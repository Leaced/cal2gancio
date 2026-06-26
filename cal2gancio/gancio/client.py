"""
GancioClient – wraps the three API operations used by the sync:

  find_by_uid_tag(uid_tag)       GET  /api/events?tags[]=…
  create_event(event)            POST /api/event
  update_event(gancio_id, event) PUT  /api/event
"""

import time
import urllib.parse

import requests

from .encoding import ApiResult, strip_meta, to_multipart


class GancioClient:
    def __init__(self, base_url: str, token: str | None, request_delay: float = 0.0) -> None:
        self._base    = _resolve_base_url(base_url)
        self._headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._delay   = request_delay

    @property
    def is_anonymous(self) -> bool:
        return not self._headers

    # ── Lookup ────────────────────────────────────────────────────────────

    def find_by_uid_tag(self, uid_tag: str) -> dict | None:
        """
        Search Gancio for an event carrying the given internal uid tag.
        Returns the first matching event dict or None.
        """
        try:
            resp = requests.get(
                f"{self._base}/api/events",
                params={"tags": uid_tag},
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            events = resp.json()
            if isinstance(events, list) and events:
                return events[0]
        except Exception as e:
            print(f"  ⚠ Lookup fehlgeschlagen ({uid_tag}): {e}", flush=True)
        return None

    # ── Write ─────────────────────────────────────────────────────────────

    def create_event(self, event: dict) -> ApiResult:
        """POST /api/event – create a new event."""
        files = to_multipart(strip_meta(event))
        resp, err = self._write(
            lambda: requests.post(
                f"{self._base}/api/event",
                files=files,
                headers=self._headers,
                timeout=20,
            )
        )
        if err:
            return ApiResult(success=False, gancio_id=None, error=err)
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
        payload = strip_meta(event)
        payload["id"] = gancio_id
        files = to_multipart(payload)
        resp, err = self._write(
            lambda: requests.put(
                f"{self._base}/api/event",
                files=files,
                headers=self._headers,
                timeout=20,
            )
        )
        if err:
            return ApiResult(success=False, gancio_id=gancio_id, error=err)
        if resp.status_code in (200, 201):
            return ApiResult(success=True, gancio_id=gancio_id)
        return ApiResult(
            success=False, gancio_id=gancio_id,
            error=f"HTTP {resp.status_code}: {resp.text[:200]}",
        )

    # ── Internal ──────────────────────────────────────────────────────────

    def _write(self, req_fn) -> tuple[requests.Response | None, str | None]:
        """Execute a write request, retry once on 429, then apply the configured delay."""
        try:
            resp = req_fn()
        except requests.RequestException as e:
            return None, str(e)

        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", max(self._delay, 5.0)))
            _wait(retry_after, reason="Rate limit (429)")
            try:
                resp = req_fn()
            except requests.RequestException as e:
                return None, str(e)

        if self._delay > 0:
            _wait(self._delay)

        return resp, None


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _wait(seconds: float, reason: str = "") -> None:
    if seconds > 30:
        label = f"{reason} – " if reason else ""
        print(f"  ⏳ {label}warte {seconds:.0f}s …", flush=True)
    time.sleep(seconds)


def _resolve_base_url(url: str) -> str:
    """Follow redirects once at startup to get the canonical base URL."""
    try:
        resp = requests.get(url, allow_redirects=True, timeout=10)
        parsed = urllib.parse.urlparse(resp.url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return url


def _extract_id(resp: requests.Response) -> int | None:
    try:
        body = resp.json()
        for key in ("id", "event_id"):
            if key in body:
                return int(body[key])
    except Exception:
        pass
    return None
