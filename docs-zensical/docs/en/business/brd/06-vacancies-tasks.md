---
icon: lucide/list-todo
---

# Vacancies, applications, and tasks

The extra path: publishing, the candidate feed, take-homes, recurring tasks, and closing a need.

## FR-К-26. Recurring tasks

**Priority:** extra · K6 · **UC:** UC-К-31, UC-К-32, UC-Р-35

Once every F_регуляр a candidate with a category receives one task from the pool of employers in their specialization and grade ±1 sub-level. The task is the same for everyone. There is no correct answer and no verdict. The answer is text up to 5000 characters and one link or a file up to 10 MB. Suggested time is T_регуляр. Skipping has no penalty. The author sees the answer, and so does any employer on the card if the candidate allowed it.

**UI strings:** «Отправить решение», «Пропустить».

## FR-К-27. Employer take-home

**Priority:** extra · K6 · **UC:** UC-К-30, UC-Р-32

It arrives only in an open chat. It must be started within 7 days, with a limit of 90 minutes. At most L_тестовых are active at once. A refusal and an expiry do not affect ranking or the grade. Statuses: «Отправлено», «Начато», «Сдано», «Отклонено», «Истекло».

## FR-К-28. Profile freshness

**Priority:** extra · K6 · **UC:** UC-К-31, UC-Р-17

The date of the latest of: a counted test attempt, a submitted recurring task, a submitted take-home. The employer sees «Активен: N дней назад». It affects position only through freshness in FR-Р-06 and does not change the grade.

## FR-К-29. Vacancy feed without search

**Priority:** extra · K6 · **UC:** UC-К-33, UC-К-34

There is no search box. The feed shows published vacancies whose specialization matches a resume and whose grade range covers the candidate's grade (confirmed, or claimed if there is no test) within ±1 sub-level. Order: stack, band versus expected salary, freshness. Filters for salary from, format, city, stack, and industry narrow the feed and do not change the order. Modes: «Карточки» and «Список».

## FR-К-30. Candidate swipes

**Priority:** extra · K6 · **UC:** UC-К-33

One card. Right applies. Left skips. «Отмена» is available for 5 seconds. Skipped vacancies are kept for 30 days and can still be applied to.

## FR-К-31. Application

**Priority:** extra · K6 · **UC:** UC-К-35, UC-К-36

An application contains a resume and an optional cover note up to 1000 characters, and reveals contacts to the vacancy's author. One application per vacancy. It can be withdrawn before «Принято». At most L_откликов per day. No reply within T_ответ sets «Истекло».

**UI strings:** «Откликнуться», «Отозвать».

## FR-К-32. Mutual match

**Priority:** extra · K1 · **UC:** UC-Р-30

A match is an application to a vacancy and the employer's favourite on that vacancy, in either order. The application becomes «Принято», both sides receive «Взаимный интерес», and a chat opens.

## FR-Р-19. Publishing a vacancy

**Priority:** extra · K6 · **UC:** UC-Р-27, UC-Р-28

A need with every required field can be published. The vacancy appears in feeds within 1 minute. Changing the band or the grade notifies people who applied. Unpublishing removes it from feeds; active applications stay.

**UI strings:** «Опубликовать потребность», «Снять с публикации».

## FR-Р-20. Working with applications

**Priority:** extra · K6 · **UC:** UC-Р-29

Applications are ranked by FR-Р-05 and FR-Р-06 and include reasons. Opening one sets «Просмотрено». «Принять» opens the chat. «Отклонить» requires a reason from the same dictionary the candidate uses.

## FR-Р-21. Employer take-home

**Priority:** extra · K6 · **UC:** UC-Р-32, UC-Р-33

Built from the pattern bank the same way as a grade test: specialization, grade, and required skills, with a unique variant. The employer adds up to 1000 characters of context and does not change the load-bearing elements. Up to 90 minutes. Only in an open chat. The result is an autocheck or rubric score, time, and the solution. It does not affect the grade.

## FR-Р-22. Recurring tasks from an employer

**Priority:** extra · K6 · **UC:** UC-Р-34, UC-Р-35

A task has a title, a statement up to 3000 characters, a specialization, a grade range, and a time up to T_регуляр. A correct answer is not required and is not stored. A company has at most L_задач active tasks. Answers are shown on cards under FR-К-33. From there the author can be invited or favourited.

**UI strings:** «Создать задачу».

## FR-Р-23. Closing a need

**Priority:** extra · K6 · **UC:** UC-Р-36, UC-Р-37

The outcome is one of four: «Наняли через платформу» (a candidate from an open chat), «Наняли вне платформы», «Найм отменён», «Не нашли». Closing sets active invitations to «Отозвано» with the reason «Позиция закрыта» and unpublishes the vacancy. A hire through the platform counts under FR-О-15.

**UI strings:** «Закрыть потребность».

## FR-Р-24. Fake-vacancy rule

**Priority:** extra · K6 · **UC:** UC-А-15

Counted closings are those with at least one accepted invitation or application. When there are at least M_мин_закрытий such closings and the share with a confirmed hire is below N_фикт, the company becomes «Под подозрением» and goes to an administrator. There is no automatic ban. The employer does not see this status. «Наняли вне платформы» is shown to the administrator on its own line.

## FR-Р-25. ATS integration

**Priority:** extra · K6 · **UC:** UC-Р-39

For a candidate whose contacts are revealed, the employer exports a contact card: PDF, contacts, need, band, status, and status history. Hire statuses can come back from the ATS. In the hackathon this is a description plus a manual file export.

**UI strings:** «Выгрузить в ATS».
