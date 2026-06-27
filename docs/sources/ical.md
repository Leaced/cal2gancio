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
