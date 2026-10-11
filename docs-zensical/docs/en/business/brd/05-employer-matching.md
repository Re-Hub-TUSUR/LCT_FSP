---
icon: lucide/search
---

# Bank, swipes, and an invitation

An employer looks for people in the bank and in swipes, then sends an invitation. There is no separate «need» and no saved versions of a shortlist.

## FR-Р-01. Company profile

**Priority:** MVP · К1 · **UC:** UC-Р-01

The company name and the company details are required. Without them an invitation does not go out: the system answers «Сначала заполните профиль компании». The industry is chosen from the list: «Финтех», «E-commerce», «Телеком», «Госсектор», «Образование», «Медицина», «Игровая индустрия», «Промышленность». Otherwise the system answers «Выберите направление из списка». A logo is optional.

**UI strings:** «Сохранить», «Выберите направление», «Выберите направление из списка».

## FR-Р-02. Candidate bank

**Priority:** MVP · К1 · **UC:** UC-Р-03

The feed shows published profiles that are not paused. Filters narrow it: specialization, grade, city, format, stack. A city matches the place from the directory, not the spelling. There is no search by email. External ATS applications do not enter this feed. The feed has no «Отобрано», «Взаимно», or «Не интересно» tabs: those lists live on «Мои отклики».

The default mode is «Свободный поиск»: the feed is not tied to a vacancy. When the company has vacancies, the page dims and a note titled «Выберите вакансию» opens to the right of the mode switch. The switch itself stays sharp. «Понял» hides it until the tab is closed: a new tab shows it again. «Больше не показывать» remembers that the note is finished and does not show it again in this browser.

**UI strings:** «Сбросить фильтры», «Свободный поиск», «Выберите вакансию», «Понял», «Больше не показывать».

## FR-Р-03. Card before contact

**Priority:** MVP · К1 · **UC:** UC-Р-04

The card shows what FR-К-06 allows, plus why the person is in the feed: the test grade and the FSP line when there is one. There are no contacts until the invitation is accepted.

On the feed row and in the side panel, specialization and grade are not repeated as a separate chip: they are already in the job title. The test status is words only («Тест пройден»), without an «N/100» score. The «Сила профиля» scale is not shown in these two places; «Под вакансию» stays.

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

The employer sees sent invitations on the cabinet page «Обзор» and their status: «Отправлено», «Принято», «Отклонено». The cabinet menu has no separate «Приглашения» section. A sent invitation cannot be withdrawn.

**UI strings:** «Открыть чат».
