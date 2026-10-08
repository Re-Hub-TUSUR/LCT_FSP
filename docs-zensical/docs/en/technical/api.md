---
icon: lucide/cable
---

# API

Prefix `/api/v1`. The router is assembled in `backend/app/api/router.py`. OpenAPI is `/api/docs`.

| Module | Prefix | What it does now |
|--------|--------|------------------|
| health | `/health` | Liveness and readiness |
| auth | `/auth` | Register, sign-in, email confirmation code, resend, refresh, logout |
| users | `/users` | `/users/me` |
| categories | `/categories` | Category dictionary |
| candidates | `/candidates` | Search, own resume, a second resume, photo, PDF, FSP link and sync |
| fsp-id | `/fsp-id` | Start of OIDC + PKCE sign-in |
| companies | `/companies` | Own profile, logo, public page, the company's task bank |
| test-assignments | `/companies/me/test-assignments` | Send a take-home, answers, manual review |
| vacancies | `/vacancies` | List, feed, own, card, reactions. Create and update are `501` |
| invitations | `/invitations` | Every operation is `501` |
| applications | `/applications` | Create and list are `501` |
| matching | `/matching` | Need and recommendations are `501` |
| responses | `/responses` | Incoming likes and a like back |
| calendar | `/calendar` | Meetings in a range, create, move, cancel, confirm |
| conversations | `/conversations` | Chats and attachments |
| notifications | `/notifications` | Event feed |
| assessments | `/assessments` | Categories, templates, attempts, code run, finish, interview, incoming take-homes. The survey `/survey` is `501` |
| admin | `/admin` | Users, plus the `app/admin` package: bank, analytics, employers, ban list, settings, verification |
| ats | `/ats` | ATS connection, poll, external applications and the decision. Does not change the candidate bank |

The FSP ID and registry emulation (`/mock/...`) is mounted only when `FSP_ID_MODE=mock`.

List pagination is `page` and `perPage`. The role is read from the database, not only from the token.
