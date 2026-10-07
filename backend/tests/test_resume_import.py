"""Resume upload: the model never sees the contacts, and its answer is cleaned into a draft."""

import io
import zipfile
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient, Response

from app.dependencies.services import get_resume_reader
from tests.conftest import API, bearer, register_and_login

RESUME = (
    "Иван Петров",
    "Python-разработчик, Москва",
    "Телефон: +7 (999) 123-45-67, почта ivan.petrov@example.com, Telegram: @ivan_dev",
    "Опыт работы 5 лет: FastAPI, PostgreSQL, Docker. Рассматриваю удалённую работу.",
)


def docx(*paragraphs: str) -> bytes:
    body = "".join(f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>" for text in paragraphs)
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            f'<w:document xmlns:w="{namespace}"><w:body>{body}</w:body></w:document>',
        )
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
