# cal2gancio

Synchronizes one or more iCal feeds to a [Gancio](https://gancio.org) instance.

## Features

- Transfers all event data: title, description, location, coordinates, tags, images, recurrence
- Stateless sync — no local state file; events are tracked via internal Gancio tags (`_ical_…` / `_icalv_…`)
- Detects unchanged events and skips them; updates events when content changes
- Per-feed title filters (include / exclude) and past-event filtering
- `STATUS:CANCELLED` handling: delete from Gancio or prefix title
- Multi-arch OCI container image (amd64 + arm64)

## Requirements

- A running Gancio instance with API access
- podman (or any OCI runtime / Kubernetes)

## Quick start

```bash
podman pull ghcr.io/leaced/cal2gancio:latest

echo -n "your-gancio-password" | podman secret create gancio_password -

podman run --rm \
  -v /opt/cal2gancio:/opt/cal2gancio:ro,Z \
  --secret gancio_password \
  ghcr.io/leaced/cal2gancio:latest
```

Minimal `config.yml` at `/opt/cal2gancio/config.yml`:

```yaml
gancio:
  url: https://your-gancio-instance.org
  username: admin@example.org
  # password_file: /run/secrets/gancio_password  ← default

sources:
  - url: https://example.org/events/?ical=1
```

## Documentation

| Document | Contents |
| -------- | -------- |
| [Configuration](docs/configuration.md) | All config keys, filters, disclaimer formatting |
| [Deployment](docs/deployment.md) | Container, password setup, systemd + Quadlet timer |
| [How it works](docs/how-it-works.md) | Program flow diagram, stateless sync, anonymous mode, supported iCal fields |
| [Adding a source type](docs/adding-a-source.md) | How to implement and register a new source (RSS, etc.) |

## Project structure

```
cal2gancio/
├── __main__.py          Entry point
├── config.py            YAML config loading, dataclasses
├── gancio/
│   ├── auth.py          Login (v1 / v2)
│   ├── client.py        GancioClient (find / create / update / delete)
│   └── encoding.py      multipart/form-data encoding
├── sources/
│   ├── __init__.py      Source dispatcher + title filter
│   └── ical/            iCal source implementation
│       ├── fetch.py     HTTP fetch + iCal parsing
│       ├── event.py     VEVENT → Gancio event dict
│       ├── timestamps.py DTSTART/DTEND/DURATION → Unix timestamp
│       ├── location.py  LOCATION + GEO parsing
│       ├── media.py     ATTACH → image URL
│       ├── recurrence.py RRULE → Gancio recurrence format
│       └── tags.py      Categories, additional tags, internal sync tags
└── sync/
    ├── decision.py      Per-event create / update / skip / delete logic
    └── feed.py          Feed iteration, summary output
```
