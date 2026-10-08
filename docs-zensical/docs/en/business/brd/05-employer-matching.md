---
icon: lucide/search
---

# Need, shortlist, and invitation

How an employer describes a role, gets people with reasons, and sends an invitation. Screens: П-Р-01 through П-Р-10.

## FR-Р-01. Company profile

**Priority:** MVP · K1 · **UC:** UC-Р-02, UC-Р-03

Required: name, an industry from the dictionary, a description of 100–3000 characters, city, a contact method, a site. Optional: logo and size. Without a profile, invitations and publishing are unavailable. Edits apply only to new invitations.

**UI strings:** «Сохранить».

## FR-Р-02. Describing a need

**Priority:** MVP · K1 · **UC:** UC-Р-05, UC-Р-06

Required: role, specialization, a grade range from the 11, required skills (1–10), what the team does (at least 100 characters), a band under FR-О-07, format, city. Optional: desired skills (up to 10), industry, tasks for the first 3 months. A need is private until it is published. Statuses: «Черновик», «Активна», «Закрыта», plus the flag «Опубликована как вакансия».

**UI strings:** «Показать подборку», «Описать потребность».

## FR-Р-03. Recommended categories

**Priority:** MVP · K1 · **UC:** UC-Р-08

Exact categories are the need's specialization and each grade in the range. Neighbours are one sub-level past each edge. Each shows the count of confirmed people and a sentence, for example «Senior− — на 1 подуровень выше вашего диапазона, 12 кандидатов». Turning a category on or off rebuilds the shortlist.

## FR-Р-04. Building the shortlist

**Priority:** MVP · K1 · **UC:** UC-Р-05, UC-Р-09

Only the selected categories, with publication consent and without a search pause. The category comes from the test, not the resume. Up to 200 people, the first 50 immediately. People hidden for this need are not shown.

## FR-Р-05. Confirmed ranks above unconfirmed

**Priority:** MVP · K1 · **UC:** UC-Р-14, UC-Р-15

A confirmed grade always ranks above an unconfirmed one, regardless of the match score. «Только подтверждённые» is on by default. If it is turned off, unconfirmed people appear in a separate block below with the label «Не подтверждён».

## FR-Р-06. Match score

**Priority:** MVP · K1 · **UC:** UC-Р-09, UC-Р-15

Inside a block, sort by a 0–100 score of five weighted parts: category (1 inside the range, 0.6 for a neighbouring sub-level); share of required skills (tested skill counts as 1, resume-only as 0.5); test score; FSP score (0 with no history); freshness (1 within T_актуальность, linearly to 0 at 3 × T_актуальность). In the bank without a need, order inside a category comes from the test score, FSP, and freshness.

## FR-Р-07. Reasons

**Priority:** MVP · K1 · **UC:** UC-Р-09, UC-Р-29

In the shortlist, in applications, and on task answers, a person has 2–3 reasons: the factors with the largest contribution, in plain words and with numbers. Examples: «Грейд Middle+ подтверждён тестом: 84 из 100», «Стек совпадает: 4 из 5 обязательных, 3 проверены тестом». A missing required skill adds «Нет в профиле: Kafka».

## FR-Р-08. Filters do not rebuild the shortlist

**Priority:** MVP · K1 · **UC:** UC-Р-12

Filters: grade, category, skill, FSP results, confirmed only, freshness, city, format. A filter narrows the view and does not rebuild the shortlist. Reset restores it whole. Filters, mode, and position in «Карточки» persist across sessions.

**UI strings:** «Сбросить фильтры».

## FR-Р-09. Shortlist versions

**Priority:** MVP · K1 · **UC:** UC-Р-06, UC-Р-13

Each save of a changed need creates a version marked «добавлено N, убрано M». The last 10 are kept. Favourites, hidden people, and invitations belong to the need, not to a version.

## FR-Р-10. Candidate bank

**Priority:** MVP · K1 · **UC:** UC-Р-15, UC-Р-16

The whole base of people who consented to publication. Filters: specialization, grade, category, skill, FSP results, confirmed only (on by default). There is no search by name or contacts. Twenty people per page. From the bank a person can be favourited on any need or invited.

## FR-Р-11. Card before contact

**Priority:** MVP · K1 · **UC:** UC-Р-17, UC-Р-18

The FR-К-33 fields with privacy applied, reasons if the card was opened from a shortlist, history with this company, and the employer PDF. No contacts before reveal.

**UI strings:** «Пригласить», «Профиль недоступен».

## FR-Р-12. Employer swipes

**Priority:** MVP · K1 · **UC:** UC-Р-10, UC-Р-11

One card. Right adds the person to favourites for the current need. Left hides them for that need. «Отмена» is available for 5 seconds. A hidden person does not return in versions of this need, but stays visible on other needs and in the bank.

## FR-Р-13. Favourites and hidden

**Priority:** MVP · K1 · **UC:** UC-Р-11, UC-Р-18, UC-Р-20

Lists are per need. From favourites an invitation is two clicks: «Пригласить» and «Отправить приглашение» on a form filled from the need. Hidden people can be restored.

## FR-Р-14. What an invitation contains

**Priority:** MVP · K1 · **UC:** UC-Р-21, UC-Р-23

Required: title, description of 100–3000 characters, band, format, city, contact method. The company name is filled in. Fields from the need are filled in. Before sending, a preview shows what the candidate will see.

## FR-Р-15. Invitation without a vacancy

**Priority:** MVP · K1 · **UC:** UC-Р-22

A published vacancy is not required. An invitation from the bank without a need creates a one-off offer from the form and the candidate's category. It is not in the candidate feed, closes itself after 60 days without activity, supports favourites, does not take part in matches, and counts as a need in the fake-vacancy rule.

## FR-Р-16. Invitation limits

**Priority:** MVP · K6 · **UC:** UC-Р-24

One active invitation per candidate–need pair. After «Отклонено», a repeat on the same need waits T_повтор_приглашения. At most L_приглашений per day, and L_приглашений_огр while «Ограничен». The form shows when the limit resets.

## FR-Р-17. Statuses and withdrawal

**Priority:** MVP · K1 · **UC:** UC-Р-25, UC-Р-26

The list shows FR-О-06 statuses, dates, decline reasons, filters by need and status, and counters. «Отправлено» and «Просмотрено» can be withdrawn.

**UI strings:** «Открыть чат», «Отозвать».

## FR-Р-18. How candidates were checked

**Priority:** MVP · K2 · **UC:** UC-Р-07

The need has a block: skills, task types, and difficulty steps of the test for the recommended categories, and the share of coding tasks. Task texts and answers are not shown.
