"""
Converts a single iCal VEVENT component into a normalized Gancio event dict.

The returned dict contains:
  - All Gancio API fields (title, description, start_datetime, …)
  - Internal meta-fields prefixed with "_" (stripped before sending to API):
      _uid_tag      stable lookup tag, e.g. "_ical_abc123def456"
      _hash_tag     content fingerprint tag, e.g. "_icalv_a1b2c3d4"
      _uid_is_real  False if the UID was generated from title+timestamp
"""

from ..config import FeedConfig
from .location   import parse_location, parse_geo
from .media      import parse_image_url
from .recurrence import parse_recurrent
from .tags       import parse_categories, uid_tag, hash_tag, content_hash
from .timestamps import to_timestamp


def build_event(component, feed: FeedConfig, disclaimer: str = "") -> dict | None:
    """
    Convert a VEVENT to a Gancio event dict.
    Returns None if the component has no DTSTART (unparseable).
    """
    dtstart = component.get("DTSTART")
    if not dtstart:
        return None

    start_ts = to_timestamp(dtstart)
    title    = str(component.get("SUMMARY", "(kein Titel)")).strip()

    dtend     = component.get("DTEND")
    multidate = int(dtend is not None and to_timestamp(dtend) - start_ts > 86400)

    # Recurrence → Gancio flat keys
    recurrent   = parse_recurrent(component)
    rec_fields  = {}
    if recurrent:
        rec_fields["recurrent[frequency]"] = recurrent["frequency"]
        if recurrent.get("days"):
            rec_fields["recurrent[days]"] = recurrent["days"]

    user_tags = parse_categories(component, feed)
    image_url = parse_image_url(component)

    description = str(component.get("DESCRIPTION", "")).strip()
    if disclaimer:
        if description:
            description = f"{description}\n\n<hr>\n\n{disclaimer}"
        else:
            description = disclaimer

    event: dict = {
        "title":          title,
        "description":    description,
        "start_datetime": start_ts,
        "multidate":      multidate,
        **parse_location(component, feed),
        **parse_geo(component),
    }
    if user_tags:
        event["tags"] = user_tags
    if image_url:
        event["image_url"] = image_url
    event.update(rec_fields)

    # Derive identity and content fingerprint
    raw_uid     = str(component.get("UID", "")).strip()
    uid_is_real = bool(raw_uid)
    uid         = raw_uid if uid_is_real else f"noid::{title}::{start_ts}"

    _uid_tag  = uid_tag(uid)
    _hash_tag = hash_tag(content_hash(event))

    # Inject internal tags into the tag list (sent to Gancio, used for lookup)
    event["tags"] = (event.get("tags") or []) + [_uid_tag, _hash_tag]

    event["_uid_tag"]     = _uid_tag
    event["_hash_tag"]    = _hash_tag
    event["_uid_is_real"] = uid_is_real

    return event
