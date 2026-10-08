---
icon: lucide/list-checks
---

# Brief coverage

«Out of scope» means the item is deliberately not built for the hackathon. The normative text is the [BRD](brd/index.md). This page is a self-check of the specification, not a code status. Code is in [implementation status](../technical/implementation-status.md).

## Product essence

| Item | Requirements | Status |
|------|----------------|--------|
| The employer finds a category and reaches a candidate | FR-Р-03, FR-Р-04, FR-Р-12, FR-Р-14, FR-К-23 | MVP |
| The category comes from the survey, the grade, and the test, not the resume | FR-К-03, FR-К-08, FR-К-09, FR-К-10, FR-К-18 | MVP |
| Rank inside a category by profile strength and FSP | FR-Р-06, FR-К-37 | MVP |
| The test resists leaks and stays comparable | FR-А-02, FR-А-04, FR-А-05, FR-К-11, FR-А-08 | MVP |
| Several vacancy descriptions show how tasks are assembled | FR-А-21, FR-Р-18, FR-Р-21 | MVP, take-home is extra |
| The grade is not lowered by itself; a lower or higher test; a time limit | FR-К-17, FR-К-19 | MVP |
| Short recurring tasks | FR-К-26, FR-Р-22, FR-К-28 | Extra |
| An invitation path that is not an application | FR-Р-04 through FR-Р-17 | MVP |
| FSP ID link, empty history; Keycloak | FR-К-36, FR-К-37, FR-К-38, NFR-07 | MVP, Keycloak is extra |
| Synthetic data and our own validation | FR-А-18, FR-А-19, FR-А-20, NFR-19 through NFR-24 | MVP |
| Fake-vacancy protection, ATS | FR-Р-24, FR-А-13, FR-Р-25 | Extra, ATS is a concept |

## Minimum functionality

Candidate: resume and PDF, test and category, invitations, privacy, consents, FSP — MVP. Recurring tasks, the vacancy feed, and applications — extra. They see only their own objects (FR-О-05).

Employer: profile, need, shortlist with reasons, bank, invitation without a mandatory vacancy, hidden contacts — MVP. Publishing and applications — extra.

The from–to band, invitation contents, shared statuses, and email registration — MVP. Company verification as a mandatory brief step is out of MVP scope; partial protection is FR-А-13 and FR-О-12. 152-FZ, roles, and passwords — MVP. Keycloak — extra. Desktop — MVP, mobile from 360 px — extra. Tens of users — MVP.

## End-to-end scenario

Steps 1–5 (registration, test, category, search, contact) are MVP. The classic application is extra. A separate showing of the test and of matching is MVP. The steps are in the [demo](../user-flows/demo.md).

## Team ideas and decisions

Email is MVP, Yandex is extra, Gosuslugi is out of scope. Employer swipes are MVP, candidate swipes are extra. Calendar, take-homes, fake vacancies, and ATS are extra. 2FA, 11 grades, four specializations, one administrator role, the «Приглашения» home screen, and an empty FSP history with no penalty are MVP. GDPR is out of scope. In-product video is out of scope; a meeting stores an external link.

## Must be shown

Pattern bank, calibration, one-shot, leak alerts, proctoring queue, dictionaries, parameters, K1/K2 dashboard, audit log — MVP. Open-source monitoring and reports — extra. The ban list is MVP, the suspicious-employer review is extra. One primary action per page, an empty state that points forward, the same status names, and 2–3 reasons on each person in the shortlist.

## Gaps the specification already closed

1. An invitation without a vacancy is tied to a one-off offer (FR-Р-15).
2. Proctoring retention is NFR-К-01 and NFR-К-02.
3. A dropped connection is FR-К-15, NFR-К-03, and NFR-К-04.
4. An application with no reply becomes «Истекло» (FR-К-31).
5. Deleting an account with active invitations is FR-К-39.
