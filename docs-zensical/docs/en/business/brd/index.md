---
icon: lucide/file-text
---

# Business Requirements Document (BRD)

Normative requirements for the target behaviour of KADRY. This is the source for product, design, and engineering. The current code is described separately in [implementation status](../../technical/implementation-status.md) and does not cancel a requirement.

## How to read an identifier

| Prefix | Domain |
|--------|--------|
| FR-О | Rules shared by more than one role |
| FR-К | Candidate |
| FR-Р | Employer |
| FR-А | Administrator |
| UC-* | A scenario on one page, see [use cases](../../use-cases/index.md) |
| NFR-* | A measurable non-functional requirement |
| П-* | A screen on the [page map](../../product/pages.md) |
| T_ P_ N_ L_ W_ K_ F_ R_ Δ_ | An administrator parameter. Starting values are in [chapter 09](09-parameters.md) |

**Priority** comes from the source label: **MVP** is needed for the demo, **extra** is additional scope. Criterion marks K1–K6 stay next to the priority.

## Product language

The interface is Russian. In both locales of this documentation, buttons and statuses are quoted in Russian, as on screen: «Принять», «Не подтверждён», «Отправить приглашение».

## Chapters

| # | Chapter | Contents |
|---|---------|----------|
| 1 | [Authentication](01-auth.md) | Email, password, 2FA, roles, lockout |
| 2 | [Candidate profile](02-candidate-profile.md) | Resume, PDF, privacy, FSP, deletion |
| 3 | [Assessment](03-assessment.md) | Survey, grade, proctoring, interview, category |
| 4 | [Invitations and chat](04-invitations-chat.md) | Statuses, salary band, contacts, chat, meetings, reports |
| 5 | [Matching](05-employer-matching.md) | Need, shortlist, bank, invitation |
| 6 | [Vacancies and tasks](06-vacancies-tasks.md) | Publishing, applications, take-homes, recurring tasks, closing |
| 7 | [Admin](07-admin.md) | Patterns, leaks, proctoring, validation, audit log |
| 8 | [User data](08-user-data.md) | What is known about a person, and what is not used for ranking |
| 9 | [Parameters](09-parameters.md) | Starting values and open questions |

Also: [NFR](../nfr.md), [brief coverage](../coverage.md), [specification](../specification.md).
