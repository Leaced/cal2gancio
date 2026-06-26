# cal2gancio

Synchronizes one or more iCal feeds to a [Gancio](https://gancio.org) instance.

## Features

- Transfers all event data: title, description, location, coordinates, tags, images, recurrence
- Stateless: events are tracked via internal tags stored directly in Gancio (`_ical_…` / `_icalv_…`) — no local state file needed
- Per-feed defaults for location and tags (useful for feeds without `LOCATION` field)
- Detects unchanged events and skips them; updates events when content changes
- Multi-arch OCI container image (amd64 + arm64)

## Requirements

- A running Gancio instance with API access
- podman (or any OCI runtime / Kubernetes)

## Configuration

Place a `config.yml` at `/opt/cal2gancio/config.yml`:

```yaml
gancio:
  url: https://your-gancio-instance.org
  username: admin@example.org             # omit for anonymous posting
  password_file: /run/secrets/gancio_password  # default, ignored without username
  wait: 2.0                               # seconds between writes (default: 0)

disclaimer: "<em>Importiert via cal2gancio.</em>"  # optional, global fallback

sources:
  - url: https://example.org/events/?ical=1
    default_place_name: Kreativfabrik Wiesbaden
    default_place_address: Murnaustraße 1, 65189 Wiesbaden
    additional_tags:
      - kreativfabrik
      - wiesbaden
    disclaimer: "<em>Quelle: <a href=\"https://example.org\">Veranstalter XY</a></em>"  # overrides global

  - url: https://other-location.org/cal.ics
    # No defaults needed if the feed contains LOCATION fields
```

### `gancio:` section

| Key             | Required | Description                                                                      |
| --------------- | -------- | -------------------------------------------------------------------------------- |
| `url`           | ✓        | Base URL of the Gancio instance (redirects are followed automatically)           |
| `version`       | –        | Gancio API version: `1` (≤ 1.x) or `2` (≥ 2.x, default)                        |
| `username`      | –        | Login e-mail; omit for anonymous posting (if the instance allows it)             |
| `password_file` | –        | Path to a file containing the password (default: `/run/secrets/gancio_password`) |
| `wait`          | –        | Seconds to wait between write requests; use when hitting HTTP 429 (default: `0`) |

### `text:` section

Language-specific strings. All keys are optional.

| Key         | Description                                                          | Default          |
| ----------- | -------------------------------------------------------------------- | ---------------- |
| `event_link`| Link text for the iCal `URL` field                                   | `"Event details"`|
| `cancelled` | Prefix added to the title of `STATUS:CANCELLED` events               | `"Cancelled: "`  |

```yaml
text:
  event_link: "Zur Veranstaltung"
  cancelled: "Abgesagt: "
```

### Top-level keys

| Key          | Required | Description                                                                   |
| ------------ | -------- | ----------------------------------------------------------------------------- |
| `sources`    | ✓        | List of feeds (see below)                                                     |
| `disclaimer` | –        | HTML fallback disclaimer; appended to every event without a per-feed override |
| `text`       | –        | Language-specific strings (see `text:` section above)                         |

Per feed (`sources` entries):

| Key                     | Required | Description                                                                          |
| ----------------------- | -------- | ------------------------------------------------------------------------------------ |
| `url`                   | ✓        | iCal feed URL                                                                        |
| `default_place_name`    | –        | Used when the feed has no `LOCATION` field                                           |
| `default_place_address` | –        | Used when the feed has no `LOCATION` field                                           |
| `additional_tags`       | –        | Tags added to every event from this feed                                             |
| `disclaimer`            | –        | HTML appended to every event from this feed; overrides global                        |
| `event_link_text`       | –        | Link text for the `URL` field of this feed; overrides `text.event_link`              |
| `ignore_past_events`    | –        | Skip events whose start time is in the past (default: `true`)                        |
| `delete_cancelled`      | –        | Delete `STATUS:CANCELLED` events from Gancio; if `false`, prefix title (default: `false`) |

The `disclaimer` field accepts HTML. Use `<br>` for line breaks. YAML `>-` is recommended so `<br>` stays in the string while source lines can wrap:

```yaml
disclaimer: >-
  <em>Quelle: <a href="https://example.org">Veranstalter XY</a></em><br>
  Keine Gewähr für Vollständigkeit.
```

If the iCal feed contains a `URL` field, it is included in the description as a clickable link:

```
Event description

——————————————————————————————

<a href="https://…">Event details</a>

disclaimer
```

If the disclaimer changes, all affected events are updated on the next run (it is part of the content hash).

## Container

Images are published to the GitHub Container Registry:

```bash
podman pull ghcr.io/leaced/cal2gancio:latest
```

### Password setup

The password is read from a file whose path you specify in `password_file`. The recommended approach is a **podman secret**:

```bash
echo -n "your-gancio-password" | podman secret create gancio_password -
```

This stores the secret in podman's secret store and mounts it at `/run/secrets/gancio_password` inside the container.

Alternatively, put the password in a plain file on the host (e.g. `/etc/cal2gancio/password`) and mount it directly:

```bash
# config.yml: password_file: /run/secrets/gancio_password
echo "your-gancio-password" > /etc/cal2gancio/password
chmod 600 /etc/cal2gancio/password
```

### Quick run

With a podman secret:

```bash
podman run --rm \
  -v /opt/cal2gancio:/opt/cal2gancio:ro,Z \
  --secret gancio_password \
  ghcr.io/leaced/cal2gancio:latest
```

With a password file mounted directly:

```bash
podman run --rm \
  -v /opt/cal2gancio:/opt/cal2gancio:ro,Z \
  -v /etc/cal2gancio/password:/run/secrets/gancio_password:ro,Z \
  ghcr.io/leaced/cal2gancio:latest
```

### Running on a schedule (systemd + Quadlet)

[Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html) lets systemd manage the container declaratively — no `podman run` buried in `ExecStart`.

```ini
# /etc/containers/systemd/cal2gancio.container
[Unit]
Description=cal2gancio iCal → Gancio sync

[Container]
Image=ghcr.io/leaced/cal2gancio:latest
Volume=/opt/cal2gancio:/opt/cal2gancio:ro,Z
Secret=gancio_password

[Service]
Type=oneshot
```

```ini
# /etc/systemd/system/cal2gancio.timer
[Unit]
Description=cal2gancio sync timer

[Timer]
OnCalendar=*:0/30
Persistent=true
Unit=cal2gancio.service

[Install]
WantedBy=timers.target
```

```bash
systemctl daemon-reload        # triggers the Quadlet generator
systemctl enable --now cal2gancio.timer
```

## How stateless sync works

Every event uploaded to Gancio receives two internal tags:

| Tag             | Purpose                                                   |
| --------------- | --------------------------------------------------------- |
| `_ical_{hash}`  | Stable identity key derived from the iCal `UID`           |
| `_icalv_{hash}` | Content fingerprint; changes when any event field changes |

On each run, for every iCal event:

1. Search Gancio for an event with the matching `_ical_` tag
2. **Not found** → create (POST)
3. **Found, `_icalv_` matches** → skip (nothing changed)
4. **Found, `_icalv_` differs** → update (PUT); the new content tag replaces the old one automatically

This means the tool works correctly across multiple machines and survives restarts without any local state.

### Anonymous mode limitation

When running without `username`, events are submitted anonymously and placed in Gancio's **pending/unconfirmed** queue. Pending events are not returned by the public events API, so a freshly submitted anonymous event is invisible on the next run.

Once an admin approves (publishes) an event, it becomes visible and the stateless lookup works again:

| Lookup result                                | Action                                    |
| -------------------------------------------- | ----------------------------------------- |
| Not found (still pending or never created)   | create — `✓ erstellt`                     |
| Found, content unchanged (`_icalv_` matches) | skip — `= unverändert`                    |
| Found, content changed (`_icalv_` differs)   | create new version — `⚠ erstellt (Duplikat)` |

The third case creates a duplicate because `PUT /api/event` always requires authentication. The summary line flags this with `⚠ Duplikat(e)`.

**Use credentials (`username` + `password_file`) for full create / update / skip support.**

> **Note:** Events without a `UID` field in the iCal feed use `title + start_timestamp` as a fallback identity key. If their title or date changes, they will be duplicated rather than updated. Well-maintained feeds always export proper UIDs.

## Supported iCal fields

| iCal                  | Gancio                                           |
| --------------------- | ------------------------------------------------ |
| `SUMMARY`             | `title`                                          |
| `DESCRIPTION`         | `description`                                    |
| `DTSTART`             | `start_datetime`                                 |
| `DTEND` > 24 h        | `multidate`                                      |
| `LOCATION`            | `place_name` + `place_address`                   |
| `GEO`                 | `place_latitude` / `place_longitude`             |
| `CATEGORIES`          | `tags`                                           |
| `ATTACH` (image URL)  | `image_url`                                      |
| `URL`                 | link in description (text via `event_link_text`) |
| `DURATION`            | used for `multidate` when `DTEND` is absent      |
| `EXDATE`              | excluded recurrence dates (tracked in content hash; Gancio receives no native EXDATE) |
| `RRULE` weekly        | `recurrent[frequency]` `1w` / `2w`               |
| `RRULE` monthly       | `recurrent[frequency]` `1m` / `2m` (no `BYDAY`)  |
| `RRULE` yearly        | `recurrent[frequency]` `1y`                      |

## Project structure

```
cal2gancio/
├── __main__.py          Entry point
├── config.py            YAML config loading, dataclasses
├── ical/
│   ├── fetch.py         HTTP fetch + iCal parsing
│   ├── event.py         VEVENT → Gancio event dict
│   ├── timestamps.py    DTSTART/DTEND → Unix timestamp
│   ├── location.py      LOCATION + GEO parsing
│   ├── media.py         ATTACH → image URL
│   ├── recurrence.py    RRULE → Gancio recurrence format
│   └── tags.py          Categories, additional tags, internal sync tags
├── gancio/
│   ├── auth.py          OAuth login
│   ├── client.py        GancioClient (find / create / update)
│   └── encoding.py      multipart/form-data encoding
└── sync/
    ├── decision.py      Per-event create / update / skip logic
    └── feed.py          Feed iteration, summary output
```
