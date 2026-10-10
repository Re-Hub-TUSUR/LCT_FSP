from datetime import date

from httpx import AsyncClient

from tests.conftest import API, bearer, make_inn, register_and_login, tiny_image

RESUME = {
    "displayName": "Иван Иванов",
    "headline": "Backend-разработчик",
    "specialization": "backend",
    "city": "Казань",
    "experienceYears": 4,
    "workFormats": ["hybrid"],
    "employmentTypes": ["full"],
    "stack": ["Python", "PostgreSQL", "Docker"],
    "softSkills": ["Наставничество"],
    "about": "Делаю платёжные сервисы.",
    "phone": "+7 900 000-00-00",
    "telegram": "@ivan",
    "salaryExpectation": 220000,
    "profileDisplayConsent": True,
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
    "inn": "7707083893",
    "kpp": "773601001",
    "ogrn": "1027700132195",
}


async def employer_with_company(client: AsyncClient, email: str) -> str:
    """The candidate bank opens to an employer with a company profile only."""
    token = await register_and_login(client, email, role="employer")
    saved = await client.put(
        f"{API}/companies/me", headers=bearer(token), json={**COMPANY, "inn": make_inn(email)}
    )
    assert saved.status_code == 200, saved.text
    return token


async def test_candidate_resume_is_private_until_an_invitation_is_accepted(
    client: AsyncClient,
) -> None:
    token = await register_and_login(client, "ivan@fsp.ru")
    missing = await client.get(f"{API}/candidates/me", headers=bearer(token))
    assert missing.status_code == 200
    assert missing.json() is None

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

    stranger = await register_and_login(client, "no-company@fsp.ru", role="employer")
    closed = await client.get(f"{API}/candidates/{body['id']}", headers=bearer(stranger))
    assert closed.status_code == 409

    employer = await employer_with_company(client, "hr-view@fsp.ru")
    seen = await client.get(f"{API}/candidates/{body['id']}", headers=bearer(employer))
    assert seen.status_code == 200
    assert seen.json()["contacts"] is None
    assert seen.json()["stack"] == ["Python", "PostgreSQL", "Docker"]
    assert seen.json()["jobStatus"] == "open"
    assert seen.json()["lastActiveAt"] is not None

    hidden = await client.patch(
        f"{API}/candidates/me/searching", headers=bearer(token), json={"searching": False}
    )
    assert hidden.status_code == 200
    assert hidden.json()["searching"] is False
    assert hidden.json()["jobStatus"] == "not_looking"
    gone = await client.get(f"{API}/candidates/{body['id']}", headers=bearer(employer))
    assert gone.status_code == 404

    active = await client.patch(
        f"{API}/candidates/me/searching", headers=bearer(token), json={"jobStatus": "active"}
    )
    assert active.json()["searching"] is True
    back = await client.get(f"{API}/candidates/{body['id']}", headers=bearer(employer))
    assert back.status_code == 200


async def test_new_resume_needs_the_fields_of_the_spec(client: AsyncClient) -> None:
    token = await register_and_login(client, "spec@fsp.ru")
    no_contact = {**RESUME, "phone": None, "telegram": None}
    refused = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=no_contact)
    assert refused.status_code == 400
    assert "Telegram" in refused.json()["error"]["message"]

    short_stack = {**RESUME, "stack": ["Python", "SQL"]}
    refused = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=short_stack)
    assert refused.status_code == 400


async def test_birth_date_marks_minors_and_stays_private(client: AsyncClient) -> None:
    today = date.today()
    token = await register_and_login(client, "teen@fsp.ru")
    child = {**RESUME, "birthDate": f"{today.year - 13}-01-01"}
    refused = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=child)
    assert refused.status_code == 400

    teen = {**RESUME, "birthDate": f"{today.year - 16}-01-01"}
    saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=teen)
    assert saved.status_code == 200, saved.text
    assert saved.json()["isMinor"] is True
    assert saved.json()["birthDate"] == f"{today.year - 16}-01-01"

    employer = await employer_with_company(client, "hr-teen@fsp.ru")
    seen = await client.get(f"{API}/candidates/{saved.json()['id']}", headers=bearer(employer))
    assert seen.json()["isMinor"] is True
    assert "birthDate" not in seen.json()


