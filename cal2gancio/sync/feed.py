"""Iterates over all configured feeds and syncs each event."""

import time

from ..config      import AppConfig, FeedConfig
from ..gancio      import GancioClient, get_token
from ..sources     import fetch_for_feed
from .decision     import sync_event

_ICONS = {"erstellt": "✓", "aktualisiert": "✓", "unverändert": "=", "vergangen": "=", "erstellt (Duplikat)": "⚠"}


def sync_feed(feed: FeedConfig, client: GancioClient, global_disclaimer: str = "", global_link_text: str = "Event details") -> None:
    print(f"\n→ {feed.url}")
    disclaimer      = feed.disclaimer       if feed.disclaimer       else global_disclaimer
    event_link_text = feed.event_link_text  if feed.event_link_text  else global_link_text
    events = fetch_for_feed(feed, disclaimer, event_link_text)

    if not events:
        print("  (keine Events oder Abruf fehlgeschlagen)")
        return

    if feed.ignore_past_events:
        now = time.time()
        before = len(events)
        events = [e for e in events if e.get("start_datetime", 0) >= now]
        skipped = before - len(events)
        if skipped:
            print(f"  (vergangene Events übersprungen: {skipped})")

    counts: dict[str, int] = {"erstellt": 0, "aktualisiert": 0, "unverändert": 0, "vergangen": 0, "Duplikat": 0, "Fehler": 0}

    for event in events:
        status  = sync_event(event, client)
        icon    = _ICONS.get(status, "✗")
        warning = "" if event.get("_uid_is_real", True) else "  ⚠ kein UID im Feed"
        print(f"  {icon} {event['title']} [{status}]{warning}")

        if status == "erstellt (Duplikat)":
            counts["Duplikat"] += 1
        elif status == "vergangen":
            counts["vergangen"] += 1
        else:
            bucket = next((k for k in counts if k in status), "Fehler")
            counts[bucket] += 1

    parts = [
        f"{counts['erstellt']} erstellt",
        f"{counts['aktualisiert']} aktualisiert",
        f"{counts['unverändert']} unverändert",
    ]
    if counts["vergangen"]:
        parts.append(f"{counts['vergangen']} vergangen")
    if counts["Duplikat"]:
        parts.append(f"{counts['Duplikat']} Duplikat(e) ⚠")
    parts.append(f"{counts['Fehler']} Fehler")
    print(f"  → {', '.join(parts)}")


def sync_all(cfg: AppConfig) -> None:
    token  = get_token(cfg.gancio_url, cfg.username, cfg.password, cfg.gancio_version) if cfg.username else None
    client = GancioClient(cfg.gancio_url, token, request_delay=cfg.request_delay)

    if cfg.username:
        print(f"Angemeldet als {cfg.username} @ {cfg.gancio_url}")
    else:
        print(f"Anonym @ {cfg.gancio_url}")
        print("  ⚠ Anonymer Modus: Events werden nur erstellt, nicht aktualisiert")
        print("    (Gancio stellt anonyme Events in Pending – Lookup nicht möglich)")

    for feed in cfg.feeds:
        sync_feed(feed, client, global_disclaimer=cfg.disclaimer, global_link_text=cfg.event_link_text)

    print("\nFertig.")
