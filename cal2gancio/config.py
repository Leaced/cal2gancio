"""
config.py – Load and validate /opt/cal2gancio/config.yml.

Config file structure:
    gancio_url: https://demo.gancio.org
    username: admin@example.org
    password_file: /run/secrets/gancio_password
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
    disclaimer: str
    feeds: list[FeedConfig]


def load() -> AppConfig:
    if not CONFIG_PATH.exists():
        print(f"Error: config not found at {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    with CONFIG_PATH.open() as f:
        raw = yaml.safe_load(f)

    required = ["gancio_url", "username", "ical_urls"]
    missing = [k for k in required if not raw.get(k)]
    if missing:
        print(f"Error: missing config keys: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    try:
        password = Path(raw.get("password_file", "/run/secrets/gancio_password")).read_text().strip()
    except OSError as e:
        print(f"Error reading password file: {e}", file=sys.stderr)
        sys.exit(1)

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
        gancio_url=raw["gancio_url"].rstrip("/"),
        username=raw["username"],
        password=password,
        disclaimer=raw.get("disclaimer", ""),
        feeds=feeds,
    )
