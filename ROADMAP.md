# Roadmap

## Requires Gancio: hidden tags or custom metadata (framagit.org/les/gancio/-/work_items/716)

### Replace visible internal tags with hidden metadata and detect source deletions

The `_ical_*` (identity) and `_icalv_*` (content hash) tracking tags are
currently stored as regular Gancio tags, where they are visible to all users.
Once Gancio supports hidden tags or a custom metadata API, these should be
migrated to that mechanism and removed from the public tag list.

A third hidden tag — `_icalf_{feed_hash}` — would also enable deletion
detection: after each sync, cal2gancio queries Gancio for all future events
carrying that feed tag, compares them against the UIDs seen in the current
run, and deletes any that have disappeared from the source. This keeps
Gancio in sync without a local state file.

## Requires Gancio 2.0

### Native cancelled-event support

Gancio 2.0 adds a first-class cancelled status on events
(framagit.org/les/gancio/-/work_items/625). Once available, cal2gancio
should use this API field instead of prefixing the title (the current
`text.cancelled` / `delete_cancelled` approach).

## New source type: `page_json`

### Generic JSON extraction from pages or API endpoints

Some sites embed structured event data as a JavaScript variable in their main
page (e.g. `window.calendarEvents = [...]`) or expose a plain JSON array via
a dedicated endpoint. Neither the `ical` nor the `html` source fits this
pattern.

`source_type: page_json` would fetch a URL, optionally extract a named
variable from an inline `<script>` block, and map arbitrary JSON keys to
Gancio fields via a configurable `fields:` definition. A `time_field` option
could combine separate date and time keys into a single `start_datetime`.

Example config sketch:

```yaml
sources:
  - url: https://example.org/
    source_type: page_json
    page_json:
      extract: window.calendarEvents   # JS variable to extract; omit for bare JSON responses
      fields:
        title:       title_de
        start_date:  date              # YYYY-MM-DD
        start_time:  time              # HH:MM or HH:MM-HH:MM (start extracted via time_regex)
        description: description_de_html
        place_name:  room_label
        tags:        tags
        image_url:   "images[0]"       # basic index access into arrays
```

## cal2gancio v2.0

### Remove deprecated flat `html:` config form

The flat `html:` structure (all options at the same level) was replaced in v1.x
by the `html.listing_page` / `html.detail_page` split. v2.0 removes the flat
form entirely. A deprecation warning is printed at startup when the flat form is
detected.

Migration: see the [HTML source documentation](docs/sources/html.md).
