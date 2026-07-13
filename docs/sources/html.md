# HTML source (`source_type: html`)

Scrapes an event listing page to discover individual event URLs, then builds each
event from an optional per-event iCal file and/or HTML CSS selectors on the detail page.

When both iCal and HTML selectors provide a value for the same field, the
**explicit HTML selector wins**.

## How it works

1. Fetch the **listing page** (`url`) and collect event links via `listing_page.event_link_selector`.
2. For each event URL, fetch the **detail page**.
3. Acquire iCal data via one of two options under `detail_page`:
   - `ical_link_selector` — find the iCal `<a>` on the detail page and fetch it, or
   - `ical_url_pattern` — construct the iCal URL from a template (no extra request).
4. Apply `detail_page.fields` selectors (override iCal values where both exist).
5. Apply `detail_page.status_selectors` for cancellation, extra tags, and title prefixes.

## Config reference

```yaml
sources:
  - source_type: html
    url: https://example.org/events/
    html:
      listing_page:
        event_link_selector: "a[href*='/events/']"  # required
        event_id_attribute: "data-event-id"          # optional
        max_events: 50                               # optional, 0 = unlimited
      detail_page:
        ical_url_pattern: "{base}/?method=ical&id={event_id}"  # see below
        ical_link_selector: "a[href*='/ical/']"                 # alternative to ical_url_pattern
        status_selectors:
          - selector: "img[alt='Fällt aus']"
            cancelled: true
          - selector: "img[alt='Ausverkauft']"
            tag: "ausverkauft"
            title_prefix: "Ausverkauft: "
        fields:
          title:
            selector: "h1.event-title"
          start_datetime:
            selector: ".event-date"
            format: "%d.%m.%Y %H:%M"
          end_datetime:
            selector: ".event-end"
            format: "%d.%m.%Y %H:%M"
          description:
            selector: ".event-description"
            as_html: true
          image_url:
            selector: "img.event-hero"
            attribute: src
          place_name:
            selector: ".venue-name"
          place_address:
            selector: ".venue-address"
```

### `listing_page` options

| Key | Default | Description |
| --- | ------- | ----------- |
| `event_link_selector` | — | **Required.** CSS selector matching `<a>` links to individual event pages. |
| `event_id_attribute` | — | HTML attribute on each link to use as `{event_id}` in `ical_url_pattern` (e.g. `"data-event-id"`). |
| `max_events` | `0` | Limit events processed. `0` = unlimited. Applied after collecting all links. |

### `detail_page` options

#### iCal acquisition (choose one)

Both options are optional. Omit both to rely entirely on `fields` selectors.
`ical_link_selector` takes priority if both are set.

| Key | Description |
| --- | ----------- |
| `ical_link_selector` | CSS selector for an `<a>` on the detail page whose `href` is the iCal URL. Use when the iCal URL contains a server-generated token (e.g. TYPO3 `cHash`) that cannot be derived from the event slug. |
| `ical_url_pattern` | URL template constructed without an extra request. Placeholders: `{base}` (feed URL without trailing slash), `{slug}` (last path segment of the event URL), `{event_id}` (value of `event_id_attribute`, falls back to `{slug}`). |

#### `status_selectors`

A list of CSS presence checks. Each matching element triggers one or more side effects.
All keys except `selector` are optional; use any combination.

| Key | Description |
| --- | ----------- |
| `selector` | CSS selector (required). Side effects apply only when this element is found. |
| `cancelled` | `true` → mark event as cancelled. The post-processor applies a title prefix or deletes the event depending on `delete_cancelled`. |
| `tag` | Gancio tag added to the event. |
| `title_prefix` | String prepended to the event title. |

#### `fields`

A map of Gancio field name → extraction config. Overrides the corresponding iCal value
when both are present.

**Supported field names**

| Field name | Gancio field |
| ---------- | ------------ |
| `title` | `title` |
| `start_datetime` | `start_datetime` |
| `end_datetime` | `end_datetime` / `multidate` |
| `description` | `description` |
| `image_url` | `image_url` |
| `place_name` | `place_name` |
| `place_address` | `place_address` |

**Extraction modes** (mutually exclusive; default: block-aware plain text)

