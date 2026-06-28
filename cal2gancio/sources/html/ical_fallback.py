"""Fetches a single-event iCal URL and parses it into a Gancio event dict."""

import requests
from icalendar import Calendar

from ..ical.event import build_event

_HEADERS = {"User-Agent": "cal2gancio/1.0 (+https://github.com/Leaced/cal2gancio)"}


def fetch_ical_event(ical_url: str) -> dict | None:
    try:
        resp = requests.get(ical_url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        cal = Calendar.from_ical(resp.content)
    except Exception:
        return None

    for component in cal.walk():
        if component.name == "VEVENT":
            return build_event(component)
    return None
