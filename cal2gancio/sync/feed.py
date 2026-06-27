"""Iterates over all configured feeds and syncs each event."""

from ..config      import AppConfig, FeedConfig, TextConfig
from ..gancio      import GancioClient, get_token
from ..sources     import fetch_for_feed
from .decision     import delete_cancelled_event, sync_event

_ICONS = {
    "erstellt":          "✓",
    "aktualisiert":      "✓",
    "gelöscht":          "✓",
    "unverändert":       "=",
    "vergangen":         "=",
    "nicht gefunden":    "=",
    "erstellt (Duplikat)": "⚠",
}


def sync_feed(
    feed: FeedConfig,
    client: GancioClient,
    global_disclaimer: str = "",
    global_text: TextConfig | None = None,
) -> None:
    if global_text is None:
        global_text = TextConfig()

    print(f"\n→ {feed.url}")
    disclaimer      = feed.disclaimer      if feed.disclaimer      else global_disclaimer
    event_link_text = feed.event_link_text if feed.event_link_text else global_text.event_link

    events = fetch_for_feed(feed, disclaimer, event_link_text, text=global_text)

    if not events:
        print("  (keine Events oder Abruf fehlgeschlagen)")
        return

    counts: dict[str, int] = {
        "erstellt": 0, "aktualisiert": 0, "unverändert": 0,
        "vergangen": 0, "Duplikat": 0, "gelöscht": 0, "Fehler": 0,
    }

    for event in events:
        if event.get("_cancelled") and feed.delete_cancelled:
            status = delete_cancelled_event(event, client)
        else:
            status = sync_event(event, client)

        icon    = _ICONS.get(status, "✗")
        warning = "" if event.get("_uid_is_real", True) else "  ⚠ kein UID im Feed"
        print(f"  {icon} {event['title']} [{status}]{warning}")

        if status == "erstellt (Duplikat)":
            counts["Duplikat"] += 1
        elif status in counts:
            counts[status] += 1
        else:
            counts["Fehler"] += 1

    parts = [
        f"{counts['erstellt']} erstellt",
        f"{counts['aktualisiert']} aktualisiert",
        f"{counts['unverändert']} unverändert",
    ]
    if counts["gelöscht"]:
        parts.append(f"{counts['gelöscht']} gelöscht")
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
        sync_feed(feed, client, global_disclaimer=cfg.disclaimer, global_text=cfg.text)

    print("\nFertig.")
