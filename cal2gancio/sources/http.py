"""Shared HTTP GET helper with retries for transient network/server errors."""

import time

import requests

DEFAULT_HEADERS = {"User-Agent": "cal2gancio/1.0 (+https://github.com/Leaced/cal2gancio)"}

_RETRYABLE_STATUS = {500, 502, 503, 504}


def get(
    url: str,
    *,
    headers: dict | None = None,
    timeout: float = 20,
    retries: int = 2,
    backoff: float = 2.0,
) -> requests.Response:
    """GET with retries on timeouts, connection errors, and 5xx responses.

    Makes up to retries+1 attempts with linear backoff (backoff * attempt number)
    between them. Raises the underlying exception if all attempts fail.
    """
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers or DEFAULT_HEADERS, timeout=timeout)
            if resp.status_code in _RETRYABLE_STATUS and attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp
        except (requests.Timeout, requests.ConnectionError):
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            raise
