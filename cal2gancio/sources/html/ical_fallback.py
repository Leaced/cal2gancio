"""Fetches a single-event iCal URL and parses it into a Gancio event dict."""

from icalendar import Calendar

from .. import http
from ..ical.event import build_event


def fetch_ical_event(ical_url: str) -> dict | None:
    try:
        resp = http.get(ical_url, timeout=15)
        cal = Calendar.from_ical(resp.content)
    except Exception:
        return None

    for component in cal.walk():
        if component.name == "VEVENT":
            try:
                return build_event(component)
            except Exception:
                return None
    return None