async def test_experience_periods_set_the_years(client: AsyncClient) -> None:
    token = await register_and_login(client, "periods@fsp.ru")
    resume = {
        **RESUME,
        "experienceYears": None,
        "experienceEntries": [
            {"company": "Банк", "position": "Разработчик", "start": "2019-01", "end": "2021-12"},
            {"company": "Стартап", "position": "Тимлид", "start": "2021-06", "end": "2022-12"},
        ],
        "education": [{"institution": "ТУСУР", "specialty": "Программная инженерия"}],
        "githubUrl": "github.com/ivan",
    }
    saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=resume)
    assert saved.status_code == 200, saved.text
    body = saved.json()
    assert body["experienceYears"] == 4
    assert body["githubUrl"] == "https://github.com/ivan"
    assert body["education"][0]["institution"] == "ТУСУР"

    none = await client.patch(
        f"{API}/candidates/me", headers=bearer(token), json={"noExperience": True}
    )
    assert none.json()["experienceYears"] == 0
    assert none.json()["experienceEntries"] == []

    foreign = await client.patch(
        f"{API}/candidates/me", headers=bearer(token), json={"githubUrl": "https://evil.example"}
    )
    assert foreign.status_code == 400


async def test_employer_company_profile_and_role_split(client: AsyncClient) -> None:
    employer = await register_and_login(client, "hr@fsp.ru", role="employer")
    missing = await client.get(f"{API}/companies/me", headers=bearer(employer))
    assert missing.status_code == 200
    assert missing.json() is None

    short = await client.put(
        f"{API}/companies/me",
        headers=bearer(employer),
        json={**COMPANY, "description": "слишком коротко"},
    )
    assert short.status_code == 422
    odd_size = await client.put(
        f"{API}/companies/me", headers=bearer(employer), json={**COMPANY, "size": "38173178318637"}
    )
    assert odd_size.status_code == 422

    saved = await client.put(f"{API}/companies/me", headers=bearer(employer), json=COMPANY)
    assert saved.status_code == 200, saved.text
    company_id = saved.json()["id"]
    assert saved.json()["city"] == "Москва"
    assert saved.json()["contactEmail"] == "hr@company.example"

    public = await client.get(f"{API}/companies/{company_id}")
    assert public.status_code == 200
    assert public.json()["name"] == "ООО «Технологии»"

    assert public.json()["inn"] == "7707083893"
    assert public.json()["itAccredited"] is False

    candidate = await register_and_login(client, "seeker@fsp.ru")
    forbidden = await client.put(f"{API}/companies/me", headers=bearer(candidate), json=COMPANY)
    assert forbidden.status_code == 403
    foreign_resume = await client.get(f"{API}/candidates/me", headers=bearer(employer))
    assert foreign_resume.status_code == 403


async def test_inn_is_checked_and_unique(client: AsyncClient) -> None:
    employer = await register_and_login(client, "inn@fsp.ru", role="employer")
    wrong = await client.put(
        f"{API}/companies/me", headers=bearer(employer), json={**COMPANY, "inn": "7707083890"}
    )
    assert wrong.status_code == 422
    saved = await client.put(f"{API}/companies/me", headers=bearer(employer), json=COMPANY)
    assert saved.status_code == 200, saved.text

    other = await register_and_login(client, "inn-copy@fsp.ru", role="employer")
    taken = await client.put(f"{API}/companies/me", headers=bearer(other), json=COMPANY)
    assert taken.status_code == 409
    own = await client.put(
        f"{API}/companies/me", headers=bearer(other), json={**COMPANY, "inn": make_inn("other")}
    )
    assert own.status_code == 200, own.text


async def test_company_logo_and_owner_name(client: AsyncClient) -> None:
    employer = await register_and_login(client, "logo@fsp.ru", role="employer")
    named = await client.patch(
        f"{API}/users/me",
        headers=bearer(employer),
        json={"firstName": "Анна", "lastName": "Петрова", "phone": "+7 900 111-22-33"},
    )
    assert named.status_code == 200, named.text
    me = await client.get(f"{API}/users/me", headers=bearer(employer))
    assert me.json()["firstName"] == "Анна"

    saved = await client.put(f"{API}/companies/me", headers=bearer(employer), json=COMPANY)
    company_id = saved.json()["id"]
    rejected = await client.post(
        f"{API}/companies/me/logo",
        headers=bearer(employer),
        files={"file": ("logo.svg", b"<svg/>", "image/svg+xml")},
    )
    assert rejected.status_code == 400
    png = tiny_image()
    uploaded = await client.post(
        f"{API}/companies/me/logo",
        headers=bearer(employer),
        files={"file": ("logo.png", png, "image/png")},
    )
    assert uploaded.json()["hasLogo"] is True
    logo = await client.get(f"{API}/companies/{company_id}/logo")
    assert logo.headers["content-type"].startswith("image/png")
    assert logo.headers["x-content-type-options"] == "nosniff"


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

    png = tiny_image()
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
