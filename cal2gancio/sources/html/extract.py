"""Extracts field values from a BeautifulSoup document using FieldSelectors."""

import re
from datetime import datetime, timezone
from html import unescape

import requests
from bs4 import BeautifulSoup

from ...config import FieldSelector

_HEADERS = {"User-Agent": "cal2gancio/1.0 (+https://github.com/Leaced/cal2gancio)"}


def fetch_detail(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=_HEADERS, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


_BLOCK_TAGS = re.compile(
    r"<br\s*/?>|</(p|div|h[1-6]|li|tr|blockquote)>",
    re.IGNORECASE,
)
_STRIP_BLOCKS = re.compile(
    r"<style\b[^>]*>.*?</style>|<script\b[^>]*>.*?</script>|<!--.*?-->",
    re.IGNORECASE | re.DOTALL,
)
_ALL_TAGS = re.compile(r"<[^>]+>")


def extract_field(soup: BeautifulSoup, fs: FieldSelector, page_url: str = "") -> str:
    el = soup.select_one(fs.selector)
    if el is None:
        return ""
    if fs.attribute:
        value = el.get(fs.attribute, "").strip()
        if value and page_url and value.startswith("/"):
            from urllib.parse import urljoin
            value = urljoin(page_url, value)
    elif fs.as_html:
        value = el.decode_contents().strip()
    else:
        # 1. Replace block-level tags with \n to preserve paragraph/line structure.
        # 2. Remove <style>, <script>, and HTML comments (incl. Office XML in
        #    <!--[if gte mso 9]>...<![endif]-->) before stripping remaining tags,
        #    so their text content doesn't leak into the output.
        # 3. Strip remaining tags with regex — unlike get_text(strip=True) this preserves
        #    surrounding whitespace, so inline elements like <strong> keep their spaces.
        # 4. Decode HTML entities, then normalise whitespace within each line.
        raw = _BLOCK_TAGS.sub("\n", str(el))
        raw = _STRIP_BLOCKS.sub("", raw)
        raw = unescape(_ALL_TAGS.sub("", raw))
        lines = [" ".join(line.split()) for line in raw.split("\n")]
        value = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    if fs.regex and value:
        m = re.search(fs.regex, value)
        value = (m.group(1) if m and m.lastindex else m.group(0) if m else "")
    if fs.time_selector and value:
        time_el = soup.select_one(fs.time_selector)
        if time_el:
            time_text = time_el.get_text(strip=True)
            if time_text:
                value = f"{value} {time_text}"
    return value


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
