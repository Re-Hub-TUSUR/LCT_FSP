---
icon: lucide/user
---

# Candidate scenarios

Normative text: [profile](../business/brd/02-candidate-profile.md), [test](../business/brd/03-assessment.md), [invitations](../business/brd/04-invitations-chat.md), [vacancies](../business/brd/06-vacancies-tasks.md).

## UC-К-01 Start

**As** a candidate, **I want** to see 3 steps (resume, test, FSP), **so that** I press «Создать резюме» on the first unfinished one. П-К-01.

## UC-К-02 Upload a PDF

**As** a candidate, **I want** to attach a PDF, **so that** within 30 seconds the form fills in and highlights uncertain fields. Nothing is saved until I confirm. A scan, a file over 5 MB, or more than 10 pages leads to the manual form. FR-К-02.

## UC-К-03 Fill the form

**As** a candidate, **I want** to fill the form and press «Сохранить резюме», **so that** the resume is saved. An empty required field blocks save. Leaving the page keeps a draft. FR-К-01.

## UC-К-04 Another resume

**As** a candidate, **I want** to press «Создайте ещё одно резюме», **so that** an empty form opens. A taken specialization is an error. At N_резюме the banner hides. FR-К-04.

## UC-К-05 Employer's view

**As** a candidate, **I want** to switch «До раскрытия контактов» and «После», **so that** I see both versions and download a PDF. FR-К-05.

## UC-К-06 Start the test

**As** a candidate, **I want** to press «Начать тест», **so that** the survey opens. FR-К-07.

## UC-К-07 Refuse the test

**As** a candidate, **I want** to press «Не сейчас», **so that** after the low-rank warning the status becomes «Не подтверждён» and «Приглашения» shows «Пройти тест». FR-К-07.

## UC-К-08 Survey

**As** a candidate, **I want** to answer about industries, specialization, stack, experience, and roles, **so that** each answer is saved immediately. If I stop, I continue from the same question. FR-К-08.

## UC-К-09 Choose a grade

**As** a candidate, **I want** to pick 1 of 11 grades, **so that** I see the description and the duration. The resume grade is already selected with «из резюме». FR-К-09.

## UC-К-10 Permissions

**As** a candidate, **I want** to allow the camera, microphone, full screen, and recording consent, **so that** 3 checks turn green and «Начать тест» enables. A browser tab instead of the screen is requested again. FR-К-12.

## UC-К-11 Test from a phone

**As** a candidate on a phone, **I want** to press «Отправить ссылку на почту», **so that** I continue on a computer. The survey and grade chosen on the phone are kept. FR-К-13.

## UC-К-12 Solve a task

**As** a candidate, **I want** to submit a solution, **so that** the AI interview starts and the next task gets harder or easier. FR-К-10, FR-К-11.

## UC-К-13 Dropped connection

**As** a candidate, **I want** to return by the same link, **so that** the attempt continues with the timer paused. More than 5 minutes of pause in total sets «Прервана». FR-К-15.

## UC-К-14 Stopped screen share

**As** a candidate, **I want** to press «Возобновить трансляцию», **so that** the pause lifts. After 60 seconds the attempt is «Прервана». FR-К-12.

## UC-К-15 Answer the AI

**As** a candidate, **I want** to answer 2–3 questions by voice, **so that** the system transcribes the answer and moves on. Thirty seconds of silence repeats the question, then scores 0. FR-К-14.

## UC-К-16 Accept the grade

**As** a candidate, **I want** to press «Принять грейд», **so that** a category appears and «Приглашения» opens. FR-К-18.

## UC-К-17 Result below the claim

**As** a candidate, **I want** to press «Не принимать», **so that** I stay «Не подтверждён» and see the date of the next attempt. FR-К-17.

## UC-К-18 Test one level down

**As** a candidate, **I want** to press «Пройти тест на уровень ниже», **so that** I take it without a pause until N_первичных is used up. Junior− has no lower level. FR-К-17.

## UC-К-19 Test one level up

**As** a candidate, **I want** to press «Пройти тест на уровень выше» or «Позже», **so that** I try the next level. The current grade stays if the new one is not confirmed. The offer lasts 7 days. FR-К-17.

## UC-К-20 Result under review

**As** a candidate, **I want** to see «Результат на проверке, решение до <дата>», **so that** I wait for a notification. FR-К-18, FR-К-21.

## UC-К-21 History

**As** a candidate, **I want** to open «Категория и грейд», **so that** I see a category per resume and the attempt history without task texts. FR-К-20.

## UC-К-22 Change grade

