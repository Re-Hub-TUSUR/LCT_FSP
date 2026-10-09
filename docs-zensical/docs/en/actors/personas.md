---
icon: lucide/users
---

# Actors and personas

Roles follow [FR-О-03](../business/brd/01-auth.md): one account, one role. An administrator does not read chats.

## Map

| Actor | Channel | Main screen |
|-------|---------|-------------|
| Candidate | Cabinet | Resume, test, invitations |
| Employer | Cabinet | Swipes and the feed |
| Administrator | Admin | Task bank |
| Email | A message with a code | Sign-up confirmation |
| FSP ID | Profile link | Does not replace sign-up by email |

## Candidate

Wants employers to find them by a confirmed grade, not by a lucky sentence in the resume.

| Area | What they do |
|------|----------------|
| Start | Email, password, and consent, then a code from the email |
| Resume | A form or a file. A second resume is another profession |
| Test | A grade choice, tasks, and written questions when the code works |
| Invitations | «Принять» or «Отклонить». Acceptance opens contacts and the chat |
| Settings | «Не ищу работу», the FSP link |

## Employer

Wants to find a person in the bank and invite them with a clear band.

| Area | What they do |
|------|----------------|
| Start | Email, password, company profile |
| Search | A feed with filters and swipes «Интересно» / «Пропустить» |
| Contact | An invitation with a band. Contacts appear after the candidate answers |
| Extra | A vacancy, a meeting, a take-home, an ATS poll |

Without a filled company profile the invitation does not go out.

## Administrator

One role for the task bank, analytics, company checks, the ban list, dictionaries, parameters, and the journal. Entry is the browser window on the `admin` subdomain. A second factor is not required.
