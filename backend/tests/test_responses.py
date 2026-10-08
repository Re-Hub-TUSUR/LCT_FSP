"""«Я понравился»: answering an incoming like makes the interest mutual and opens the chat."""

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
