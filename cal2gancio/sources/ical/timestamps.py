"""Converts iCal DTSTART/DTEND values to Unix timestamps."""

from datetime import datetime, timezone


def to_timestamp(dt_prop) -> int:
    dt = dt_prop.dt
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    # date-only → midnight UTC
    return int(datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc).timestamp())
