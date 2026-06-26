"""
config.py – Load and validate /opt/cal2gancio/config.yml.

Config file structure:
    gancio:
      url: https://demo.gancio.org
      username: admin@example.org       # optional, omit for anonymous posting
      password_file: /run/secrets/gancio_password  # optional
      wait: 2.0                         # seconds between writes, default 0

    disclaimer: "<em>Importiert via cal2gancio.</em>"  # optional, global fallback

    sources:
      - url: https://example.org/events/?ical=1
        default_place_name: Kreativfabrik Wiesbaden
        default_place_address: Murnaustraße 1, 65189 Wiesbaden
        additional_tags:
          - kreativfabrik
        disclaimer: "<em>Quelle: Kreativfabrik</em>"  # optional, overrides global
      - url: https://other.org/feed.ics
"""

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml


class SourceType(Enum):
    ICAL = "ical"

CONFIG_PATH = Path("/opt/cal2gancio/config.yml")


@dataclass
class FeedConfig:
    url: str
    source_type: SourceType = SourceType.ICAL
    default_place_name: str = ""
    default_place_address: str = ""
    additional_tags: list[str] = field(default_factory=list)
    disclaimer: str = ""
    event_link_text: str = ""
    ignore_past_events: bool = True


@dataclass
class AppConfig:
    gancio_url: str
    gancio_version: int
    username: str
    password: str
    request_delay: float
    disclaimer: str
    event_link_text: str
    feeds: list[FeedConfig]


def load() -> AppConfig:
    if not CONFIG_PATH.exists():
        print(f"Error: config not found at {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    with CONFIG_PATH.open() as f:
        raw = yaml.safe_load(f)

    gancio = raw.get("gancio") or {}
    gancio_url = (gancio.get("url") or "").rstrip("/")
    if not gancio_url:
        print("Error: missing gancio.url", file=sys.stderr)
        sys.exit(1)

    if not raw.get("sources"):
        print("Error: missing sources", file=sys.stderr)
        sys.exit(1)

    username = gancio.get("username") or ""
    password = ""
    if username:
        try:
            password = Path(gancio.get("password_file", "/run/secrets/gancio_password")).read_text().strip()
        except OSError as e:
            print(f"Error reading password file: {e}", file=sys.stderr)
            sys.exit(1)

    gancio_version = int(gancio.get("version", 2))
    request_delay = float(gancio.get("wait", 0.0))

    feeds = [
        FeedConfig(
            url=entry["url"],
            default_place_name=entry.get("default_place_name", ""),
            default_place_address=entry.get("default_place_address", ""),
            additional_tags=entry.get("additional_tags") or [],
            disclaimer=entry.get("disclaimer", ""),
            event_link_text=entry.get("event_link_text", ""),
            ignore_past_events=bool(entry.get("ignore_past_events", True)),
        )
        for entry in raw["sources"]
        if entry.get("url")
    ]

    return AppConfig(
        gancio_url=gancio_url,
        gancio_version=gancio_version,
        username=username,
        password=password,
        request_delay=request_delay,
        disclaimer=raw.get("disclaimer", ""),
        event_link_text=raw.get("event_link_text", "Event details"),
        feeds=feeds,
    )
