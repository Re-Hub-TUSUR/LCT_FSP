---
icon: lucide/git-compare
---

# Implementation status

A cut of the code at the time of writing. «Done» means the scenario exists in routes and models. «Partial» means neighbouring behaviour exists, but not the BRD rule. «Absent» means the route is a `501` stub or the entity was not found. What was not checked is marked as such.

The BRD does not change because of this page.

| BRD domain | Fact in the code |
|------------|------------------|
| Email registration, FR-О-01 | Partial. Register, sign-in, a 6-digit code (not a 24-hour link), refresh, and logout exist. Password recovery is not in `auth.py` |
| Minimum fields, FR-О-02 | Partial. Roles are split across `/auth/candidate` and `/auth/employer`. The password is set at registration, not after the letter |
| Yandex ID and Gosuslugi, FR-О-03 | Absent. FSP ID only links a profile |
| 2FA, FR-О-04 | Absent. No second-factor table or routes were found |
| Roles and 403, FR-О-05 | Done at the level of `require_roles` and owner checks. The automated «0 foreign successes» run was not executed in this cut |
| Account ban, FR-О-13 | Partial. The admin ban list is described in `docs/ADMIN.md` (companies, tax ids, email, domains). The candidate screen with a reason and a term was not compared line by line |
| Resume and PDF, FR-К-01, FR-К-02 | Done: own resume, a second resume, PDF upload through RouterAI when the key is set |
| 11 grades and a category, FR-К-09, FR-К-18 | Partial. `Grade` has five values: intern, junior, middle, senior, lead. `CandidateCategory` and attempts exist |
| Survey, FR-К-08 | Absent. `POST /assessments/survey` returns `501` |
| Test, code, interview, FR-К-10, FR-К-14 | Partial. Attempts, code run, finish, and the `interview` status exist. Camera and screen proctoring were not found in the models |
| Cooldown and history, FR-К-19, FR-К-20 | Partial. `GET /assessments/me` returns categories, pauses, and attempt history. The set of 11 grades does not match the BRD |
| Privacy and pause, FR-К-33, FR-К-34 | Partial. The search status `not_looking` exists. The full set of visibility toggles was not compared line by line |
| FSP, FR-К-36, FR-К-38 | Done in mock mode: authorize, callback, sync, unlink. An empty registry is not an error |
| Account deletion, FR-К-39 | Not found in the auth and candidates routes |
| Statuses and band, FR-О-06, FR-О-07 | Partial. A vacancy band is validated. An invitation has no «Отозвано» or «Истекло». The invitation routes themselves are `501` |
| Contact reveal, FR-О-08 | Partial. The candidate card cuts fields by backend rules. An audit row for every contact view was not confirmed in this cut |
| Chat, FR-О-09 | Done: `conversations` and attachments. The rule «one chat per need» is not confirmed: there is no need entity |
| Meetings, FR-О-10 | Done: calendar, schedule, move, confirm. This is extra in the BRD |
| Notifications, FR-О-11 | Partial. The `/notifications` route exists. Email per event type was not compared |
| Need and shortlist, FR-Р-02 through FR-Р-09 | Absent. `matching` create need and recommendations are `501`. Shortlist versions are not in the models |
| Bank and employer swipes, FR-Р-10, FR-Р-12 | Partial. Candidate search and reactions exist. That is not a shortlist for a need |
| Invitation, FR-Р-14, FR-Р-15 | Absent. Every `/invitations` method is `501`. There is no one-off offer |
| Vacancies and applications, FR-Р-19, FR-К-31 | Partial. The feed and reactions exist. Creating and editing a vacancy is `501`. Applications `/applications` are `501`. Mutual interest goes through `/responses` |
| Take-homes, FR-Р-21 | Done as company assignments and a candidate taking them. Assembly from patterns with load-bearing elements is absent |
| Admin patterns and validation, FR-А-02 through FR-А-22 | Partial. The `app/admin` package: task bank, analytics on a button, parameters, dictionaries, audit log, ban list, company verification. LLM-persona calibration, one-shot, a proctoring queue, and K1/K2 reference runs were not found in the routes |

Where this page says «not compared» or «not found», that is the edge of this cut, not proof that the behaviour is absent from every frontend file.
