---
icon: lucide/search
---

# Bank, swipes, and an invitation

An employer looks for people in the bank and in swipes, then sends an invitation. There is no separate «need» and no saved versions of a shortlist.

## FR-Р-01. Company profile

**Priority:** MVP · К1 · **UC:** UC-Р-01

The company name and the company details are required. Without them an invitation does not go out: the system answers «Сначала заполните профиль компании». A logo is optional.

**UI strings:** «Сохранить».

## FR-Р-02. Candidate bank

**Priority:** MVP · К1 · **UC:** UC-Р-03

The feed shows published profiles that are not paused. Filters narrow it: specialization, grade, city, format, stack. There is no search by email. External ATS applications do not enter this feed.

**UI strings:** «Сбросить фильтры».

## FR-Р-03. Card before contact

**Priority:** MVP · К1 · **UC:** UC-Р-04

The card shows what FR-К-06 allows, plus why the person is in the feed: the test grade and the FSP line when there is one. There are no contacts until the invitation is accepted.

**UI strings:** «Пригласить».

## FR-Р-04. Employer swipes

**Priority:** MVP · К1 · **UC:** UC-Р-02

One card. Right is «Интересно», left is «Пропустить». The ← and → keys do the same. A skipped person does not leave the bank forever: it is a decision on the current deck.

**UI strings:** «Интересно», «Пропустить».

## FR-Р-05. What an invitation contains

**Priority:** MVP · К1 · **UC:** UC-Р-05

The text, the «от–до» band, and a contact method are required. A vacancy is optional: an invitation can go without one. The company is taken from the employer's profile.

**UI strings:** «Отправить приглашение».

## FR-Р-06. An invitation without a vacancy

**Priority:** MVP · К1 · **UC:** UC-Р-06

A published vacancy is not required. An invitation from the bank or from swipes goes to the person directly and does not appear in the vacancy feed.

## FR-Р-07. One open invitation

**Priority:** MVP · К6 · **UC:** UC-Р-07

While the candidate has not answered, the same company does not send them a second invitation. There is no daily cap and no pause after a decline.

## FR-Р-08. Invitation list

**Priority:** MVP · К1 · **UC:** UC-Р-08

The employer sees sent invitations and their status: «Отправлено», «Принято», «Отклонено». A sent invitation cannot be withdrawn.

**UI strings:** «Открыть чат».
