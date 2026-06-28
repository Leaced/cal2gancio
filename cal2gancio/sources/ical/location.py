"""Parses LOCATION and GEO from a VEVENT component."""


def parse_location(component) -> dict:
    """
    Parse iCal LOCATION into place_name + place_address.
    Splits "Venue Name, Street, City" into place_name + place_address.
    Feed-level defaults are applied by the source dispatcher, not here.
    """
    raw = str(component.get("LOCATION", "")).strip()
    if not raw:
        return {}
    parts = [p.strip() for p in raw.split(",", 1)]
    return {"place_name": parts[0], "place_address": raw}


def parse_geo(component) -> dict:
    """Returns place_latitude / place_longitude if a GEO field is present."""
    geo = component.get("GEO")
    if geo:
        return {"place_latitude": geo.latitude, "place_longitude": geo.longitude}
    return {}