**As** a candidate, **I want** to pick a target grade and press «Пройти тест на другой грейд», **so that** I go through the survey and the test again. Until T_кулдаун ends the button stays inactive. FR-К-19.

## UC-К-23 Test for the next resume

**As** a candidate, **I want** to press «Пройти тест» on a resume without a category, **so that** the test uses that specialization. FR-К-04.

## UC-К-24 Incoming invitations

**As** a candidate, **I want** to see invitations, newest first, **so that** I open the right one. No category shows «Пройти тест». No invitations show three tips. FR-К-23.

## UC-К-25 Accept

**As** a candidate, **I want** to press «Принять» after the contact warning, **so that** the status becomes «Принято» and the chat opens. FR-К-25, FR-О-08.

## UC-К-26 Decline

**As** a candidate, **I want** to press «Отклонить» and optionally pick a reason, **so that** the employer sees «Отклонено». FR-К-25.

## UC-К-27 Report an invitation

**As** a candidate, **I want** to press «Пожаловаться», **so that** the report dialog opens and the signal counts for the company. FR-О-12.

## UC-К-28 Dead invitation

**As** a candidate, **I want** to open an expired or withdrawn invitation, **so that** I see the terms and have no «Принять» button. FR-К-24.

## UC-К-29 Answer a meeting

**As** a candidate, **I want** to press «Подтвердить» or «Попросить перенос» with three slots, **so that** the status changes for both sides. FR-О-10. Extra.

## UC-К-30 Take-home

**As** a candidate, **I want** to press «Начать», **so that** a timer of up to 90 minutes runs and the answer saves every 10 seconds. «Отказаться» does not affect rank. Not started in 7 days — «Истекло». FR-К-27. Extra.

## UC-К-31 Recurring task

**As** a candidate, **I want** to submit a solution or an approach up to 5000 characters, **so that** freshness updates. There is no verdict. FR-К-26, FR-К-28. Extra.

## UC-К-32 Skip a task

**As** a candidate, **I want** to press «Пропустить», **so that** the task leaves with no penalty and the next date is shown. FR-К-26. Extra.

## UC-К-33 Vacancy swipes

**As** a candidate, **I want** to swipe right or left, **so that** I apply or move the vacancy to «Пропущенные». «Отмена» lasts 5 seconds. FR-К-30. Extra.

## UC-К-34 Feed filters

**As** a candidate, **I want** to set salary from, format, city, and stack, **so that** the feed narrows without changing order. Empty: «Сбросить фильтры». FR-К-29. Extra.

## UC-К-35 Apply

**As** a candidate, **I want** to pick a resume, optionally write a cover note, and press «Откликнуться», **so that** the status becomes «Отправлено» and the company sees contacts. A repeat on the same vacancy is unavailable. FR-К-31. Extra.

## UC-К-36 Application statuses

**As** a candidate, **I want** to see statuses and press «Отозвать» before «Принято», **so that** the application becomes «Отозвано». FR-К-31. Extra.

## UC-К-37 Confirm a hire

**As** a candidate, **I want** to press «Подтвердить» or «Это не так», **so that** the hire counts or stays unconfirmed. FR-О-15. Extra.

## UC-К-38 Visibility

**As** a candidate, **I want** to toggle name, photo, job, FSP, task answers, and per-skill result, **so that** I see a preview. FR-К-33.

## UC-К-39 Pause

**As** a candidate, **I want** to turn on «Не ищу работу», **so that** within a minute I leave shortlists and the bank. Active invitations stay. FR-К-34.

## UC-К-40 Withdraw publication

**As** a candidate, **I want** to withdraw publication consent, **so that** after a warning the profile hides within a minute. Open chats stay. FR-К-35.

## UC-К-41 Link FSP

**As** a candidate, **I want** to press «Связать с ФСП» and sign in with FSP ID, **so that** I see results and a visibility toggle. If the service is down: «Попробуйте позже». FR-К-36.

## UC-К-42 No history

**As** a candidate with no history, **I want** to see neutral text and a link to the competition calendar, **so that** an empty block does not look like a minus. FR-К-38.

## UC-К-43 Unlink

**As** a candidate, **I want** to press «Отвязать», **so that** results leave the profile and ranking within a minute. FR-К-36.

## UC-К-44 Turn on 2FA

**As** a candidate, **I want** to press «Включить 2FA», **so that** the second-factor page opens. FR-О-04.

## UC-К-45 Delete the account

**As** a candidate, **I want** to press «Удалить аккаунт» and enter the password, **so that** the profile hides immediately and data is deleted within NFR-03. Undo is possible for 7 days. FR-К-39.
