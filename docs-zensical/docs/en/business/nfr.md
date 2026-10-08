---
icon: lucide/gauge
---

# Non-functional requirements

Each requirement is measurable. Priority follows the source label.

## Security and 152-FZ

**NFR-01. Consent before processing.** MVP · K4. No profile field is saved before the consent checkbox. The text opens before the checkbox. Each consent stores version, date, and time. A lawyer checks the texts before launch.

**NFR-02. Storage in Russia.** MVP · K4. Personal data sits on servers in Russia.

**NFR-03. Deletion term.** MVP · K4. After withdrawal of processing consent or account deletion, data is deleted or anonymised within 30 days. Analytics after that is anonymised only.

**NFR-04. Passwords and links.** MVP · K4. A password is at least 10 characters, with letters and digits. It is not stored in the clear and nobody, including an administrator, can read it. The email confirmation link lasts 24 hours, the password-reset link 1 hour, both single-use.

**NFR-05. Sessions.** MVP · K4. A candidate or employer session ends after 7 days idle and never lives longer than 30 days. An administrator session lasts 12 hours. Five wrong passwords lock sign-in for 15 minutes. A password change ends every session. Traffic uses a protected connection.

**NFR-06. Authorization checks.** MVP · K4. Rights are checked on 100% of pages and actions by role and owner, whatever the interface showed. Before a release an automated check of other people's objects from each role must succeed 0 times.

**NFR-07. FSP ID compatibility.** Extra · K4. Sign-in is built on OpenID Connect, which Keycloak supports. An existing account is linked by a confirmed email, without recreating it.

## Speed and reliability

**NFR-08.** MVP · K4. At 50 concurrent users, for 95% of requests: a shortlist of up to 200 people within 3 s, a filter within 1 s, a card within 1.5 s, the bank within 2 s, other pages within 1 s.

**NFR-09.** MVP · K4. 50 concurrent users, 10 of them in a proctored test, error responses at most 1%.

**NFR-10.** MVP · K4. 99% availability in a month. No planned work on demo days.

**NFR-11.** Extra · K4. A copy once a day, kept 14 days. Restore within 4 hours, data loss at most 24 hours.

**NFR-12.** MVP · K1. A status change is visible to the other side within 5 seconds. A cabinet notification within 5 seconds, an email within 2 minutes.

## Interface

**NFR-13.** MVP · K4. The last 2 versions of Chrome, Yandex Browser, Firefox, Edge, and Safari on a computer, from 1280×720. The grade test runs where screen share works: Chrome, Yandex Browser, Edge, Firefox.

**NFR-14.** Extra · K6. Every page except the grade test and admin works from 360 px without horizontal scroll. Swipes are a gesture.

**NFR-15.** MVP · K3. Body text contrast at least 4.5:1, large text and controls at least 3:1. Body font at least 14 px. Every action, including swipes, works from the keyboard, and focus is visible. A status is never colour alone.

**NFR-16.** MVP · K3. In an unguided hallway test at least 4 of 5 candidates reach the start of the test from registration within 10 minutes, and at least 4 of 5 employers send a first invitation from registration within 10 minutes.

**NFR-17.** MVP · K3. The interface is Russian. Amounts look like «250 000 ₽», dates are DD.MM.YYYY, time is in the user's zone, Moscow by default. Status names match in both cabinets.

## Audit log and mechanic quality

**NFR-18.** MVP · K4. FR-А-22 events are kept for 1 year. Email is masked (`iv***@mail.ru`). Passwords and codes are never written.

**NFR-19. Consistency.** MVP · K2. At least 80% of repeated runs of reference personas yield the same grade ±1 sub-level, at least 60% the exact same grade.

**NFR-20. Discrimination.** MVP · K2. For at least 80% of active variants the solve-rate gap between the top and bottom third is at least 0.3.

**NFR-21. Equivalence.** MVP · K2. Inside a pattern a variant's solve rate differs from the mean by at most 10 percentage points, and difficulty by at most 1 sub-level.

**NFR-22. Match to the reference.** MVP · K2. The grade matches the expert label ±1 sub-level in at least 80% of cases, and the level in at least 90%.

**NFR-23. Categorization correctness.** MVP · K2. 100% of candidates with a counted attempt receive a category under FR-К-16 through FR-К-18. Specialization matches the reference for at least 95% of personas.

**NFR-24. Shortlist relevance.** MVP · K1. On reference pairs the share of relevant people in the top 10 is at least 0.7. At least 90% of needs have at least 1 relevant person in the top 3.

**NFR-25. One-prompt resistance.** MVP · K2. At most 30% of active variants are marked «Только с интервью».

## By role

**NFR-К-01.** MVP · K4. Recordings without flags are deleted after 30 days. With flags, 30 days after the decision, or 30 days after an appeal decision. Recordings are not used to identify a person or to train models. This is said before the test starts.

**NFR-К-02.** MVP · K4. Only administrators watch recordings. Every view is logged. There is no download.

**NFR-К-03.** MVP · K2. A failure loses at most 10 seconds of input. After a reload the attempt is restored within 5 seconds.

**NFR-К-04.** MVP · K2. Up to 5 minutes of pause in total and up to 3 drops, without losing answers.

**NFR-К-05.** MVP · K2. The next AI line starts within 3 seconds after the answer. Russian speech with IT terms is at least 90% of words correct on a set of 30 recordings.

**NFR-К-06.** MVP · K3. The survey is up to 5 minutes. The test with the interview is at most 90 minutes; the exact time is T_тест.

**NFR-К-07.** MVP · K5. A PDF is recognised within 30 seconds. On 50 resumes at least 85% of fields are correct, name and email at least 95%.

**NFR-К-08.** MVP · K5. A PDF profile is ready within 10 seconds and is at most 1 MB.

**NFR-Р-01.** MVP · K3. Filters, mode, and position restore within 1 card. Shortlist versions are kept 90 days after the need closes.

**NFR-Р-02.** Extra · K6. A take-home is assembled into a preview within 60 seconds.

**NFR-А-01.** MVP · K2. The dashboard recomputes once a day and on a button. 10 000 attempts take at most 10 minutes.

**NFR-А-02.** MVP · K2. 50 variants finish calibration and the one-shot check within 30 minutes.

**NFR-А-03.** MVP · K2. «Утёк» stops being issued within 1 minute. Search monitoring, when connected, checks 100% of active patterns every 24 hours.

**NFR-А-04.** MVP · K2. A proctoring recording starts within 3 seconds. A jump to an event takes 1 second.
