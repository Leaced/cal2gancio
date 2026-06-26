"""Extracts image URLs from iCal ATTACH properties."""

_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")


def parse_image_url(component) -> str | None:
    """
    Returns the URL of an attached image, or None.

    Detection order:
      1. FMTTYPE parameter starts with "image/"  (most reliable)
      2. URL ends with a known image extension    (fallback)
    """
    attach = component.get("ATTACH")
    if not attach:
        return None

    url = str(attach)
    if not url.startswith("http"):
        return None  # binary blob, not a URL

    if hasattr(attach, "params"):
        if attach.params.get("FMTTYPE", "").startswith("image/"):
            return url

    if any(url.lower().split("?")[0].endswith(ext) for ext in _IMAGE_EXTENSIONS):
        return url

    return None
