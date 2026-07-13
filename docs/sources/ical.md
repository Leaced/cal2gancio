# iCal source (`source_type: ical`)

Fetches a standard iCal/ICS feed URL and converts each `VEVENT` into a Gancio event.

## Minimal config

```yaml
sources:
  - url: https://example.org/events/?ical=1
```

## Supported iCal fields

| iCal field           | Gancio field / behaviour                                    |
| -------------------- | ----------------------------------------------------------- |
| `SUMMARY`            | `title`                                                     |
| `DESCRIPTION`        | `description`                                               |
| `DTSTART`            | `start_datetime`                                            |
| `DTEND` > 24 h       | `multidate`                                                 |
| `DURATION`           | used for `multidate` when `DTEND` is absent                 |
| `LOCATION`           | `place_name` + `place_address`                              |
| `GEO`                | `place_latitude` / `place_longitude`                        |
| `CATEGORIES`         | `tags`                                                      |
| `ATTACH` (image URL) | `image_url`                                                 |
| `URL`                | clickable link in description (label via `text.event_link`) |
| `EXDATE`             | excluded recurrence dates (tracked in content hash)         |
| `STATUS:CANCELLED`   | title-prefix or delete, depending on `delete_cancelled`     |
| `RRULE` weekly       | `recurrent[frequency]` → `1w` / `2w`                       |
| `RRULE` monthly      | `recurrent[frequency]` → `1m` / `2m` (no `BYDAY`)          |
| `RRULE` yearly       | `recurrent[frequency]` → `1y`                               |

## Notes

- `RECURRENCE-ID` components (modified single occurrences of a recurring series) are skipped. Full `STATUS:CANCELLED` + `RECURRENCE-ID` support is planned.
- Events without a `UID` field use `title + start_timestamp` as a fallback identity key. If title or date changes, the event will be duplicated rather than updated. Well-maintained feeds always export proper UIDs.

## Comparison with the Gancio Feed Plugin

Gancio ships a built-in [Feed Plugin](https://framagit.org/les/gancio/-/blob/main/plugins/feed/index.ts) that can also import ICS feeds. The table below shows where cal2gancio differs.

| Feature | cal2gancio (ical source) | Gancio Feed Plugin |
| ------- | ------------------------ | ------------------ |
| **Event updates** | Detects content changes via a hash stored in a tag; creates, updates, or skips each event accordingly | Deduplicates by title + start datetime at import time; never updates an already-imported event |
| **iCal UID** | Uses the iCal `UID` field as a stable identity key; a `UID` change means a new event, a date/title change does not | No UID tracking; identity is title + datetime |
| **Image import** | Imports `ATTACH` image URLs and sends them to Gancio | Not supported |
| **`STATUS:CANCELLED`** | Marks cancelled events with a title prefix or removes them, depending on `delete_cancelled` | Not supported |
| **Link to source** | Appends a clickable link to the original event page (from iCal `URL`) in the description | Not supported |
| **Venue** | Parses `LOCATION` into `place_name` + `place_address`; falls back to `default_place_name` / `default_place_address` from config | Not supported |
