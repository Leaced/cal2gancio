"""
config.py – Load and validate /opt/cal2gancio/config.yml.

Config file structure:
    gancio:
      url: https://demo.gancio.org
      username: admin@example.org       # optional, omit for anonymous posting
      password_file: /run/secrets/gancio_password  # optional
      wait: 2.0                         # seconds between writes, default 0

    disclaimer: "Imported via [cal2gancio](https://github.com/leaced/cal2gancio)."  # optional

    ical_urls:
      - url: https://example.org/events/?ical=1
        default_place_name: Kreativfabrik Wiesbaden
        default_place_address: Murnaustraße 1, 65189 Wiesbaden
        additional_tags:
          - kreativfabrik
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


@dataclass
class AppConfig:
    gancio_url: str
    username: str
    password: str
    request_delay: float
    disclaimer: str
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

    if not raw.get("ical_urls"):
        print("Error: missing ical_urls", file=sys.stderr)
        sys.exit(1)

    username = gancio.get("username") or ""
    password = ""
    if username:
        try:
            password = Path(gancio.get("password_file", "/run/secrets/gancio_password")).read_text().strip()
        except OSError as e:
            print(f"Error reading password file: {e}", file=sys.stderr)
            sys.exit(1)

    request_delay = float(gancio.get("wait", 0.0))

    feeds = [
        FeedConfig(
            url=entry["url"],
            default_place_name=entry.get("default_place_name", ""),
            default_place_address=entry.get("default_place_address", ""),
            additional_tags=entry.get("additional_tags") or [],
        )
        for entry in raw["ical_urls"]
        if entry.get("url")
    ]

    return AppConfig(
        gancio_url=gancio_url,
        username=username,
        password=password,
        request_delay=request_delay,
        disclaimer=raw.get("disclaimer", ""),
        feeds=feeds,
    )
