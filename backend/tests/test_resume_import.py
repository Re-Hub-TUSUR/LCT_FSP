"""Resume upload: the model never sees the contacts, and its answer is cleaned into a draft."""

import base64
import io
import zipfile
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fpdf import FPDF
from httpx import AsyncClient, Response
from PIL import Image

from app.dependencies.services import get_resume_reader
from app.services.resume_photo import resume_photo
from tests.conftest import API, bearer, register_and_login

RESUME = (
    "Иван Петров",
    "Python-разработчик, Москва",
    "Телефон: +7 (999) 123-45-67, почта ivan.petrov@example.com, Telegram: @ivan_dev",
    "Опыт работы 5 лет: FastAPI, PostgreSQL, Docker. Рассматриваю удалённую работу.",
)


def picture(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (64, 47, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def docx(*paragraphs: str, media: dict[str, bytes] | None = None) -> bytes:
    body = "".join(f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>" for text in paragraphs)
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            f'<w:document xmlns:w="{namespace}"><w:body>{body}</w:body></w:document>',
        )
        for name, data in (media or {}).items():
            archive.writestr(f"word/media/{name}", data)
    return buffer.getvalue()


class StubReader:
    """Answers like a sloppy model: values the draft must not pass on as they are."""

    def __init__(self) -> None:
        self.texts: list[str] = []

    async def read(self, text: str) -> dict[str, Any]:
        self.texts.append(text)
        return {
            "display_name": "  Иван   Петров ",
            "headline": "Python-разработчик",
            "specialization": "python",
            "experience_years": 5,
            "city": "Москва",
            "work_formats": ["remote", "remote", "space"],
            "salary_expectation": -1,
            "stack": ["FastAPI", "fastapi", "PostgreSQL", "x" * 41],
            "soft_skills": [],
            "about": None,
        }


@pytest.fixture
async def reader(client: AsyncClient) -> AsyncIterator[StubReader]:
    stub = StubReader()
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_resume_reader] = lambda: stub
    yield stub
    app.dependency_overrides.pop(get_resume_reader)


async def upload(client: AsyncClient, token: str, data: bytes) -> Response:
    return await client.post(
        f"{API}/candidates/me/resume", headers=bearer(token), files={"file": ("cv.docx", data)}
    )


async def test_resume_becomes_a_clean_draft_without_sending_contacts(
    client: AsyncClient, reader: StubReader
) -> None:
    token = await register_and_login(client, "resume@fsp.ru")

    response = await upload(client, token, docx(*RESUME))

    assert response.status_code == 200, response.text
    assert response.json() == {
        "displayName": "Иван Петров",
        "headline": "Python-разработчик",
        "specialization": None,
        "city": "Москва",
        "experienceYears": 5,
        "workFormats": ["remote"],
        "stack": ["FastAPI", "PostgreSQL"],
        "softSkills": [],
        "about": None,
        "salaryExpectation": None,
        "phone": "+7 (999) 123-45-67",
        "telegram": "ivan_dev",
        "photo": None,
    }
    [text] = reader.texts
    assert "Иван Петров" in text
    for contact in ("123-45-67", "ivan.petrov", "ivan_dev"):
        assert contact not in text


async def test_upload_explains_a_missing_key_and_a_wrong_file(client: AsyncClient) -> None:
    token = await register_and_login(client, "resume-errors@fsp.ru")

    no_key = await upload(client, token, docx(*RESUME))
    image = await upload(client, token, b"\x89PNG\r\n\x1a\n" + bytes(100))

    assert no_key.status_code == 503
    assert no_key.json()["error"]["code"] == "resume_reader_unavailable"
    assert image.status_code == 400
    assert image.json()["error"]["code"] == "resume_unreadable"


async def test_portrait_from_the_resume_comes_with_the_draft(
    client: AsyncClient, reader: StubReader
) -> None:
    token = await register_and_login(client, "resume-photo@fsp.ru")
    media = {
        "image1.png": picture(16, 16),  # an icon
        "image2.png": picture(300, 400),
        "image3.png": picture(1200, 100),  # a banner
    }

    response = await upload(client, token, docx(*RESUME, media=media))

    assert response.status_code == 200, response.text
    photo = Image.open(io.BytesIO(base64.b64decode(response.json()["photo"])))
    assert (photo.format, photo.size) == ("JPEG", (300, 400))


def test_portrait_is_read_from_the_first_page_of_a_pdf() -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.image(Image.new("RGB", (240, 320), (64, 47, 255)), x=10, y=10, w=30)
    pdf.add_page()
    pdf.image(Image.new("RGB", (900, 900), (255, 0, 0)), x=10, y=10, w=100)

    photo = resume_photo(bytes(pdf.output()))

    assert photo is not None
    assert Image.open(io.BytesIO(photo)).size == (240, 320)
    assert resume_photo(b"not a document") is None