| Key | Description |
| --- | ----------- |
| `attribute` | Read this HTML attribute of the matched element. |
| `as_html` | Extract `innerHTML` as a raw HTML string. |
| `flat_text` | Concatenate all text nodes without separator (`get_text(strip=True)`). Use when the CMS splits a single value across many inline/block elements. |

**Post-extraction transforms** (applied in order)

| Key | Description |
| --- | ----------- |
| `regex` | Regex applied to the extracted value; returns capture group 1 if present, otherwise the full match. |
| `time_selector` | For `start_datetime` / `end_datetime` only: CSS selector for a separate time element. Its text is appended (space-separated) before `format` parsing. Requires plain-text or `flat_text` mode. |
| `format` | `strptime` format string, or a YAML list tried in order (first match wins — useful when a time component is optional). German and English month names (full and abbreviated, e.g. `Juli`, `July`, `Jul`) are normalised to zero-padded numbers automatically. |
| `multi_match` | `start_datetime` only. `true` → select **all** elements matching `selector` instead of just the first, and produce one event per parsed datetime. Useful for venues that list all performance dates on a single detail page. Each date gets a distinct stable identity derived from the event URL and its timestamp. |

## UID and identity

- If an iCal file is fetched, its `UID` field is used as the stable identity key.
- Without iCal, the event page URL is used as the identity key. If the URL changes, the event will be duplicated rather than updated.

## Examples

### WordPress / The Events Calendar with per-event iCal

```yaml
- source_type: html
  url: https://example.org/events/
  html:
    listing_page:
      event_link_selector: "a[href*='/event/']"
    detail_page:
      ical_url_pattern: "https://example.org/event/{slug}/?ical=1"
```

### HTML-only with field selectors

```yaml
- source_type: html
  url: https://example.org/programm/
  html:
    listing_page:
      event_link_selector: "a[href*='/meetups/']"
    detail_page:
      fields:
        title:
          selector: "h1.info__header"
        start_datetime:
          selector: ".date__wrapper"
          flat_text: true
          time_selector: ".info__block h1.event__name"
          format: "%d.%m.%y %H:%M"
        description:
          selector: ".rte.about.events"
          as_html: true
        image_url:
          selector: ".info__header__image"
          attribute: style
          regex: "url\\(['\"]?([^'\"\\)]+)['\"]?\\)"
```

### TYPO3 with server-generated iCal URL

TYPO3 appends a `cHash` security token to iCal URLs that cannot be derived from
the event slug. The token is read directly from the detail page.

```yaml
- source_type: html
  url: https://example.org/veranstaltungen/
  html:
    listing_page:
      event_link_selector: "a.teaser__link[href*='/es_detail/']"
    detail_page:
      ical_link_selector: "a[href*='/veranstaltung/ical/']"
```

### WordPress with status selectors (sold out / cancelled / postponed)

```yaml
- source_type: html
  url: https://example.org/
  html:
    listing_page:
      event_link_selector: "a[href*='/events/']"
      max_events: 50
    detail_page:
      ical_url_pattern: "{base}/ics/{slug}.ics"
      status_selectors:
        - selector: "img[alt='Fällt aus']"
          cancelled: true
        - selector: "img[alt='Ausverkauft']"
          title_prefix: "Ausverkauft: "
        - selector: "img[alt='Verschoben']"
          title_prefix: "Verschoben: "
      fields:
        description:
          selector: "div.editor.events"
        image_url:
          selector: "img[src^='/img/http/']"
          attribute: src
```

## Deprecated: flat `html:` structure

The flat form (all options directly under `html:`) is deprecated and will be
removed in v2.0. A warning is printed at startup.

```yaml
# deprecated — migrate to listing_page / detail_page
html:
  event_link_selector: "a[href*='/events/']"
  ical_url_pattern: "{base}/ics/{slug}.ics"
  cancelled_selector: "img[alt='Fällt aus']"
```

Migration: move `event_link_selector`, `event_id_attribute`, and `max_events`
under `listing_page`; move all other options under `detail_page`. Replace
`cancelled_selector: "…"` with a `status_selectors` entry with `cancelled: true`.
