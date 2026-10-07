"""Checks for files a candidate uploads. The bytes decide the type, not the file name."""

PHOTO_LIMIT = 2 * 1024 * 1024
CHAT_ATTACHMENT_LIMIT = 10 * 1024 * 1024

_JPEG = b"\xff\xd8\xff"
_PNG = b"\x89PNG\r\n\x1a\n"
_RIFF = b"RIFF"
_WEBP = b"WEBP"
_GIF87 = b"GIF87a"
_GIF89 = b"GIF89a"
_PDF = b"%PDF"
_OLE = b"\xd0\xcf\x11\xe0"
_ZIP = b"PK\x03\x04"


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
    if data.startswith(_GIF87) or data.startswith(_GIF89):
        return "image/gif"
    return None


def sniff_chat_attachment(data: bytes) -> str | None:
    """Return a safe media type for chat files, or None when rejected."""
    image = sniff_image(data)
    if image is not None:
        return image
    if data.startswith(_PDF):
        return "application/pdf"
    if data.startswith(_OLE):
        return "application/msword"
    if data.startswith(_ZIP):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return None
