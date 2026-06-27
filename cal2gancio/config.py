"""
config.py – Load and validate /opt/cal2gancio/config.yml.

Config file structure:
    gancio:
      url: https://demo.gancio.org
      version: 1                          # 1 = Gancio ≤1.x, 2 = Gancio ≥2.x (default)
      username: admin@example.org         # optional, omit for anonymous posting
      password_file: /run/secrets/gancio_password
      wait: 2.0

    text:
      event_link: "Event details"         # link text for iCal URL field
      cancelled: "Cancelled: "            # prefix for STATUS:CANCELLED events

    disclaimer: "<em>Importiert via cal2gancio.</em>"

    sources:
      - url: https://example.org/events/?ical=1
        default_place_name: Kreativfabrik Wiesbaden
        default_place_address: Murnaustraße 1, 65189 Wiesbaden
        additional_tags:
          - kreativfabrik
        disclaimer: "<em>Quelle: Kreativfabrik</em>"
        delete_cancelled: false
      - url: https://other.org/feed.ics
"""

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml


class SourceType(Enum):
    ICAL = "ical"
    HTML = "html"

CONFIG_PATH = Path("/opt/cal2gancio/config.yml")


@dataclass
class FieldSelector:
    selector: str
    attribute: str = ""     # extract this HTML attribute; empty → text content
    as_html: bool = False   # True → extract innerHTML instead of text
    format: str = ""        # strptime format string for datetime fields


@dataclass
class StatusSelector:
    selector: str
    tag: str = ""           # Gancio tag added when selector matches
    title_prefix: str = ""  # prepended to event title when selector matches


@dataclass
class HtmlConfig:
    event_link_selector: str = ""
    event_id_attribute: str = ""   # HTML attribute on the link element to use as {event_id} in ical_url_pattern
    ical_url_pattern: str = ""     # optional; placeholders: {base}, {slug}, {event_id}
    cancelled_selector: str = ""
    status_selectors: list[StatusSelector] = field(default_factory=list)
    fields: dict[str, FieldSelector] = field(default_factory=dict)


@dataclass
class TextConfig:
    event_link: str = "Event details"
    cancelled: str = "Cancelled: "


@dataclass
class FilterConfig:
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


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
    delete_cancelled: bool = False
    filter: FilterConfig = field(default_factory=FilterConfig)
    html: HtmlConfig = field(default_factory=HtmlConfig)


@dataclass
class AppConfig:
    gancio_url: str
    gancio_version: int
    username: str
    password: str
    request_delay: float
    disclaimer: str
    text: TextConfig
    feeds: list[FeedConfig]


def _parse_field_selectors(raw: dict) -> dict[str, FieldSelector]:
    result: dict[str, FieldSelector] = {}
    for name, cfg in (raw or {}).items():
        if isinstance(cfg, str):
            result[name] = FieldSelector(selector=cfg)
        else:
            result[name] = FieldSelector(
                selector=cfg.get("selector", ""),
                attribute=cfg.get("attribute", ""),
                as_html=bool(cfg.get("as_html", False)),
                format=cfg.get("format", ""),
            )
    return result


def _parse_html_config(raw: dict) -> HtmlConfig:
    status_selectors = [
        StatusSelector(
            selector=item["selector"],
            tag=item.get("tag", ""),
            title_prefix=item.get("title_prefix", ""),
        )
        for item in (raw.get("status_selectors") or [])
    ]
    return HtmlConfig(
        event_link_selector=raw.get("event_link_selector", ""),
        event_id_attribute=raw.get("event_id_attribute", ""),
        ical_url_pattern=raw.get("ical_url_pattern", ""),
        cancelled_selector=raw.get("cancelled_selector", ""),
        status_selectors=status_selectors,
        fields=_parse_field_selectors(raw.get("fields") or {}),
    )


def _parse_filter(raw: dict) -> FilterConfig:
    return FilterConfig(
        include=[str(s) for s in raw.get("include") or []],
        exclude=[str(s) for s in raw.get("exclude") or []],
    )


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
    request_delay  = float(gancio.get("wait", 0.0))

    text_raw = raw.get("text") or {}
    text = TextConfig(
        event_link=text_raw.get("event_link", "Event details"),
        cancelled=text_raw.get("cancelled", "Cancelled: "),
    )

    feeds = [
        FeedConfig(
            url=entry["url"],
            source_type=SourceType(entry.get("source_type", "ical").lower()),
            default_place_name=entry.get("default_place_name", ""),
            default_place_address=entry.get("default_place_address", ""),
            additional_tags=entry.get("additional_tags") or [],
            disclaimer=entry.get("disclaimer", ""),
            event_link_text=entry.get("event_link_text", ""),
            ignore_past_events=bool(entry.get("ignore_past_events", True)),
            delete_cancelled=bool(entry.get("delete_cancelled", False)),
            filter=_parse_filter(entry.get("filter") or {}),
            html=_parse_html_config(entry.get("html") or {}),
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
        text=text,
        feeds=feeds,
    )
