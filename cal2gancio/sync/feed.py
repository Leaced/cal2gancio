"""Iterates over all configured feeds and syncs each event."""

from ..config      import AppConfig, FeedConfig
from ..gancio      import GancioClient, get_token
from ..sources     import fetch_for_feed
from .decision     import sync_event

_ICONS = {"erstellt": "✓", "aktualisiert": "✓", "unverändert": "="}


def sync_feed(feed: FeedConfig, client: GancioClient, disclaimer: str = "") -> None:
    print(f"\n→ {feed.url}")
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
    client = GancioClient(cfg.gancio_url, token)

    if cfg.username:
        print(f"Angemeldet als {cfg.username} @ {cfg.gancio_url}")
    else:
        print(f"Anonym @ {cfg.gancio_url}")

    for feed in cfg.feeds:
        sync_feed(feed, client, cfg.disclaimer)

    print("\nFertig.")
