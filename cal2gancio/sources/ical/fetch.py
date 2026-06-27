"""Fetches and parses an iCal feed URL into a list of event dicts."""

import sys

import requests
from icalendar import Calendar

from ...config import FeedConfig
from .event   import build_event


def fetch_events(feed: FeedConfig) -> list[dict]:
    """
    Download the iCal feed and return a list of normalized Gancio event dicts.
    Returns [] on HTTP or parse errors (error printed to stderr).
    """
    try:
        resp = requests.get(feed.url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Fehler beim Abrufen von {feed.url}: {e}", file=sys.stderr)
        return []

    try:
        cal = Calendar.from_ical(resp.content)
    except Exception as e:
        print(f"  Fehler beim Parsen des iCal-Feeds: {e}", file=sys.stderr)
        return []

    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        # RECURRENCE-ID marks a modified/cancelled single occurrence of a recurring
        # series. Skip for now; STATUS:CANCELLED + RECURRENCE-ID will be handled
        # separately when we add cancellation support.
        if component.get("RECURRENCE-ID"):
            continue
        event = build_event(component, feed)
        if event is not None:
            events.append(event)

    return events
