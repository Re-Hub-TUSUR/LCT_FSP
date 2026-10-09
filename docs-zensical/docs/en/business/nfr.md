---
icon: lucide/gauge
---

# Non-functional requirements

What can be checked on the current product.

## Security

**NFR-01. Consent before the account.** Sign-up does not create an account without the consent mark.

**NFR-02. Password.** At least 8 characters. Stored only as a hash. The password does not enter the journal or API responses.

**NFR-03. Session.** Sign-in issues an access token and a refresh token. Logout revokes the refresh token. Each refresh replaces the previous one. The refresh lifetime is 30 days by default.

**NFR-04. Rights.** An action checks the role and the owner on the server. Someone else's object is unavailable to a candidate and an employer.

## Speed and interface

**NFR-05. Live event.** A like and a new message reach the open tab as a stream, without reloading the list.

**NFR-06. Narrow screen.** The feed, swipes, and application cards stay readable from 360 px: the meter moves under the name instead of being cut off.

**NFR-07. Russian interface.** Buttons and statuses are Russian. Amounts are in rubles. In both documentation locales the button strings stay Russian.

## Test and resume

**NFR-К-01. Draft.** Leaving the test page sends the unsaved answer. The loss is the last request that did not land, not the whole attempt.

**NFR-К-02. Interview time.** Written answers have a time limit. The start value is 15 minutes (`interview_minutes`).

**NFR-К-03. Resume parsing.** PDF and DOCX are read when a model key is set. Without the key the form is filled by hand, and the upload does not fail silently.

## Admin

**NFR-08. Journal.** A parameter change and a block are written with the author and the reason. A password does not enter the journal. The journal exports to CSV.
