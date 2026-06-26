# Adding a new source type

cal2gancio uses a simple dispatcher pattern: a dictionary maps each `SourceType` to a fetch function. Adding a new source type requires three steps.

## Step 1 — Register the source type

Add a new value to the `SourceType` enum in [`cal2gancio/config.py`](../cal2gancio/config.py):

```python
class SourceType(Enum):
    ICAL = "ical"
    RSS  = "rss"   # ← new
```

Users can then set `source_type: rss` in their `config.yml` per feed.

## Step 2 — Implement the fetch function

Create a new subdirectory under `cal2gancio/sources/` and implement a `fetch_events` function that matches the `FetchFn` signature:

```
cal2gancio/sources/
├── __init__.py
├── ical/           ← existing
└── rss/            ← new
    ├── __init__.py
    └── fetch.py
```

**`cal2gancio/sources/rss/fetch.py`:**

```python
from ...config import FeedConfig


def fetch_events(
    feed: FeedConfig,
    disclaimer: str = "",
    event_link_text: str = "Event details",
    cancelled_prefix: str | None = "Cancelled: ",
) -> list[dict]:
    """
    Fetch events from an RSS feed and return a list of Gancio event dicts.
    Each dict must contain at minimum: title, description, start_datetime.
    """
    events = []
    # ... your implementation ...
    return events
```

### Required output fields

Each event dict must contain these fields for the sync to work:

| Field           | Type        | Description                                    |
| --------------- | ----------- | ---------------------------------------------- |
| `title`         | `str`       | Event title                                    |
| `start_datetime`| `int`       | Unix timestamp                                 |
| `description`   | `str`       | Event description (HTML allowed)               |
| `_uid_tag`      | `str`       | Stable lookup tag, e.g. `_ical_abc123def456`   |
| `_hash_tag`     | `str`       | Content fingerprint tag, e.g. `_icalv_a1b2c3d4`|
| `_uid_is_real`  | `bool`      | `False` if UID was synthesised from title+time |

Optional fields: `place_name`, `place_address`, `place_latitude`, `place_longitude`, `image_url`, `multidate`, `tags`, `recurrent[frequency]`, `recurrent[days]`, `_cancelled`, `_exdates`.

The easiest way to generate the internal tags correctly is to reuse the helpers from `sources/ical/tags.py`:

```python
from ..ical.tags import uid_tag, hash_tag, content_hash

_uid_tag  = uid_tag(uid_string)
_hash_tag = hash_tag(content_hash(event_dict))
```

## Step 3 — Register the fetcher

Add an entry to `_FETCHERS` in [`cal2gancio/sources/__init__.py`](../cal2gancio/sources/__init__.py):

```python
from .ical.fetch import fetch_events as _ical_fetch
from .rss.fetch  import fetch_events as _rss_fetch   # ← new

_FETCHERS: dict[SourceType, FetchFn] = {
    SourceType.ICAL: _ical_fetch,
    SourceType.RSS:  _rss_fetch,   # ← new
}
```

That's all. The title filter, past-event filtering, cancelled handling, and sync logic in `sync/feed.py` and `sync/decision.py` apply automatically to every source type.
