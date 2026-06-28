"""
Converts a single iCal VEVENT component into a normalized Gancio event dict.

The returned dict contains:
  - All Gancio API fields (title, description, start_datetime, …)
  - Internal meta-fields prefixed with "_" (stripped before sending to API):
      _uid_tag      stable lookup tag, e.g. "_ical_abc123def456"
      _uid_is_real  False if the UID was generated from title+timestamp
      _exdates      sorted list of excluded recurrence timestamps (for hash only)
      _hash_tag is NOT set here; it is added later by the post-processor.
"""

from datetime import datetime, timezone

from .location   import parse_location, parse_geo
from .media      import parse_image_url
from .recurrence import parse_recurrent
from .tags       import parse_categories, uid_tag
from .timestamps import to_timestamp

def _end_from_duration(dtstart_prop, duration_prop) -> int | None:
    """Compute end Unix timestamp from DTSTART + DURATION."""
    try:
        start_dt = dtstart_prop.dt
        if not isinstance(start_dt, datetime):
            start_dt = datetime(start_dt.year, start_dt.month, start_dt.day, tzinfo=timezone.utc)
        elif start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        return int((start_dt + duration_prop.dt).timestamp())
    except Exception:
        return None


def _parse_exdates(component) -> list[int]:
    """Return sorted Unix timestamps of all EXDATE entries."""
    prop = component.get("EXDATE")
    if not prop:
        return []
    if not isinstance(prop, list):
        prop = [prop]
    timestamps = []
    for entry in prop:
        dts = getattr(entry, "dts", None)
        if dts is not None:
            for dt_item in dts:
                try:
                    timestamps.append(to_timestamp(dt_item))
                except Exception:
                    pass
        else:
            try:
                timestamps.append(to_timestamp(entry))
            except Exception:
                pass
    return sorted(set(timestamps))


def build_event(component) -> dict | None:
    """
    Convert a VEVENT to a Gancio event dict.
    Returns None if the component has no DTSTART (unparseable).

    Sets event["_event_url"] when the VEVENT has a URL field; the post-processor
    will render it as a clickable link appended after the description body.

    STATUS:CANCELLED sets _cancelled=True; title prefixing and delete decisions
    are handled by the source dispatcher post-processor, not here.
    """
    dtstart = component.get("DTSTART")
    if not dtstart:
        return None

    start_ts  = to_timestamp(dtstart)
    title     = str(component.get("SUMMARY", "(kein Titel)")).strip()
    cancelled = str(component.get("STATUS", "")).strip().upper() == "CANCELLED"

    dtend = component.get("DTEND")
    if dtend is not None:
        multidate = int(to_timestamp(dtend) - start_ts > 86400)
    else:
        duration = component.get("DURATION")
        if duration is not None:
            end_ts    = _end_from_duration(dtstart, duration)
            multidate = int(end_ts is not None and end_ts - start_ts > 86400)
        else:
            multidate = 0

    # Recurrence → Gancio flat keys
    recurrent   = parse_recurrent(component)
    rec_fields  = {}
    if recurrent:
        rec_fields["recurrent[frequency]"] = recurrent["frequency"]
        if recurrent.get("days"):
            rec_fields["recurrent[days]"] = recurrent["days"]

    user_tags = parse_categories(component)
    image_url = parse_image_url(component)
    exdates   = _parse_exdates(component)

    url         = str(component.get("URL", "")).strip()
    description = str(component.get("DESCRIPTION", "")).strip()

    event: dict = {
        "title":          title,
        "description":    description,
        "start_datetime": start_ts,
        "multidate":      multidate,
        **parse_location(component),
        **parse_geo(component),
    }
    if user_tags:
        event["tags"] = user_tags
    if image_url:
        event["image_url"] = image_url
    if exdates:
        event["_exdates"] = exdates
    if cancelled:
        event["_cancelled"] = True
    if url:
        event["_event_url"] = url
    event.update(rec_fields)

    # Derive stable identity (content hash is computed later, after post-processing)
    raw_uid     = str(component.get("UID", "")).strip()
    uid_is_real = bool(raw_uid)
    uid         = raw_uid if uid_is_real else f"noid::{title}::{start_ts}"

    _uid_tag = uid_tag(uid)

    event["tags"]         = (event.get("tags") or []) + [_uid_tag]
    event["_uid_tag"]     = _uid_tag
    event["_uid_is_real"] = uid_is_real

    return event
