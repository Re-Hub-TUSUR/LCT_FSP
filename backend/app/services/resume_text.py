"""Reads the text of an uploaded resume and keeps the contacts out of what leaves the server."""

import io
import logging
import re
import zipfile
from dataclasses import dataclass
from typing import Final
from xml.etree import ElementTree

from pypdf import PdfReader

from app.core.errors import AppError

logger = logging.getLogger(__name__)
# pypdf warns about every font it cannot fully decode; the text is still usable.
logging.getLogger("pypdf").setLevel(logging.ERROR)

_PDF: Final = b"%PDF"
_ZIP: Final = b"PK\x03\x04"
_DOCX_BODY: Final = "word/document.xml"
_W: Final = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Enough for any real resume; bounds the parsing work and the tokens sent to the model.
MAX_PAGES: Final = 10
MAX_CHARS: Final = 20_000
_MAX_XML_BYTES: Final = 10 * 1024 * 1024
# Less text than this is a scan or an empty document.
_MIN_CHARS: Final = 80
HIDDEN: Final = "[скрыто]"

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE = re.compile(
    r"(?<![\w+])(?:\+7|8|\+\d{1,3})[\s\-(]*\d{3}[\s\-)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}(?!\d)"
)
# A t.me link, or a handle after a «Telegram:» label; a bare word after «Telegram» is a technology.
_TELEGRAM = re.compile(
    r"(?:https?://)?(?:t|telegram)\.me/(?P<link>[A-Za-z]\w{4,31})"
    r"|(?:telegram|телеграм|tg)\s*(?::\s*@?|[\-–]?\s*@)(?P<label>[A-Za-z]\w{4,31})",
    re.IGNORECASE,
)
_SPACES = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n{3,}")


class ResumeFileError(AppError):
    code = "resume_unreadable"
    default_message = "Не удалось прочитать файл. Приложите PDF или DOCX."


@dataclass(frozen=True, slots=True)
class ResumeText:
    """Text for the model with the contacts hidden; the contacts themselves stay on the server."""

    text: str
    phone: str | None
    telegram: str | None


def read_resume(data: bytes) -> ResumeText:
    """The bytes decide the format, not the file name. CPU-bound: call it off the event loop."""
    if data.startswith(_PDF):
        raw = _pdf_text(data)
    elif data.startswith(_ZIP):
        raw = _docx_text(data)
    else:
        raise ResumeFileError("Нужен файл PDF или DOCX")
    text = _tidy(raw)
    if len(text) < _MIN_CHARS:
        raise ResumeFileError(
            "В файле нет текста — похоже на скан. Приложите PDF с текстом или DOCX"
        )
    return _hide_contacts(text)


def _pdf_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise ResumeFileError("PDF защищён паролем. Снимите защиту или приложите DOCX")
        pages = (reader.pages[index] for index in range(min(len(reader.pages), MAX_PAGES)))
        return "\n".join(page.extract_text() or "" for page in pages)
    except ResumeFileError:
        raise
    except Exception as exc:
        # A broken PDF makes pypdf fail with almost any exception type.
        logger.info("Unreadable PDF resume: %r", exc)
        raise ResumeFileError("PDF повреждён. Сохраните его заново или приложите DOCX") from exc


def _docx_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            body = archive.getinfo(_DOCX_BODY)
            if body.file_size > _MAX_XML_BYTES:
                raise ResumeFileError("Документ слишком большой для резюме")
            xml = archive.read(body)
        parts: list[str] = []
        # End events visit text in document order, so text boxes inside paragraphs are not doubled.
        # Expat (2.4.1+) limits entity expansion and ElementTree resolves no external entities.
        for _, node in ElementTree.iterparse(io.BytesIO(xml), events=("end",)):  # noqa: S314
            if node.tag == f"{_W}t" and node.text:
                parts.append(node.text)
            elif node.tag == f"{_W}tab":
                parts.append(" ")
            elif node.tag in {f"{_W}p", f"{_W}br", f"{_W}cr"}:
                parts.append("\n")
    except (KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise ResumeFileError("Это не документ DOCX. Сохраните резюме в Word заново") from exc
    return "".join(parts)


def _tidy(text: str) -> str:
    lines = (_SPACES.sub(" ", line).strip() for line in text.splitlines())
    return _BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()


def _hide_contacts(text: str) -> ResumeText:
    # E-mails first: the part after @ is not a Telegram handle.
    text = _EMAIL.sub(HIDDEN, text)
    telegram_match = _TELEGRAM.search(text)
    telegram = (
        (telegram_match.group("link") or telegram_match.group("label")) if telegram_match else None
    )
    text = _TELEGRAM.sub(HIDDEN, text)
    phone_match = _PHONE.search(text)
    phone = " ".join(phone_match.group().split())[:32] if phone_match else None
    text = _PHONE.sub(HIDDEN, text)
    return ResumeText(text=text[:MAX_CHARS], phone=phone, telegram=telegram)
