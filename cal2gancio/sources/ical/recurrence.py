"""Maps iCal RRULE to Gancio's recurrence format.

Supported mappings:
  WEEKLY  INTERVAL=1            → 1w
  WEEKLY  INTERVAL=2            → 2w
  MONTHLY INTERVAL=1  no BYDAY  → 1m  (repeats on same day-of-month)
  MONTHLY INTERVAL=2  no BYDAY  → 2m
  YEARLY  INTERVAL=1            → 1y

MONTHLY with BYDAY (ordinal: "first Monday of month") is not supported —
Gancio's ordinal type requires additional params we cannot derive from RRULE alone.
DAILY and other frequencies are not supported by Gancio.
"""

_DAY_MAP = {"MO": 1, "TU": 2, "WE": 3, "TH": 4, "FR": 5, "SA": 6, "SU": 0}


def parse_recurrent(component) -> dict | None:
    """
    Returns {"frequency": str, "days": list} or None.
    Injects as recurrent[frequency] / recurrent[days] in the Gancio payload.
    """
    rrule = component.get("RRULE")
    if not rrule:
        return None

    freq     = (rrule.get("FREQ")     or [None])[0]
    interval = (rrule.get("INTERVAL") or [1])[0]

    if freq == "WEEKLY":
        frequency = "2w" if interval == 2 else "1w"
        days = [_DAY_MAP[d] for d in (rrule.get("BYDAY") or []) if d in _DAY_MAP]
        return {"frequency": frequency, "days": days}

    if freq == "MONTHLY":
        if rrule.get("BYDAY"):
            return None  # ordinal (e.g. "first Monday") — not supported
        frequency = "2m" if interval == 2 else "1m"
        return {"frequency": frequency}

    if freq == "YEARLY" and interval == 1:
        return {"frequency": "1y"}

    return None
