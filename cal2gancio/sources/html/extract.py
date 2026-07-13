"""Extracts field values from a BeautifulSoup document using FieldSelectors."""

import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from ...config import FieldSelector
from ..parse_utils import normalize_month_names

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


def _extract_value(el: Tag, fs: FieldSelector, page_url: str = "") -> str:
    """Extract a value from a single already-selected element."""
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

    return value


def extract_field(soup: BeautifulSoup, fs: FieldSelector, page_url: str = "") -> str:
    el = soup.select_one(fs.selector)
    if el is None:
        return ""

    value = _extract_value(el, fs, page_url)

    if fs.time_selector and value:
        time_el = soup.select_one(fs.time_selector)
        if time_el:
            time_text = time_el.get_text(strip=True)
            if time_text:
                value = f"{value} {time_text}"

    return value


def extract_all_fields(soup: BeautifulSoup, fs: FieldSelector, page_url: str = "") -> list[str]:
    """Extract a value from every element matching fs.selector (for multi_match)."""
    return [_extract_value(el, fs, page_url) for el in soup.select(fs.selector)]


def parse_datetime(text: str, fmt: str | list[str]) -> int | None:
    """Parse a date/time string using one or more strptime formats.

    German and English month names (full and 3-letter abbreviations) are
    normalized to two-digit numbers before parsing, so formats like
    ``%d. %m. %Y`` work without locale changes.
    If *fmt* is a list, each format is tried in order; the first match wins.
    """
    if not text or not fmt:
        return None
    text = normalize_month_names(text.strip())
    formats = [fmt] if isinstance(fmt, str) else fmt
    for f in formats:
        try:
            dt = datetime.strptime(text, f)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError:
            continue
    return None


def slug_from_url(url: str) -> str:
    return urlparse(url).path.rstrip("/").split("/")[-1]
