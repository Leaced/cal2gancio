"""Shared parsing utilities, available to all source types."""

import re

_MONTHS: dict[str, str] = {
    # German
    "januar": "01", "februar": "02", "märz": "03", "april": "04",
    "mai": "05", "juni": "06", "juli": "07", "august": "08",
    "september": "09", "oktober": "10", "november": "11", "dezember": "12",
    # English
    "january": "01", "february": "02", "march": "03",
    "june": "06", "july": "07",
    "october": "10", "december": "12",
    # English abbreviations (3-letter, unambiguous ones only)
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}
_MONTH_RE = re.compile(
    r"\b(" + "|".join(sorted(_MONTHS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def normalize_month_names(text: str) -> str:
    """Replace month names (German and English, full and abbreviated) with zero-padded numbers.

    Examples:
      "7. Juli 2026"      → "7. 07 2026"
      "July 4, 2026"      → "04 4, 2026"   (use format ``%m %d, %Y``)
      "04 Jun 2026 20:00" → "04 06 2026 20:00"
    """
    return _MONTH_RE.sub(lambda m: _MONTHS[m.group(1).lower()], text)
