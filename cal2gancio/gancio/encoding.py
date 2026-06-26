"""
Helpers for encoding event dicts as multipart/form-data.

Gancio requires multipart/form-data for all event writes (POST and PUT),
because it needs to support image_url alongside other string fields.
Using requests' files= parameter with (None, value) tuples forces this encoding.
"""

from dataclasses import dataclass


@dataclass
class ApiResult:
    success: bool
    gancio_id: int | None
    error: str = ""


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
            fields.append((key, (None, str(value))))
    return fields


def strip_meta(event: dict) -> dict:
    """Remove internal _* keys so they are not sent to the Gancio API."""
    return {k: v for k, v in event.items() if not k.startswith("_")}
