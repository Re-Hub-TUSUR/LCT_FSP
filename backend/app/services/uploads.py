"""Checks for files a candidate uploads. The bytes decide the type, not the file name."""

import io
import warnings
import zipfile

from PIL import Image

PHOTO_LIMIT = 2 * 1024 * 1024
CHAT_ATTACHMENT_LIMIT = 10 * 1024 * 1024
RESUME_LIMIT = 5 * 1024 * 1024
# 40 Mpx is more than any phone camera; a few kilobytes of PNG could otherwise unpack into
# gigabytes when the resume PDF decodes the photo.
MAX_IMAGE_PIXELS = 40_000_000

_JPEG = b"\xff\xd8\xff"
_PNG = b"\x89PNG\r\n\x1a\n"
_RIFF = b"RIFF"
_WEBP = b"WEBP"
_GIF87 = b"GIF87a"
_GIF89 = b"GIF89a"
_PDF = b"%PDF"
_OLE = b"\xd0\xcf\x11\xe0"
_ZIP = b"PK\x03\x04"
_DOCX_BODY = "word/document.xml"
_DOCX_MACROS = "word/vbaProject.bin"


def _sane_size(data: bytes) -> bool:
    """Reads only the header: the picture is not decoded here."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                width, height = image.size
    except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        return False
    return 0 < width * height <= MAX_IMAGE_PIXELS


def sniff_image(data: bytes) -> str | None:
    """Return a safe image media type, or None when the bytes are not a photo we can show.

    SVG and HTML are rejected: a browser would execute them if we served them as an image
    without sniffing. The response is always this media type plus `nosniff`. A header that
    promises more than MAX_IMAGE_PIXELS is rejected too.
    """
    if data.startswith(_JPEG):
        media = "image/jpeg"
    elif data.startswith(_PNG):
        media = "image/png"
    elif data.startswith(_RIFF) and data[8:12] == _WEBP:
        media = "image/webp"
    elif data.startswith(_GIF87) or data.startswith(_GIF89):
        media = "image/gif"
    else:
        return None
    return media if _sane_size(data) else None


def is_docx(data: bytes) -> bool:
    """A Word document: a ZIP with the document body and without macros.

    Any OOXML file (a .pptx, an .xlsx) and any archive is a ZIP too, so the magic bytes alone
    would let them through as «Word».
    """
    if not data.startswith(_ZIP):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())
    except zipfile.BadZipFile:
        return False
    return _DOCX_BODY in names and _DOCX_MACROS not in names


def sniff_chat_attachment(data: bytes) -> str | None:
    """Return a safe media type for chat files, or None when rejected."""
    image = sniff_image(data)
    if image is not None:
        return image
    if data.startswith(_PDF):
        return "application/pdf"
    if data.startswith(_OLE):
        return "application/msword"
    if is_docx(data):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return None
