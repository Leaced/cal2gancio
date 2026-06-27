"""Fetches a listing page and extracts event detail URLs via a CSS selector."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

_HEADERS = {"User-Agent": "cal2gancio/1.0 (+https://github.com/Leaced/cal2gancio)"}


def discover_event_urls(listing_url: str, selector: str) -> list[str]:
    resp = requests.get(listing_url, headers=_HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    seen: set[str] = set()
    urls: list[str] = []
    for el in soup.select(selector):
        href = el.get("href", "").strip()
        if not href:
            continue
        full = urljoin(listing_url, href)
        if full not in seen:
            seen.add(full)
            urls.append(full)
    return urls
