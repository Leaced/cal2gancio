# Roadmap

## v2.0

### Remove deprecated flat `html:` config form

The flat `html:` structure (all options at the same level) was replaced in v1.x
by the `html.listing_page` / `html.detail_page` split. v2.0 removes the flat
form entirely. A deprecation warning is printed at startup when the flat form is
detected.

Migration: see the [HTML source documentation](docs/sources/html.md).
