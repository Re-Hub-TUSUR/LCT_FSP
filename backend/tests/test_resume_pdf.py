import io
from datetime import UTC, datetime
from urllib.parse import unquote

import pytest
from httpx import AsyncClient
from PIL import Image
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import hash_password
from app.repositories.candidate import CandidateRepository
from app.schemas.candidate import ExperienceEntry
from app.seed.fixtures import SeedData, load_seed_data
from app.seed.generate import DEMO_CANDIDATE_EMAIL, DEMO_EMPLOYER_EMAIL
from app.seed.loader import seed_database, seed_id
from app.services.presenters import candidate_read
from app.services.resume_pdf import period, render_resume, years
from tests.conftest import API, PASSWORD, bearer, login, register_and_login


@pytest.fixture
async def data(sessionmaker: async_sessionmaker[AsyncSession]) -> SeedData:
    data = load_seed_data()
    async with sessionmaker() as session:
        await seed_database(session, data, password_hash=hash_password(PASSWORD))
        await session.commit()
    return data


def text_of(pdf: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf))
    return "\n".join(page.extract_text() for page in reader.pages)


def png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), (64, 47, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


async def test_candidate_downloads_own_resume_with_contacts_and_photo(
    client: AsyncClient, data: SeedData
) -> None:
    token = await login(client, DEMO_CANDIDATE_EMAIL)
    uploaded = await client.post(
        f"{API}/candidates/me/photo",
        files={"file": ("me.png", png(), "image/png")},
        headers=bearer(token),
    )
    assert uploaded.status_code == 200, uploaded.text
    me = uploaded.json()

    response = await client.get(f"{API}/candidates/{me['id']}/resume.pdf", headers=bearer(token))

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    disposition = response.headers["content-disposition"]
    assert unquote(disposition.split("filename*=UTF-8''")[1]) == (
        f"Резюме — {me['displayName']}.pdf"
    )
    text = text_of(response.content)
    assert me["displayName"] in text
    assert me["headline"] in text
    assert DEMO_CANDIDATE_EMAIL in text
    assert "ОПЫТ РАБОТЫ" in text
    assert len(PdfReader(io.BytesIO(response.content)).pages[0].images) == 1


async def test_employer_gets_the_resume_without_hidden_contacts(
    client: AsyncClient, data: SeedData
) -> None:
    token = await login(client, DEMO_EMPLOYER_EMAIL)
    candidate = next(c for c in data.candidates if c.is_visible_to_employers)
    hidden = next(c for c in data.candidates if not c.is_visible_to_employers)

    response = await client.get(
        f"{API}/candidates/{seed_id('candidate', candidate.key)}/resume.pdf", headers=bearer(token)
    )
    missing = await client.get(
        f"{API}/candidates/{seed_id('candidate', hidden.key)}/resume.pdf", headers=bearer(token)
    )

    assert response.status_code == 200, response.text
    text = text_of(response.content)
    assert candidate.display_name in text
    # No accepted invitation: the email and the phone stay hidden, as on the site.
    assert "Почта" not in text
    assert "Телефон" not in text
    assert missing.status_code == 404


async def test_another_candidate_cannot_download_a_resume(
    client: AsyncClient, data: SeedData
) -> None:
    token = await register_and_login(client, "curious@example.com")
    candidate = next(c for c in data.candidates if c.is_visible_to_employers)

    response = await client.get(
        f"{API}/candidates/{seed_id('candidate', candidate.key)}/resume.pdf", headers=bearer(token)
    )

    assert response.status_code == 404


def test_periods_and_plurals_read_naturally() -> None:
    now = datetime(2026, 10, 9, tzinfo=UTC)
    current = ExperienceEntry(company="Яндекс", position="Разработчик", start="2024-08")
    finished = ExperienceEntry(company="Авито", position="Стажёр", start="2023-01", end="2023-01")

    assert period(current, now=now) == "август 2024 — по настоящее время · 2 года 3 месяца"
    assert period(finished, now=now) == "январь 2023 — январь 2023 · 1 месяц"
    assert [years(n) for n in (1, 2, 5, 11, 21)] == ["1 год", "2 года", "5 лет", "11 лет", "21 год"]


async def test_text_the_font_cannot_draw_is_left_out(
    sessionmaker: async_sessionmaker[AsyncSession], data: SeedData
) -> None:
    candidate = data.candidates[0]
    async with sessionmaker() as session:
        profile = await CandidateRepository(session).get(seed_id("candidate", candidate.key))
        assert profile is not None
        resume = candidate_read(profile).model_copy(update={"about": "Люблю код 🚀 и тесты"})

    text = text_of(render_resume(resume, photo=b"not an image", now=datetime.now(UTC)))

    assert "Люблю код  и тесты" in text
