"""Extracts field values from a BeautifulSoup document using FieldSelectors."""

from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from ...config import FieldSelector

_HEADERS = {"User-Agent": "cal2gancio/1.0 (+https://github.com/Leaced/cal2gancio)"}


def fetch_detail(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=_HEADERS, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def extract_field(soup: BeautifulSoup, fs: FieldSelector, page_url: str = "") -> str:
    el = soup.select_one(fs.selector)
    if el is None:
        return ""
    if fs.attribute:
        value = el.get(fs.attribute, "").strip()
        if value and page_url and value.startswith("/"):
            from urllib.parse import urljoin
            value = urljoin(page_url, value)
        return value
    if fs.as_html:
        return el.decode_contents().strip()
    return el.get_text(separator=" ", strip=True)


def parse_datetime(text: str, fmt: str) -> int | None:
    if not text or not fmt:
        return None
    try:
        dt = datetime.strptime(text.strip(), fmt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except ValueError:
        return None


def slug_from_url(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).path.rstrip("/").split("/")[-1]
