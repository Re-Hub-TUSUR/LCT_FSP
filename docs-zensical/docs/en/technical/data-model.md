---
icon: lucide/database
---

# Data model

The ORM is in `backend/app/models`. Identifiers of user entities are UUIDs. Admin tables are described in `docs/ADMIN.md` and live in `app/admin/models.py`: analytics snapshots, task meta, the audit log, parameters, dictionaries, employer cases, the ban list, company verification.

## Accounts

| Entity | Why it exists |
|--------|----------------|
| `User` | Email, password hash, role `candidate` / `employer` / `admin` |
| `EmailVerificationCode` | The email confirmation code |
| `RefreshToken` | Session renewal |

There is no 2FA table in the models.

## People and companies

| Entity | Why it exists |
|--------|----------------|
| `CandidateProfile` | Resume, contacts, feed preferences, search status |
| `CandidateCategory` | A category per specialization, cooldown, attempt history next to the test |
| `Company` | The employer profile |
| `FspAchievement`, `FspSportTitle` | Results and titles from the registry |

Grades in code (`Grade`): intern, junior, middle, senior, lead. The eleven sub-levels with «−» and «+» are not in the enum.

## Matching and conversation

| Entity | Why it exists |
|--------|----------------|
| `Vacancy` | A vacancy, including the salary band |
| `Invitation` | An invitation. Statuses: sent, viewed, accepted, declined. «Отозвано» and «Истекло» are not in the enum |
| `VacancyReaction`, `CandidateReaction` | Like and skip for swipes |
| `Conversation`, `Message`, `MessageAttachment` | Chat and files |
| `Meeting` | A meeting. Statuses: pending, confirmed, and the neighbours in `MeetingStatus` |

## Assessment

| Entity | Why it exists |
|--------|----------------|
| `AssessmentTask` | A quiz, code, or open answer. The owner is the platform or a company |
| `AssessmentTest` | A template: a sample or a fixed list |
| `AssessmentAttempt`, `AssessmentAnswer`, `AssessmentTaskTime` | The attempt, answers, and time |
| `TestAssignment` | A take-home a company sent to a candidate |

The attempt status `interview` is written questions about the code, not a screen recording. There are no proctoring tables: the product does not keep them.

There is no need entity, no shortlist versions, and no one-off offer. Search hangs off the bank, vacancies, and reactions.

## ATS

Tables `ats_connections`, `ats_jobs`, `ats_candidates`, `ats_applications`, `ats_raw_events`, `screening_jobs`, `screening_results`, `ats_sync_log`. These are external applications, not platform profiles.
