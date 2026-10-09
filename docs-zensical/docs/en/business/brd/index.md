---
icon: lucide/file-text
---

# Business Requirements Document (BRD)

The requirements describe the current product: what the screens and the API do. New behavior is written here in the same change as the feature.

## How to read an identifier

| Prefix | Domain |
|--------|--------|
| FR-О | Rules shared by more than one role |
| FR-К | Candidate |
| FR-Р | Employer |
| FR-А | Administrator |
| UC-* | A scenario, see [use cases](../../use-cases/index.md) |
| NFR-* | A measurable limit |
| П-* | A screen on the [page map](../../product/pages.md) |

## Product language

The interface is Russian. Both locales of this documentation quote buttons and statuses in Russian, as on the screen: «Принять», «Отправить ответы», «Опросить».

## Chapters

| # | Chapter | Contents |
|---|---------|----------|
| 1 | [Sign-in](01-auth.md) | Email, code, roles, ban list |
| 2 | [Candidate profile](02-candidate-profile.md) | Resume, PDF, privacy, FSP |
| 3 | [Assessment](03-assessment.md) | Grade, test, written interview, category |
| 4 | [Invitations and chat](04-invitations-chat.md) | Salary band, contacts, chat, meetings |
| 5 | [Search](05-employer-matching.md) | Bank, swipes, invitation |
| 6 | [Vacancies and tasks](06-vacancies-tasks.md) | Publishing, mutual interest, take-homes, ATS |
| 7 | [Administrator](07-admin.md) | Task bank, analytics, ban list, journal |
| 8 | [User data](08-user-data.md) | What is known about a person |
| 9 | [Parameters](09-parameters.md) | Values the code reads |

Nearby: [NFR](../nfr.md), [coverage](../coverage.md), [specification](../specification.md).
