# Configuration

Place a `config.yml` at `/opt/cal2gancio/config.yml`.

## Full example

```yaml
gancio:
  url: https://your-gancio-instance.org
  version: 1                                    # 1 = Gancio ≤1.x  |  2 = Gancio ≥2.x (default)
  username: admin@example.org                   # omit for anonymous posting
  password_file: /run/secrets/gancio_password   # default path, ignored without username
  wait: 2.0                                     # seconds between writes (default: 0)

text:
  event_link: "Zur Veranstaltung"               # link label for iCal URL field
  cancelled: "Abgesagt: "                       # title prefix for cancelled events

disclaimer: >-
  <em>Automatisch importiert via
  <a href="https://github.com/Leaced/cal2gancio">cal2gancio</a>.</em>

sources:
  - url: https://example.org/events/?ical=1
    default_place_name: Kreativfabrik Wiesbaden
    default_place_address: Murnaustraße 1, 65189 Wiesbaden
    additional_tags:
      - kreativfabrik
      - wiesbaden
    disclaimer: >-
      <em>Quelle: <a href="https://example.org">Veranstalter XY</a></em><br>
      Automatisch importiert via cal2gancio.
    ignore_past_events: true
    delete_cancelled: false
    filter:
      include:
        - Konzert
        - Festival
      exclude:
        - Probe

  - url: https://other-location.org/cal.ics
```

## `gancio:` section

| Key             | Required | Description                                                                      |
| --------------- | -------- | -------------------------------------------------------------------------------- |
| `url`           | ✓        | Base URL of the Gancio instance (redirects are followed automatically)           |
| `version`       | –        | API version: `1` (Gancio ≤ 1.x) or `2` (Gancio ≥ 2.x, **default**)            |
| `username`      | –        | Login e-mail; omit for anonymous posting (if the instance allows it)             |
| `password_file` | –        | Path to a file containing the password (default: `/run/secrets/gancio_password`) |
| `wait`          | –        | Seconds to wait between write requests; use when hitting HTTP 429 (default: `0`) |

## `text:` section

Language-specific strings used in event descriptions and titles. All keys are optional.

| Key          | Description                                               | Default          |
| ------------ | --------------------------------------------------------- | ---------------- |
| `event_link` | Link label for the iCal `URL` field in the description    | `"Event details"`|
| `cancelled`  | Prefix added to the title of `STATUS:CANCELLED` events    | `"Cancelled: "`  |

## Top-level keys

| Key          | Required | Description                                                                   |
| ------------ | -------- | ----------------------------------------------------------------------------- |
| `sources`    | ✓        | List of source feeds (see below)                                              |
| `disclaimer` | –        | HTML fallback disclaimer appended to every event without a per-feed override  |
| `text`       | –        | Language-specific strings (see `text:` section above)                         |

## Per-feed options (`sources` entries)

| Key                     | Required | Description                                                                               |
| ----------------------- | -------- | ----------------------------------------------------------------------------------------- |
| `url`                   | ✓        | Source URL (feed URL or listing page)                                                     |
| `source_type`           | –        | `ical` (default) or `html` — see [source documentation](sources/)                        |
| `default_place_name`    | –        | Fallback venue name when the source provides none                                         |
| `default_place_address` | –        | Fallback venue address when the source provides none                                      |
| `additional_tags`       | –        | Tags added to every event from this feed                                                  |
| `disclaimer`            | –        | HTML appended to every event from this feed; overrides the global `disclaimer`            |
| `event_link_text`       | –        | Link label for the event URL in the description; overrides `text.event_link`              |
| `ignore_past_events`    | –        | Skip events whose start time is in the past (default: `true`)                             |
| `delete_cancelled`      | –        | `true`: delete cancelled events from Gancio; `false`: prefix title (default: `false`)    |
| `filter.include`        | –        | Whitelist: only import events whose title contains one of these strings (case-insensitive)|
| `filter.exclude`        | –        | Blacklist: skip events whose title contains one of these strings (case-insensitive)       |
| `html`                  | –        | HTML source options — see [docs/sources/html.md](sources/html.md)                        |

### Title filter

`include` is applied before `exclude`. Both perform a case-insensitive substring match on the event title. If `include` is empty all events pass through; `exclude` is then applied on that result.

```yaml
filter:
  include:
    - Konzert
    - Festival
  exclude:
    - Probe
    - Meetup
```

### Disclaimer formatting

The `disclaimer` field accepts HTML. Use `<br>` for line breaks (`\n` is collapsed by Gancio's HTML renderer). YAML `>-` lets you wrap long lines while keeping `<br>` as the sole line-break mechanism:

```yaml
disclaimer: >-
  <em>Quelle: <a href="https://example.org">Veranstalter XY</a></em><br>
  Keine Gewähr für Vollständigkeit.
```

When a `URL` field is present in the iCal event, the description is assembled as:

```
Event description

——————————————————————————————

<a href="https://…">Zur Veranstaltung</a>

disclaimer
```
