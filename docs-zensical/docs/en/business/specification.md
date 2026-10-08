---
icon: lucide/clipboard-list
---

# Business specification

## Purpose

This document fixes the goals and the edges of KADRY. Screen behaviour and rules live in the [BRD](brd/index.md). If the texts disagree, the BRD wins.

## Goals

| ID | Goal | How to tell it worked |
|----|------|------------------------|
| G1 | The employer finds a category and reaches a person | Need → shortlist with reasons → invitation with a salary band → acceptance → contacts and chat |
| G2 | The category does not come from the resume | Survey, grade choice, and a test. Refusing the test leaves «Не подтверждён» and a low rank |
| G3 | The test is comparable and resists leaks | Patterns, variants, calibration, a one-prompt check, alerts |
| G4 | Contacts and the salary band are clear to both sides | An from–to band before the chat. Contacts only after acceptance or an application |
| G5 | Personal data under 152-FZ | Consent before save, storage in Russia, deletion within 30 days |

## In MVP scope

- Email registration, a 24-hour link, a password after confirmation, recovery that does not reveal whether the address exists
- 2FA required for the employer and the administrator, optional for the candidate
- Resume by form or PDF, several resumes, a PDF profile
- Survey, 11 grades, a proctored test and an AI interview, accepting the grade, a cooldown before the next change
- Need, recommended categories, shortlist, bank, employer swipes, invitation, including one without a vacancy
- Privacy, search pause, consents, FSP link, including an empty history
- Admin: patterns, calibration, one-shot, in-platform leak alerts, proctoring, dictionaries, parameters, K1/K2 dashboard, audit log, ban list

## Extra

Marked **extra** on the requirements. It can be shown beside the demo. It is not on the mandatory MVP path.

- Publishing vacancies, the candidate feed and applications, mutual match
- Meeting calendar, employer take-homes, recurring tasks
- Reports, the fake-vacancy rule, hire confirmation, monitoring of open sources
- Yandex ID, Keycloak as production sign-in, mobile layout from 360 px, ATS as a manual file export
- Candidate cabinet counters for 30 days

## Out of scope

| Item | Why |
|------|-----|
| Gosuslugi, Mos.ru, Nalog.ru | A later option, not in the hackathon (FR-О-03) |
| GDPR | Users in the EU are not the target |
| In-product video | A meeting stores a link to an external call |
| Company verification as a mandatory brief item | Not required in the MVP; partial protection is signals and the ban list |
| Employer take-homes changing the grade | Only an accepted grade test changes the grade |

## End-to-end demo

Six steps from the [demo flow](../user-flows/demo.md): candidate registration, survey and test, category, employer search, contact, then a classic application shown separately. Beside that: how a test is assembled, and a shortlist with filters and versions.

## Platform acceptance

- [ ] A new candidate: «Я ищу работу» → email and consent → password from the link → resume → test → «Принять грейд» → «Приглашения».
- [ ] An employer: 2FA → company profile → need with a salary band → shortlist with 2–3 reasons → invitation.
- [ ] Before the invitation is accepted, contacts are absent from the card and from the employer PDF.
- [ ] Unconfirmed people rank below confirmed ones. «Только подтверждённые» is on by default.
- [ ] No FSP history means no bonus and no penalty, with the neutral label «Нет данных ФСП».
- [ ] Someone else's object is a 403 without extra detail.
