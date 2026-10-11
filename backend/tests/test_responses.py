"""«Я понравился»: answering an incoming like makes the interest mutual and opens the chat."""

import json
import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from tests.conftest import API, bearer
from tests.test_invitations import candidate_with_resume, employer_with_company
from tests.test_vacancies import VACANCY


async def test_answering_an_inbound_like_opens_the_chat_for_both_sides(
    client: AsyncClient,
) -> None:
    employer = await employer_with_company(client, "hr@fsp.ru")
    candidate, candidate_id = await candidate_with_resume(client, "dev@fsp.ru")
    vacancy = await client.post(f"{API}/vacancies", headers=bearer(employer), json=VACANCY)
    assert vacancy.status_code == 201, vacancy.text

    # The recruiter likes the candidate without naming a vacancy.
    liked = await client.put(
        f"{API}/candidates/{candidate_id}/reaction", headers=bearer(employer), json={"kind": "like"}
    )
    assert liked.status_code == 200, liked.text

    inbound = (await client.get(f"{API}/responses/inbound", headers=bearer(candidate))).json()
    assert [item["companyName"] for item in inbound] == ["ООО «Технологии»"]
    company_id = inbound[0]["companyId"]
    for token in (candidate, employer):
        assert (await client.get(f"{API}/conversations", headers=bearer(token))).json() == []

    answered = await client.post(
        f"{API}/responses/inbound/companies/{company_id}/respond", headers=bearer(candidate)
    )
    assert answered.status_code == 204, answered.text

    assert (await client.get(f"{API}/responses/inbound", headers=bearer(candidate))).json() == []
    mine = (await client.get(f"{API}/conversations", headers=bearer(candidate))).json()
    theirs = (await client.get(f"{API}/conversations", headers=bearer(employer))).json()
    assert [chat["peer"]["id"] for chat in mine] == [company_id]
    assert [chat["peer"]["id"] for chat in theirs] == [candidate_id]
    assert mine[0]["id"] == theirs[0]["id"]

    sent = await client.post(
        f"{API}/conversations/{mine[0]['id']}/messages",
        headers=bearer(candidate),
        json={"text": "Здравствуйте!"},
    )
    assert sent.status_code == 201, sent.text


async def test_like_names_its_vacancy_and_meeting_asks_for_an_answer(client: AsyncClient) -> None:
    employer = await employer_with_company(client, "hr-pick@fsp.ru")
    candidate, candidate_id = await candidate_with_resume(client, "dev-pick@fsp.ru")
    older = await client.post(f"{API}/vacancies", headers=bearer(employer), json=VACANCY)
    newer = await client.post(
        f"{API}/vacancies", headers=bearer(employer), json={**VACANCY, "title": "Go-разработчик"}
    )
    draft = await client.post(
        f"{API}/vacancies",
        headers=bearer(employer),
        json={**VACANCY, "title": "Черновик", "publish": False},
    )
    company_id = older.json()["company"]["id"]

    # The company page lists the published vacancies of the company, newest first.
    listed = await client.get(f"{API}/vacancies", params={"companyId": company_id})
    assert [item["id"] for item in listed.json()["items"]] == [
        newer.json()["id"],
        older.json()["id"],
    ]
    assert draft.json()["id"] not in {item["id"] for item in listed.json()["items"]}

    me = (await client.get(f"{API}/users/me", headers=bearer(candidate))).json()
    hub = client._transport.app.state.notifications  # type: ignore[attr-defined]
    queue = hub.subscribe(uuid.UUID(me["id"]))

    # The recruiter picks the candidate for the older vacancy, not for the latest one.
    liked = await client.put(
        f"{API}/candidates/{candidate_id}/reaction",
        headers=bearer(employer),
        json={"kind": "like", "vacancyId": older.json()["id"]},
    )
    assert liked.status_code == 200, liked.text
    event = json.loads(queue.get_nowait())
    assert (event["type"], event["vacancyTitle"]) == ("company_liked", VACANCY["title"])

    (inbound,) = (await client.get(f"{API}/responses/inbound", headers=bearer(candidate))).json()
    assert (inbound["vacancyId"], inbound["vacancyTitle"]) == (older.json()["id"], VACANCY["title"])
    assert inbound["salary"] == VACANCY["salary"]

    answered = await client.post(
        f"{API}/responses/inbound/companies/{company_id}/respond",
        headers=bearer(candidate),
        params={"vacancyId": inbound["vacancyId"]},
    )
    assert answered.status_code == 204, answered.text
    favourites = await client.get(
        f"{API}/vacancies/feed", headers=bearer(candidate), params={"view": "liked"}
    )
    assert [item["vacancy"]["id"] for item in favourites.json()["items"]] == [older.json()["id"]]

    starts_at = (datetime.now(UTC) + timedelta(days=3)).replace(microsecond=0)
    scheduled = await client.post(
        f"{API}/calendar/events",
        headers=bearer(employer),
        json={
            "candidateId": candidate_id,
            "title": "Техническое интервью",
            "startsAt": starts_at.isoformat(),
            "endsAt": (starts_at + timedelta(hours=1)).isoformat(),
        },
    )
    assert scheduled.status_code == 201, scheduled.text
    event = json.loads(queue.get_nowait())
    assert (event["type"], event["meetingId"]) == ("meeting_pending", scheduled.json()["id"])
    assert event["companyName"] == "ООО «Технологии»"


async def test_a_candidate_application_appears_for_the_company(client: AsyncClient) -> None:
    """An application stays on «Я понравился» even when the company already liked someone else."""
    employer = await employer_with_company(client, "hr-apply@fsp.ru")
    _other, other_id = await candidate_with_resume(client, "other-apply@fsp.ru")
    applicant, applicant_id = await candidate_with_resume(client, "applicant@fsp.ru")
    vacancy = await client.post(f"{API}/vacancies", headers=bearer(employer), json=VACANCY)
    assert vacancy.status_code == 201, vacancy.text
    vacancy_id = vacancy.json()["id"]

    liked_someone_else = await client.put(
        f"{API}/candidates/{other_id}/reaction",
        headers=bearer(employer),
        json={"kind": "like"},
    )
    assert liked_someone_else.status_code == 200, liked_someone_else.text

    me = (await client.get(f"{API}/users/me", headers=bearer(employer))).json()
    hub = client._transport.app.state.notifications  # type: ignore[attr-defined]
    queue = hub.subscribe(uuid.UUID(me["id"]))

    applied = await client.put(
        f"{API}/vacancies/{vacancy_id}/reaction",
        headers=bearer(applicant),
        json={"kind": "like"},
    )
    assert applied.status_code == 200, applied.text

    event = json.loads(queue.get_nowait())
    assert (event["type"], event["candidateId"], event["vacancyTitle"]) == (
        "candidate_applied",
        applicant_id,
        VACANCY["title"],
    )
    assert event["displayName"] == "Иван Иванов"

    inbound = (await client.get(f"{API}/responses/inbound", headers=bearer(employer))).json()
    assert [item["candidateId"] for item in inbound] == [applicant_id]
    assert inbound[0]["vacancyTitle"] == VACANCY["title"]
    assert inbound[0]["displayName"]

    answered = await client.post(
        f"{API}/responses/inbound/candidates/{applicant_id}/respond",
        headers=bearer(employer),
        params={"vacancyId": vacancy_id},
    )
    assert answered.status_code == 204, answered.text
    assert (await client.get(f"{API}/responses/inbound", headers=bearer(employer))).json() == []
