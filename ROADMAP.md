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

## cal2gancio v2.0

### Remove deprecated flat `html:` config form

The flat `html:` structure (all options at the same level) was replaced in v1.x
by the `html.listing_page` / `html.detail_page` split. v2.0 removes the flat
form entirely. A deprecation warning is printed at startup when the flat form is
detected.

Migration: see the [HTML source documentation](docs/sources/html.md).
