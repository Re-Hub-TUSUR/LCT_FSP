"""Invitations: a company offers a job, the candidate answers, an acceptance opens the contacts."""

from typing import Any

from httpx import AsyncClient

from tests.conftest import API, bearer, register_and_login
from tests.test_cabinet import COMPANY, RESUME
from tests.test_vacancies import VACANCY

OFFER: dict[str, Any] = {
    "message": "Предлагаем позицию backend-разработчика в команде платежей",
    "salary": {"from": 200_000, "to": 300_000},
    "contactMethod": "@hr_payments",
}


async def employer_with_company(client: AsyncClient, email: str, inn: str = COMPANY["inn"]) -> str:
    token = await register_and_login(client, email, role="employer")
    saved = await client.put(
        f"{API}/companies/me", headers=bearer(token), json={**COMPANY, "inn": inn}
    )
    assert saved.status_code == 200, saved.text
    return token


async def candidate_with_resume(client: AsyncClient, email: str) -> tuple[str, str]:
    token = await register_and_login(client, email)
    saved = await client.patch(f"{API}/candidates/me", headers=bearer(token), json=RESUME)
    assert saved.status_code == 200, saved.text
    return token, saved.json()["id"]


async def test_invitation_is_sent_listed_and_accepted(client: AsyncClient) -> None:
    employer = await employer_with_company(client, "hr@fsp.ru")
    candidate, candidate_id = await candidate_with_resume(client, "dev@fsp.ru")

    # Nothing yet: empty lists, not errors.
    for path, token in (("incoming", candidate), ("outgoing", employer)):
        empty = await client.get(f"{API}/invitations/{path}", headers=bearer(token))
        assert (empty.status_code, empty.json()["total"]) == (200, 0)

    hidden = await client.get(f"{API}/candidates/{candidate_id}", headers=bearer(employer))
    assert hidden.json()["contacts"] is None

    sent = await client.post(
        f"{API}/invitations", headers=bearer(employer), json={**OFFER, "candidateId": candidate_id}
    )
    assert sent.status_code == 201, sent.text
    invitation = sent.json()
    assert (invitation["status"], invitation["company"]["name"]) == ("sent", COMPANY["name"])
    assert invitation["salary"] == OFFER["salary"]
    # No vacancy was named: nothing to show instead of a title.
    assert (invitation["vacancyId"], invitation["vacancyTitle"]) == (None, None)

    twice = await client.post(
        f"{API}/invitations", headers=bearer(employer), json={**OFFER, "candidateId": candidate_id}
    )
    assert twice.status_code == 409

    incoming = await client.get(f"{API}/invitations/incoming", headers=bearer(candidate))
    outgoing = await client.get(f"{API}/invitations/outgoing", headers=bearer(employer))
    assert [item["id"] for item in incoming.json()["items"]] == [invitation["id"]]
    assert [item["id"] for item in outgoing.json()["items"]] == [invitation["id"]]

    accepted = await client.post(
        f"{API}/invitations/{invitation['id']}/accept", headers=bearer(candidate)
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted"

    # The answer is final, and it opens the candidate's contacts to the company.
    again = await client.post(
        f"{API}/invitations/{invitation['id']}/decline", headers=bearer(candidate)
    )
    assert again.status_code == 409
    opened = await client.get(f"{API}/candidates/{candidate_id}", headers=bearer(employer))
    assert opened.json()["contacts"]["email"] == "dev@fsp.ru"

    # A new invitation is possible once the previous one is answered.
    next_one = await client.post(
        f"{API}/invitations", headers=bearer(employer), json={**OFFER, "candidateId": candidate_id}
    )
    assert next_one.status_code == 201
    declined = await client.post(
        f"{API}/invitations/{next_one.json()['id']}/decline", headers=bearer(candidate)
    )
    assert declined.json()["status"] == "declined"


async def test_invitation_names_the_vacancy_it_was_sent_for(client: AsyncClient) -> None:
    employer = await employer_with_company(client, "hr-vacancy@fsp.ru")
    candidate, candidate_id = await candidate_with_resume(client, "dev-vacancy@fsp.ru")
    vacancy = await client.post(f"{API}/vacancies", headers=bearer(employer), json=VACANCY)
    assert vacancy.status_code == 201, vacancy.text
    vacancy_id = vacancy.json()["id"]

    sent = await client.post(
        f"{API}/invitations",
        headers=bearer(employer),
        json={**OFFER, "candidateId": candidate_id, "vacancyId": vacancy_id},
    )
    assert sent.status_code == 201, sent.text
    assert (sent.json()["vacancyId"], sent.json()["vacancyTitle"]) == (
        vacancy_id,
        VACANCY["title"],
    )

    # The join survives a list, not just the single row `create` and `accept` return.
    incoming = (await client.get(f"{API}/invitations/incoming", headers=bearer(candidate))).json()
    outgoing = (await client.get(f"{API}/invitations/outgoing", headers=bearer(employer))).json()
    assert incoming["items"][0]["vacancyTitle"] == VACANCY["title"]
    assert outgoing["items"][0]["vacancyTitle"] == VACANCY["title"]

    accepted = await client.post(
        f"{API}/invitations/{sent.json()['id']}/accept", headers=bearer(candidate)
    )
    assert accepted.json()["vacancyTitle"] == VACANCY["title"]


async def test_invitation_belongs_to_its_company_and_its_candidate(client: AsyncClient) -> None:
    employer = await employer_with_company(client, "hr-own@fsp.ru")
    stranger = await employer_with_company(client, "hr-other@fsp.ru", inn="500100732259")
    no_company = await register_and_login(client, "hr-empty@fsp.ru", role="employer")
    candidate, candidate_id = await candidate_with_resume(client, "dev-own@fsp.ru")
    other, _ = await candidate_with_resume(client, "dev-other@fsp.ru")
    offer = {**OFFER, "candidateId": candidate_id}

    assert (
        await client.post(f"{API}/invitations", headers=bearer(no_company), json=offer)
    ).status_code == 409
    assert (
        await client.post(f"{API}/invitations", headers=bearer(candidate), json=offer)
    ).status_code == 403
    unknown = {**OFFER, "candidateId": "00000000-0000-0000-0000-000000000001"}
    assert (
        await client.post(f"{API}/invitations", headers=bearer(employer), json=unknown)
    ).status_code == 404

    sent = await client.post(f"{API}/invitations", headers=bearer(employer), json=offer)
    invitation_id = sent.json()["id"]

    foreign_list = await client.get(f"{API}/invitations/outgoing", headers=bearer(stranger))
    assert foreign_list.json()["total"] == 0
    foreign_answer = await client.post(
        f"{API}/invitations/{invitation_id}/accept", headers=bearer(other)
    )
    assert foreign_answer.status_code == 404
