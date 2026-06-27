"""Fetches a listing page and extracts event detail URLs via a CSS selector."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

_HEADERS = {"User-Agent": "cal2gancio/1.0 (+https://github.com/Leaced/cal2gancio)"}


def discover_event_urls(
    listing_url: str,
    selector: str,
    event_id_attribute: str = "",
) -> list[tuple[str, str | None]]:
    """Return a list of (event_url, event_id) tuples.

    event_id is the value of event_id_attribute on the link element, or None
    when event_id_attribute is not configured.
    """
    resp = requests.get(listing_url, headers=_HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    seen: set[str] = set()
    results: list[tuple[str, str | None]] = []
    for el in soup.select(selector):
        href = el.get("href", "").strip()
        if not href:
            continue
        full = urljoin(listing_url, href)
        if full in seen:
            continue
        seen.add(full)
        event_id = el.get(event_id_attribute, "").strip() if event_id_attribute else None
        results.append((full, event_id or None))
    return results
