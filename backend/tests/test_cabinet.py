from httpx import AsyncClient

from tests.conftest import API, bearer, register_and_login

RESUME = {
    "displayName": "Иван Иванов",
    "headline": "Backend-разработчик",
    "specialization": "backend",
    "city": "Казань",
    "experienceYears": 4,
    "workFormats": ["hybrid"],
    "stack": ["Python", "PostgreSQL"],
    "softSkills": ["Наставничество"],
    "about": "Делаю платёжные сервисы.",
    "phone": "+7 900 000-00-00",
    "telegram": "@ivan",
    "salaryExpectation": 220000,
}

COMPANY = {
    "name": "ООО «Технологии»",
    "industry": "Финтех",
    "description": (
        "Платёжный шлюз для банков и магазинов. Команда из шести человек ищет тех, "
        "кто умеет держать нагрузку и спокойно разбирать инциденты."
    ),
    "city": "Москва",
    "size": "11-50",
    "website": "https://company.example",
    "contactEmail": "hr@company.example",
}


async def test_candidate_resume_is_private_until_an_invitation_is_accepted(
    client: AsyncClient,
) -> None:
    token = await register_and_login(client, "ivan@fsp.ru")
    missing = await client.get(f"{API}/candidates/me", headers=bearer(token))
    assert missing.status_code == 404

    incomplete = await client.patch(
        f"{API}/candidates/me", headers=bearer(token), json={"displayName": "Иван"}
    )
    assert incomplete.status_code == 400

    saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=RESUME)
    assert saved.status_code == 200, saved.text
    body = saved.json()
    assert body["displayName"] == "Иван Иванов"
    assert body["category"] is None
    assert body["specialization"] == "backend"
    assert body["gradeVerified"] is False
    assert body["assessmentStatus"] == "not_taken"
    assert body["searching"] is True
    assert body["contacts"]["email"] == "ivan@fsp.ru"
    assert body["contacts"]["telegram"] == "ivan"
    assert body["fspLinked"] is False

    employer = await register_and_login(client, "hr-view@fsp.ru", role="employer")
    seen = await client.get(f"{API}/candidates/{body['id']}", headers=bearer(employer))
    assert seen.status_code == 200
    assert seen.json()["contacts"] is None
    assert seen.json()["stack"] == ["Python", "PostgreSQL"]

    hidden = await client.patch(
        f"{API}/candidates/me/searching", headers=bearer(token), json={"searching": False}
    )
    assert hidden.status_code == 200
    assert hidden.json()["searching"] is False
    gone = await client.get(f"{API}/candidates/{body['id']}", headers=bearer(employer))
    assert gone.status_code == 404


async def test_fsp_id_is_unique_and_can_be_unlinked(client: AsyncClient) -> None:
    first = await register_and_login(client, "first@fsp.ru")
    await client.patch(f"{API}/candidates/me", headers=bearer(first), json=RESUME)
    linked = await client.post(
        f"{API}/candidates/me/fsp-link", headers=bearer(first), json={"fspMemberId": "104582"}
    )
    assert linked.status_code == 200
    assert linked.json()["fspLinked"] is True
    assert linked.json()["fspMemberId"] == "104582"
    assert linked.json()["fspAchievements"] == []

    second = await register_and_login(client, "second@fsp.ru")
    await client.patch(f"{API}/candidates/me", headers=bearer(second), json=RESUME)
    conflict = await client.post(
        f"{API}/candidates/me/fsp-link", headers=bearer(second), json={"fspMemberId": "104582"}
    )
    assert conflict.status_code == 409

    cleared = await client.delete(f"{API}/candidates/me/fsp-link", headers=bearer(first))
    assert cleared.status_code == 200
    assert cleared.json()["fspLinked"] is False
    assert cleared.json()["fspMemberId"] is None


async def test_employer_company_profile_and_role_split(client: AsyncClient) -> None:
    employer = await register_and_login(client, "hr@fsp.ru", role="employer")
    missing = await client.get(f"{API}/companies/me", headers=bearer(employer))
    assert missing.status_code == 404

    short = await client.put(
        f"{API}/companies/me",
        headers=bearer(employer),
        json={**COMPANY, "description": "слишком коротко"},
    )
    assert short.status_code == 422

    saved = await client.put(f"{API}/companies/me", headers=bearer(employer), json=COMPANY)
    assert saved.status_code == 200, saved.text
    company_id = saved.json()["id"]
    assert saved.json()["city"] == "Москва"
    assert saved.json()["contactEmail"] == "hr@company.example"

    public = await client.get(f"{API}/companies/{company_id}")
    assert public.status_code == 200
    assert public.json()["name"] == "ООО «Технологии»"

    candidate = await register_and_login(client, "seeker@fsp.ru")
    forbidden = await client.put(f"{API}/companies/me", headers=bearer(candidate), json=COMPANY)
    assert forbidden.status_code == 403
    foreign_resume = await client.get(f"{API}/candidates/me", headers=bearer(employer))
    assert foreign_resume.status_code == 403


async def test_second_resume_stays_behind_the_priority_one(client: AsyncClient) -> None:
    token = await register_and_login(client, "two@fsp.ru")
    saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=RESUME)
    assert saved.status_code == 200, saved.text
    added = await client.post(
        f"{API}/candidates/me/resumes",
        headers=bearer(token),
        json={
            "headline": "DevOps-инженер",
            "specialization": "devops",
            "stack": ["Kubernetes", "Terraform"],
            "softSkills": [],
            "about": None,
            "experienceYears": 3,
        },
    )
    assert added.status_code == 200, added.text
    resumes = added.json()["resumes"]
    assert [item["isPrimary"] for item in resumes] == [True, False]
    assert resumes[0]["specialization"] == "backend"
    assert resumes[1]["headline"] == "DevOps-инженер"

    promoted = await client.post(
        f"{API}/candidates/me/resumes/{resumes[1]['id']}/primary",
        headers=bearer(token),
    )
    assert promoted.status_code == 200, promoted.text
    body = promoted.json()
    assert body["specialization"] == "devops"
    assert body["resumes"][0]["isPrimary"] is True
    assert body["resumes"][0]["specialization"] == "devops"
    assert body["resumes"][1]["specialization"] == "backend"


async def test_photo_rejects_a_file_that_is_not_an_image(client: AsyncClient) -> None:
    token = await register_and_login(client, "photo@fsp.ru")
    await client.patch(f"{API}/candidates/me", headers=bearer(token), json=RESUME)
    rejected = await client.post(
        f"{API}/candidates/me/photo",
        headers=bearer(token),
        files={"file": ("face.svg", b"<svg><script>alert(1)</script></svg>", "image/svg+xml")},
    )
    assert rejected.status_code == 400

    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    accepted = await client.post(
        f"{API}/candidates/me/photo",
        headers=bearer(token),
        files={"file": ("face.png.exe", png, "application/octet-stream")},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["hasPhoto"] is True
    photo = await client.get(f"{API}/candidates/me/photo", headers=bearer(token))
    assert photo.status_code == 200
    assert photo.headers["content-type"].startswith("image/png")
    assert photo.headers["x-content-type-options"] == "nosniff"
    assert photo.content.startswith(b"\x89PNG")
