"""Checks for files a candidate uploads. The bytes decide the type, not the file name."""

PHOTO_LIMIT = 2 * 1024 * 1024

_JPEG = b"\xff\xd8\xff"
_PNG = b"\x89PNG\r\n\x1a\n"
_RIFF = b"RIFF"
_WEBP = b"WEBP"


def sniff_image(data: bytes) -> str | None:
    """Return a safe image media type, or None when the bytes are not a photo we can show.

    SVG and HTML are rejected: a browser would execute them if we served them as an image
    without sniffing. The response is always this media type plus `nosniff`.
    """
    if data.startswith(_JPEG):
        return "image/jpeg"
    if data.startswith(_PNG):
        return "image/png"
    if data.startswith(_RIFF) and data[8:12] == _WEBP:
        return "image/webp"
    return None
