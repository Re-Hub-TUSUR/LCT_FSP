---
icon: lucide/messages-square
---

# Invitations, statuses, and chat

The shared status vocabulary, the salary band, contact reveal, chat, meetings, notifications, reports, and hire confirmation. Incoming candidate invitations live here too.

## FR-О-06. Shared statuses

**Priority:** MVP · K1 · **UC:** UC-К-24, UC-К-36, UC-Р-25, UC-Р-29

One vocabulary for invitations and applications in both cabinets: «Отправлено», «Просмотрено», «Принято», «Отклонено», «Отозвано», «Истекло». «Отправлено» becomes «Просмотрено» when the recipient opens the card, then «Принято» or «Отклонено». From «Отправлено» and «Просмотрено» the author can set «Отозвано», and silence longer than T_ответ sets «Истекло». The other statuses are final. Both sides see the same name and the same transition date.

## FR-О-07. Salary band

**Priority:** MVP · K1 · **UC:** UC-Р-05, UC-Р-21, UC-Р-23, UC-К-25

A band is required on a need, a vacancy, and an invitation: «от» and «до» in rubles, integers, «от» greater than 0, «до» at least «от» and at most «от» × K_вилка. The label «до вычета НДФЛ» or «на руки» is required. The candidate sees the band before the chat opens.

## FR-О-08. Revealing contacts

**Priority:** MVP · K1 · **UC:** UC-К-25, UC-К-35, UC-Р-17, UC-Р-19

Email, phone, and messenger links become visible to a company only after the candidate accepts its invitation or applies to its vacancy. Before that they are absent from the card, the PDF, and exports. Reveal applies only to that company. Before accepting, the candidate sees which contacts will open. Every view is written to the audit log.

## FR-О-09. Opening a chat

**Priority:** MVP · K1 · **UC:** UC-О-07, UC-К-25, UC-Р-29, UC-Р-30

A chat opens in three cases: the candidate accepted an invitation, the employer accepted an application, or there was a mutual match. One chat per candidate–need pair. A message is up to 4000 characters. Files: PDF, DOCX, PNG, JPG, ZIP, up to 10 MB. There is no video call. Thirty days after the need closes, the chat is read-only.

**UI strings:** «Отправить». Empty state for the candidate: «Чат откроется, когда вы примете приглашение». For the employer: «Чат откроется, когда кандидат примет приглашение».

## FR-О-10. Meetings

**Priority:** extra · K1 · **UC:** UC-О-08, UC-К-29, UC-Р-31

Only a recruiter schedules a meeting, and only from an open chat: date, time, duration 15–180 minutes, and a required link to an external call. Both calendars show «Назначена». The candidate sets «Подтверждена» or «Запрошен перенос» with a comment and up to 3 slots. The recruiter reschedules or sets «Отменена». After it ends the status is «Прошла». Reminders go out 24 hours and 15 minutes before.

**UI strings:** «Назначить встречу», «Подтвердить», «Попросить перенос».

## FR-О-11. Notifications

**Priority:** MVP · K3 · **UC:** UC-О-09

Channels: the cabinet feed and email. Events: a new invitation, a status change, a mutual match, a new message (email if unread for 10 minutes), a meeting, a take-home, a test result and a review decision, a hire request, an account restriction. Email can be turned off per type, except security and administrator decisions.

## FR-О-12. Reports

**Priority:** extra · K6 · **UC:** UC-О-12, UC-К-27, UC-А-18

A candidate reports an invitation, a vacancy, a recurring task, or a message. An employer reports a candidate's message. Reasons: «Фиктивная вакансия», «Зарплата не соответствует», «Просят оплату», «Спам», «Оскорбления», «Другое». The comment is up to 1000 characters. One report per user per object. The report goes to an administrator and counts in the company's signals.

**UI strings:** «Отправить жалобу», «Пожаловаться».

## FR-О-14. One primary action and empty states

**Priority:** MVP · K3 · **UC:** UC-К-01, UC-К-24, UC-Р-04, UC-Р-14

Each page has one accent button from the [page map](../../product/pages.md). An empty state explains why and contains the button for the next step. An error sits next to the field and says how to fix it. Onboarding shows the steps and one button to the first unfinished step.

## FR-О-15. Confirming a hire

**Priority:** extra · K6 · **UC:** UC-К-37, UC-Р-36

A hire counts only if the employer chose «Наняли через платформу» with a specific candidate and the candidate confirmed within T_подтверждение_найма. «Это не так» or silence yields «Не подтверждён». That closing counts as a closing without a confirmed hire.

**UI strings:** «Подтвердить», «Это не так».

## FR-К-23. Home screen «Приглашения»

**Priority:** MVP · K1 · **UC:** UC-К-24

A candidate who has a resume lands on «Приглашения» after sign-in. Unseen items first, then by date. A row shows company, title, band, format, date, and status. The menu shows an unseen counter. No category shows the banner «Пройти тест». No invitations show three tips with links: FSP, a recurring task, vacancies.

## FR-К-24. Invitation card

**Priority:** MVP · K1 · **UC:** UC-К-25, UC-К-28

Shows the description, band, company, format, city, contact method, the vacancy if the need is published, and the reply deadline. The first open sets «Просмотрено».

## FR-К-25. Accept and decline

**Priority:** MVP · K1 · **UC:** UC-К-25, UC-К-26, UC-К-28

«Принять» sets «Принято», reveals contacts, and opens the chat. «Отклонить» sets «Отклонено» with an optional reason: «Зарплата ниже ожиданий», «Не подходит стек», «Не подходит формат», «Не интересна компания», «Не ищу работу», «Подозрительное предложение». The employer sees the reason. An expired or withdrawn invitation cannot be accepted.
