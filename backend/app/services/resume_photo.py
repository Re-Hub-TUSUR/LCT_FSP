"""Finds the candidate's portrait in an uploaded resume. Best effort: most resumes have none."""

import io
import logging
import zipfile
from collections.abc import Iterator
from typing import Final

from PIL import Image, ImageOps
from pypdf import PdfReader

logger = logging.getLogger(__name__)

_PDF: Final = b"%PDF"
_ZIP: Final = b"PK\x03\x04"
_DOCX_MEDIA: Final = "word/media/"
_DOCX_IMAGES: Final = (".jpg", ".jpeg", ".png", ".webp")
# The portrait sits in the header; later pages hold screenshots and diagrams.
_PDF_PAGES: Final = 1
_MAX_IMAGES: Final = 20
_MAX_IMAGE_BYTES: Final = 5 * 1024 * 1024
_MAX_PIXELS: Final = 40_000_000
# Smaller is an icon; a more stretched picture is a banner or a divider.
_MIN_SIDE: Final = 100
_MAX_RATIO: Final = 2.0
_OUTPUT_SIDE: Final = 800


def resume_photo(data: bytes) -> bytes | None:
    """JPEG of the largest portrait-like picture, or None. CPU-bound: call it off the event loop."""
    try:
        if data.startswith(_PDF):
            images = _pdf_images(data)
        elif data.startswith(_ZIP):
            images = _docx_images(data)
        else:
            return None
        portraits = [image for image in images if _is_portrait(image)]
        if not portraits:
            return None
        return _jpeg(max(portraits, key=lambda image: image.width * image.height))
    except Exception as exc:
        # The photo is a convenience: a file that breaks the image code still gives its text.
        logger.info("No photo read from the resume: %r", exc)
        return None


def _pdf_images(data: bytes) -> Iterator[Image.Image]:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted and not reader.decrypt(""):
        return
    count = 0
    for index in range(min(len(reader.pages), _PDF_PAGES)):
        for item in reader.pages[index].images:
            if count == _MAX_IMAGES:
                return
            count += 1
            if item.image is not None:
                yield item.image


def _docx_images(data: bytes) -> Iterator[Image.Image]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        files = [
            info
            for info in archive.infolist()
            if info.filename.startswith(_DOCX_MEDIA)
            and info.filename.lower().endswith(_DOCX_IMAGES)
            and info.file_size <= _MAX_IMAGE_BYTES
        ]
        for info in files[:_MAX_IMAGES]:
            try:
                image = Image.open(io.BytesIO(archive.read(info)))
            except (OSError, ValueError):
                continue
            # The header is enough for the size check; the pixels load only for the chosen one.
            if image.width * image.height <= _MAX_PIXELS:
                yield image


def _is_portrait(image: Image.Image) -> bool:
    short, long = sorted(image.size)
    return short >= _MIN_SIDE and long / short <= _MAX_RATIO


def _jpeg(image: Image.Image) -> bytes:
    upright = ImageOps.exif_transpose(image).convert("RGB")
    upright.thumbnail((_OUTPUT_SIDE, _OUTPUT_SIDE))
    buffer = io.BytesIO()
    upright.save(buffer, format="JPEG", quality=88)
    return buffer.getvalue()
