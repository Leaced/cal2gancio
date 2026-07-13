"""
HTML source — scrapes a listing page for event URLs, then builds each event
from an optional per-event iCal file and/or HTML CSS selectors.

Priority when both sources are configured:
    explicit HTML selector value  >  iCal value

Sets event["_event_url"] to the event page URL so the post-processor can
render a clickable link appended after the description body.
"""

import sys
from urllib.parse import urljoin

from ...config import FeedConfig
from ..ical.tags import uid_tag, is_internal
from .discover import discover_event_urls
from .extract import fetch_detail, extract_field, parse_datetime, slug_from_url
from .ical_fallback import fetch_ical_event

_DATETIME_FIELDS = {"start_datetime", "end_datetime"}
_BAR_WIDTH = 25


def _progress(current: int, total: int, url: str) -> None:
    filled = int(_BAR_WIDTH * current / total) if total else _BAR_WIDTH
    bar    = "█" * filled + "░" * (_BAR_WIDTH - filled)
    slug   = url.rstrip("/").split("/")[-1]
    print(f"\r  [{bar}] {current}/{total}  {slug}", end="", flush=True)


def fetch_events(feed: FeedConfig) -> list[dict]:
    cfg = feed.html
    if not cfg.event_link_selector:
        print("  html: event_link_selector ist nicht konfiguriert", file=sys.stderr)
        return []

    base_url = feed.url.rstrip("/")

    try:
        event_entries = discover_event_urls(
            feed.url, cfg.event_link_selector, cfg.event_id_attribute
        )
    except Exception as e:
        print(f"  html: Fehler beim Laden der Listing-Seite: {e}", file=sys.stderr)
        return []

    if cfg.max_events:
        event_entries = event_entries[: cfg.max_events]

    total = len(event_entries)
    print(f"  html: {total} Events werden verarbeitet")

    events = []
    for i, (event_url, event_id) in enumerate(event_entries, 1):
        _progress(i, total, event_url)
        slug = slug_from_url(event_url)

        # --- 1. Fetch detail page HTML -----------------------------------------
        # Must happen first when ical_link_selector is used (the iCal URL is
        # extracted from the detail page HTML, not derived from a pattern).
        soup = None
        try:
            soup = fetch_detail(event_url)
        except Exception as e:
            print(f"  html: Fehler beim Laden von {event_url}: {e}", file=sys.stderr)

        # --- 2. Optional iCal as base -----------------------------------------
        event: dict = {}
        ical_uid_tag: str | None = None

        ical_url: str = ""
        if cfg.ical_link_selector and soup:
            el = soup.select_one(cfg.ical_link_selector)
            if el:
                href = el.get("href", "")
                if href:
                    ical_url = urljoin(event_url, str(href))
        elif cfg.ical_url_pattern:
            ical_url = cfg.ical_url_pattern.format(
                base=base_url, slug=slug, event_id=event_id or slug
            )

        if ical_url:
            ical_event = fetch_ical_event(ical_url)
            if ical_event:
                event = ical_event
                ical_uid_tag = ical_event.get("_uid_tag")

        if not event and soup is None:
            continue

        # --- 3. Apply HTML field selectors (override iCal) --------------------
        if soup is not None:
            for field_name, fs in cfg.fields.items():
                if field_name in _DATETIME_FIELDS:
                    raw = extract_field(soup, fs, event_url)
                    ts = parse_datetime(raw, fs.format)
                    if ts is not None:
                        event[field_name] = ts
                    elif raw and fs.format:
                        fmt_hint = fs.format if isinstance(fs.format, str) else " | ".join(fs.format)
                        print(
                            f"  html: {field_name}: Datum konnte nicht geparst werden "
                            f"(Text: {raw!r}, Format: {fmt_hint!r})",
                            file=sys.stderr,
                        )
                else:
                    val = extract_field(soup, fs, event_url)
                    if val:
                        event[field_name] = val

            # --- 4. Cancelled selector → _cancelled flag ----------------------
            if cfg.cancelled_selector and soup.select_one(cfg.cancelled_selector):
                event["_cancelled"] = True

            # --- 5. Status selectors → extra tags + title prefixes ------------
            extra_tags: list[str] = []
            for ss in cfg.status_selectors:
                if not soup.select_one(ss.selector):
                    continue
                if ss.tag:
                    extra_tags.append(ss.tag)
                if ss.title_prefix:
                    title = event.get("title", "")
                    if not title.startswith(ss.title_prefix):
                        event["title"] = ss.title_prefix + title
            if extra_tags:
                existing = [t for t in (event.get("tags") or []) if not is_internal(t)]
                event["tags"] = existing + extra_tags

        # --- 6. Guard: require title and start_datetime -----------------------
        missing = [f for f, k in [("Titel", "title"), ("Startzeit", "start_datetime")] if not event.get(k)]
        if missing:
            print(f"  html: Überspringe {event_url} — {', '.join(missing)} fehlt", file=sys.stderr)
            continue

        # --- 7. Event URL for post-processor description assembly -------------
        event["_event_url"] = event_url

        # --- 8. Compute multidate from start/end if not already set -----------
        if "multidate" not in event:
            start = event.get("start_datetime", 0)
            end   = event.get("end_datetime", 0)
            event["multidate"] = int(end - start > 86400) if end else 0

        # --- 9. UID (content hash is computed later, after post-processing) ---
        # iCal UID takes priority over URL-derived UID.
        user_tags = [t for t in (event.get("tags") or []) if not is_internal(t)]

        if ical_uid_tag:
            _uid = ical_uid_tag
            uid_is_real = True
        else:
            _uid = uid_tag(event_url)
            uid_is_real = False

        event["_uid_tag"]     = _uid
        event["_uid_is_real"] = uid_is_real
        event["tags"]         = user_tags + [_uid]

        events.append(event)

    print()  # Newline nach der Progress-Bar
    return events
