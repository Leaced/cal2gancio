"""
Helpers for encoding event dicts as multipart/form-data.

Gancio requires multipart/form-data for all event writes (POST and PUT),
because it needs to support image_url alongside other string fields.
Using requests' files= parameter with (None, value) tuples forces this encoding.
"""

from dataclasses import dataclass
from urllib.parse import quote, urlsplit, urlunsplit


@dataclass
class ApiResult:
    success: bool
    gancio_id: int | None
    error: str = ""


def _encode_image_url(url: str) -> str:
    """Percent-encode non-ASCII characters in the path of an image URL.

    Gancio fetches image_url server-side; non-ASCII filenames (e.g. © in the
    path) cause its HTTP client to receive a 404 unless the path is encoded.
    """
    parts = urlsplit(url)
    encoded_path = quote(parts.path, safe="/:@!$&'()*+,;=")
    return urlunsplit((parts.scheme, parts.netloc, encoded_path, parts.query, parts.fragment))


def to_multipart(data: dict) -> list[tuple]:
    """
    Convert a flat dict to (key, (None, str)) tuples for requests' files= param.
    List values are expanded into multiple tuples with the same key
    (required for Gancio's array fields like tags and recurrent[days]).
    """
    fields = []
    for key, value in data.items():
        if isinstance(value, list):
            for item in value:
                fields.append((key, (None, str(item))))
        elif value is not None:
            v = _encode_image_url(str(value)) if key == "image_url" else str(value)
            fields.append((key, (None, v)))
    return fields


def strip_meta(event: dict) -> dict:
    """Remove internal _* keys so they are not sent to the Gancio API."""
    return {k: v for k, v in event.items() if not k.startswith("_")}
