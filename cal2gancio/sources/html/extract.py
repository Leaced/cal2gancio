"""Extracts field values from a BeautifulSoup document using FieldSelectors."""

import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

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


def _html_to_text(el: Tag) -> str:
    """Convert a BS4 element to plain text, preserving block structure.

    Strategy:
    - Block-closing tags (</p>, </div>, <br>, …) → \\n so paragraphs survive.
    - <style>, <script>, and HTML comments (incl. Office XML conditional comments)
      are removed entirely before tag stripping so their content never leaks.
    - Remaining tags are stripped with regex rather than get_text(strip=True);
      this keeps the surrounding whitespace of inline elements like <strong>.
    - HTML entities are decoded, then each line's internal whitespace is collapsed.
    - 3+ consecutive blank lines are reduced to 2 (paragraph cap).
    """
    raw = _BLOCK_TAGS.sub("\n", str(el))
    raw = _STRIP_BLOCKS.sub("", raw)
    raw = unescape(_ALL_TAGS.sub("", raw))
    lines = [" ".join(line.split()) for line in raw.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def extract_field(soup: BeautifulSoup, fs: FieldSelector, page_url: str = "") -> str:
    el = soup.select_one(fs.selector)
    if el is None:
        return ""

    if fs.attribute:
        value = el.get(fs.attribute, "").strip()
        if value and page_url and value.startswith("/"):
            value = urljoin(page_url, value)
    elif fs.as_html:
        value = el.decode_contents().strip()
    elif fs.flat_text:
        value = el.get_text(strip=True)
    else:
        value = _html_to_text(el)

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
