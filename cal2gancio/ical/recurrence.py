"""Maps iCal RRULE to Gancio's recurrence format.

Gancio only supports weekly recurrence (1w / 2w).
All other frequencies (daily, monthly, yearly) are silently ignored —
the event is then imported as a single occurrence.
"""

_DAY_MAP = {"MO": 1, "TU": 2, "WE": 3, "TH": 4, "FR": 5, "SA": 6, "SU": 0}


def parse_recurrent(component) -> dict | None:
    """
    Returns {"frequency": "1w"|"2w", "days": [...]} or None.
    Injects as recurrent[frequency] / recurrent[days] in the Gancio payload.
    """
    rrule = component.get("RRULE")
    if not rrule:
        return None

    freq = (rrule.get("FREQ") or [None])[0]
    if freq != "WEEKLY":
        return None

    interval  = (rrule.get("INTERVAL") or [1])[0]
    frequency = "2w" if interval == 2 else "1w"
    days      = [_DAY_MAP[d] for d in (rrule.get("BYDAY") or []) if d in _DAY_MAP]

    return {"frequency": frequency, "days": days}
