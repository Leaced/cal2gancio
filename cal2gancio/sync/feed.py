"""Iterates over all configured feeds and syncs each event."""

from ..config      import AppConfig, FeedConfig
from ..gancio      import GancioClient, get_token
from ..sources     import fetch_for_feed
from .decision     import sync_event

_ICONS = {"erstellt": "✓", "aktualisiert": "✓", "unverändert": "="}


def sync_feed(feed: FeedConfig, client: GancioClient, global_disclaimer: str = "") -> None:
    print(f"\n→ {feed.url}")
    disclaimer = feed.disclaimer if feed.disclaimer else global_disclaimer
    events = fetch_for_feed(feed, disclaimer)

    if not events:
        print("  (keine Events oder Abruf fehlgeschlagen)")
        return

    counts: dict[str, int] = {"erstellt": 0, "aktualisiert": 0, "unverändert": 0, "Fehler": 0}

    for event in events:
        status  = sync_event(event, client)
        icon    = _ICONS.get(status, "✗")
        warning = "" if event.get("_uid_is_real", True) else "  ⚠ kein UID im Feed"
        print(f"  {icon} {event['title']} [{status}]{warning}")

        bucket = next((k for k in counts if k in status), "Fehler")
        counts[bucket] += 1

    print(
        f"  → {counts['erstellt']} erstellt, {counts['aktualisiert']} aktualisiert, "
        f"{counts['unverändert']} unverändert, {counts['Fehler']} Fehler"
    )


def sync_all(cfg: AppConfig) -> None:
    token  = get_token(cfg.gancio_url, cfg.username, cfg.password) if cfg.username else None
    client = GancioClient(cfg.gancio_url, token, request_delay=cfg.request_delay)

    if cfg.username:
        print(f"Angemeldet als {cfg.username} @ {cfg.gancio_url}")
    else:
        print(f"Anonym @ {cfg.gancio_url}")
        print("  ⚠ Anonymer Modus: Events werden nur erstellt, nicht aktualisiert")
        print("    (Gancio stellt anonyme Events in Pending – Lookup nicht möglich)")

    for feed in cfg.feeds:
        sync_feed(feed, client, global_disclaimer=cfg.disclaimer)

    print("\nFertig.")
