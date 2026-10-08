---
icon: lucide/users
---

# Actors and personas

Roles follow [FR-О-05](../business/brd/01-auth.md): one account, one role. An administrator does not read chats except for a fragment attached to a report.

## Map

| Actor | Channel | Home screen |
|-------|---------|-------------|
| Candidate | Cabinet | «Приглашения» |
| Employer | Cabinet | «Потребности» |
| Administrator | Admin | «Дашборд валидации» |
| Email | Letters | Confirmation and notifications |
| FSP ID | External sign-in used only to link | Does not replace email registration |

## Candidate

Wants employers to find them by a confirmed grade, not by a well-phrased resume.

| Area | What they do |
|------|----------------|
| Start | Email and consent, then a password from the link in the letter |
| Resume | A form or a PDF. Up to N_резюме resumes, each with its own specialization |
| Test | Survey, grade choice, camera, microphone, full screen, then tasks and a voice AI interview |
| Invitations | Accept, decline, or report. Accepting opens contacts and the chat |
| Settings | What is visible before contacts are revealed, the «Не ищу работу» pause, the FSP link, account deletion |

2FA is optional for a candidate.

## Employer

Wants to describe a role in a few steps and invite a person with a clear reason they are on the shortlist.

| Area | What they do |
|------|----------------|
| Start | Email, password, mandatory 2FA, company profile |
| Need | Role, grades, stack, team, salary band. Until it is published, candidates do not see it |
| Shortlist | Categories, list or cards, favourites and hidden people for this need |
| Contact | An invitation with a salary band. Contacts appear after the candidate responds |
| Extra | Publish a vacancy, a meeting, a take-home, a recurring task, close the need |

Invitations stay unavailable until the company profile is filled in.

## Administrator

One role with every admin right. Only another administrator can add one. 2FA is mandatory. The last administrator cannot be removed, and an administrator cannot ban themselves.

| Area | What they do |
|------|----------------|
| Tasks | Pattern, variants, LLM-persona calibration, one-prompt check, leaks |
| Proctoring | Queue of flagged attempts, a decision within T_проверки |
| People and companies | Reports, suspicious employers, ban list |
| Settings | Dictionaries, parameters, audit log, reference sets, K1 and K2 metrics |
