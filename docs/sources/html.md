# HTML source (`source_type: html`)

Scrapes an event listing page to discover individual event URLs, then builds each
event from an optional per-event iCal file and/or HTML CSS selectors.

When both iCal and HTML selectors provide a value for the same field, the
**explicit HTML selector wins**.

## How it works

1. Fetch the listing page (`url`) and find all event links via `event_link_selector`
2. For each event URL: optionally fetch a per-event iCal file (`ical_url_pattern`)
3. Fetch the event detail page and apply `fields` selectors (override iCal values)
4. Apply `cancelled_selector` and `tag_selectors` for status and extra tags

## Config reference

```yaml
sources:
  - source_type: html
    url: https://example.org/events/
    html:
      # Required: CSS selector that matches <a> links to individual event pages
      event_link_selector: "a[href*='/events/']"

      # Optional: HTML attribute on the link element to use as {event_id}
      # in ical_url_pattern (e.g. "data-event-id")
      event_id_attribute: "data-event-id"

      # Optional: URL pattern for per-event iCal files
      # {base} = feed url without trailing slash
      # {slug} = last URL path segment of the event page
      # {event_id} = value of event_id_attribute (falls back to {slug} if not set)
      ical_url_pattern: "{base}/?method=ical&id={event_id}"

      # Optional: CSS selector whose presence marks the event as cancelled
      # Sets _cancelled=True; post-processor applies prefix or delete per feed config
      cancelled_selector: "img[alt='Fällt aus']"

      # Optional: limit the number of events fetched (0 = unlimited)
      max_events: 50

      # Optional: apply tags and/or title prefixes when a CSS selector matches
      # Both "tag" and "title_prefix" are optional; use either or both.
      status_selectors:
        - selector: "img[alt='Ausverkauft']"
          tag: "ausverkauft"
          title_prefix: "Ausverkauft: "
        - selector: "img[alt='Verschoben']"
          tag: "verschoben"
          title_prefix: "Verschoben: "

      # Optional: override or supplement iCal field values with HTML selectors
      fields:
        title:
          selector: "h1.event-title"
        start_datetime:
          selector: ".event-date"
          format: "%d.%m.%Y %H:%M"   # Python strptime format
        end_datetime:
          selector: ".event-end"
          format: "%d.%m.%Y %H:%M"
        description:
          selector: ".event-description"
          as_html: true               # extract innerHTML instead of text
        image_url:
          selector: "img.event-hero"
          attribute: src              # extract HTML attribute instead of text
        place_name:
          selector: ".venue-name"
        place_address:
          selector: ".venue-address"
```

## `ical_url_pattern` placeholders

| Placeholder  | Value |
| ------------ | ----- |
| `{base}`     | Feed URL without trailing slash |
| `{slug}`     | Last path segment of the event page URL |
| `{event_id}` | Value of `event_id_attribute` on the listing link; falls back to `{slug}` if not configured |

## Field selector options

| Key         | Default | Description                                         |
| ----------- | ------- | --------------------------------------------------- |
| `selector`  | —       | CSS selector (required)                             |
| `attribute` | —       | Extract this HTML attribute; omit to use text content |
| `as_html`   | `false` | Extract `innerHTML` instead of plain text           |
| `format`    | —       | `strptime` format string for `start_datetime` / `end_datetime` |
| `regex`     | —       | Regex applied to the extracted value; returns capture group 1 if present, otherwise the full match. Useful for extracting URLs from CSS (`style` attribute) or partial strings. |
| `time_selector` | — | For `start_datetime` / `end_datetime` only: CSS selector for a separate time-of-day element. Its text is appended (space-separated) to the date text before `format` parsing. |

## Supported field names

| Field name       | Gancio field        |
| ---------------- | ------------------- |
| `title`          | `title`             |
| `start_datetime` | `start_datetime`    |
| `end_datetime`   | `end_datetime` / `multidate` |
| `description`    | `description`       |
| `image_url`      | `image_url`         |
| `place_name`     | `place_name`        |
| `place_address`  | `place_address`     |

## UID and identity

- If an iCal file is fetched, its `UID` is used as the stable identity key (`_ical_` tag).
- Without iCal, the event page URL is used as the identity key (`_uid_is_real: false`).

## Example: Schlachthof Wiesbaden

```yaml
sources:
  - source_type: html
    url: https://schlachthof-wiesbaden.de/
    additional_tags:
      - schlachthof
      - wiesbaden
    html:
      event_link_selector: "a[href*='/events/']"
      ical_url_pattern: "{base}/ics/{slug}.ics"
      cancelled_selector: "img[alt='Fällt aus']"
      status_selectors:
        - selector: "img[alt='Ausverkauft']"
          tag: "ausverkauft"
          title_prefix: "Ausverkauft: "
        - selector: "img[alt='Verschoben']"
          tag: "verschoben"
          title_prefix: "Verschoben: "
      fields:
        description:
          selector: ".event-description"
          as_html: true
        image_url:
          selector: "img.event-image"
          attribute: src
```
