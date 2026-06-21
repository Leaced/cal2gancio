"""Parses LOCATION and GEO from a VEVENT component."""

from ..config import FeedConfig


def parse_location(component, feed: FeedConfig) -> dict:
    """
    Use iCal LOCATION if present; fall back to feed-level defaults.
    Splits "Venue Name, Street, City" into place_name + place_address.
    """
    raw = str(component.get("LOCATION", "")).strip()
    if raw:
        parts = [p.strip() for p in raw.split(",", 1)]
        return {"place_name": parts[0], "place_address": raw}

    result = {}
    if feed.default_place_name:
        result["place_name"] = feed.default_place_name
    if feed.default_place_address:
        result["place_address"] = feed.default_place_address
    return result


def parse_geo(component) -> dict:
    """Returns place_latitude / place_longitude if a GEO field is present."""
    geo = component.get("GEO")
    if geo:
        return {"place_latitude": geo.latitude, "place_longitude": geo.longitude}
    return {}
