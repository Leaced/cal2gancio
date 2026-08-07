# cal2gancio

Synchronizes events from iCal feeds and HTML event pages to a [Gancio](https://gancio.org) instance.

## Features

- Sources: iCal/ICS feeds and HTML event listing pages
- Transfers all event data: title, description, location, coordinates, tags, images, recurrence
- Stateless sync — no local state file; events are tracked via internal Gancio tags (`_ical_…` / `_icalv_…`)
- Detects unchanged events and skips them; updates events when content changes
- Per-feed title filters (include / exclude) and past-event filtering
- Cancelled event handling: delete from Gancio or prefix title

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
| [How it works](docs/how-it-works.md) | Program flow diagram, stateless sync, anonymous mode |
| [iCal source](docs/sources/ical.md) | Supported iCal fields and notes |
| [HTML source](docs/sources/html.md) | CSS selector config, field mapping, example |
| [Adding a source type](docs/adding-a-source.md) | How to implement and register a new source type |

## Image verification

All release images are signed with [Cosign](https://docs.sigstore.dev/cosign/overview/) in keyless mode via GitHub Actions.
The signing identity is the CI workflow that built the image (`_build-scan.yml`), not the release workflow —
because `skopeo copy` re-tags the manifest without rebuilding it, so the original signature remains authoritative.

```bash
cosign verify \
  --certificate-identity-regexp \
    "https://github.com/Leaced/cal2gancio/.github/workflows/_build-scan.yml@refs/pull/[0-9]+/merge" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/leaced/cal2gancio:latest
```

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
│   ├── __init__.py      Source dispatcher + post-processing
│   ├── ical/            iCal source
│   │   ├── fetch.py     HTTP fetch + iCal parsing
│   │   ├── event.py     VEVENT → Gancio event dict
│   │   ├── timestamps.py DTSTART/DTEND/DURATION → Unix timestamp
│   │   ├── location.py  LOCATION + GEO parsing
│   │   ├── media.py     ATTACH → image URL
│   │   ├── recurrence.py RRULE → Gancio recurrence format
│   │   └── tags.py      Categories, additional tags, internal sync tags
│   └── html/            HTML scraper source
│       ├── fetch.py     Orchestrates discover + extract + enrich
│       ├── discover.py  Listing page → event URLs
│       ├── extract.py   CSS selector field extraction
│       └── ical_fallback.py  Optional per-event iCal fetch
└── sync/
    ├── decision.py      Per-event create / update / skip / delete logic
    └── feed.py          Feed iteration, summary output
```
