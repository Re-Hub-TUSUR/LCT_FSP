---
icon: lucide/building-2
---

# Employer scenarios

Normative text: [matching](../business/brd/05-employer-matching.md), [vacancies](../business/brd/06-vacancies-tasks.md).

## UC-Р-01 Mandatory 2FA

**As** an employer, **I want** to press «Настроить 2FA», **so that** the cabinet does not open until the second factor is on. FR-О-04.

## UC-Р-02 First profile

**As** an employer, **I want** to fill the name, industry, description, and contact method, **so that** the system offers «Описать потребность». FR-Р-01.

## UC-Р-03 Edit the profile

**As** an employer, **I want** to press «Сохранить», **so that** changes apply only to new invitations. An empty contact method does not save. FR-Р-01.

## UC-Р-04 Need list

**As** an employer, **I want** to see counters for the shortlist, favourites, invited, and accepted, **so that** I open a shortlist. Empty: «Опишите, кого ищете». FR-О-14.

## UC-Р-05 New need

**As** an employer, **I want** to pass 3 steps and press «Показать подборку», **so that** the shortlist opens within 3 seconds. FR-Р-02, FR-Р-04.

## UC-Р-06 Change a need

**As** an employer, **I want** to change the stack or the grade, **so that** a new version appears with added and removed counts. FR-Р-09.

## UC-Р-07 How they were checked

**As** an employer, **I want** to open «Как проверяли кандидатов», **so that** I see skills and task types without the texts. FR-Р-18.

## UC-Р-08 Categories

**As** an employer, **I want** to see exact and neighbouring categories with the confirmed count, **so that** I know where to look. FR-Р-03.

## UC-Р-09 Reasons

**As** an employer, **I want** to read 2–3 reasons and a «what is missing» line, **so that** I choose people in the list. FR-Р-07.

## UC-Р-10 Swipes

**As** an employer, **I want** to swipe right or left, **so that** the person is favourited for this need or hidden. FR-Р-12.

## UC-Р-11 Undo

**As** an employer, **I want** to press «Отмена» within 5 seconds or restore someone from «Скрытые», **so that** they return to the previous place. FR-Р-12, FR-Р-13.

## UC-Р-12 Filters

**As** an employer, **I want** to narrow the view, **so that** the shortlist itself is not rebuilt and reset brings it back whole. Empty: «Сбросить фильтры». FR-Р-08.

## UC-Р-13 Previous version

**As** an employer, **I want** to pick a version, **so that** I see that shortlist. Favourites and invitations stay. FR-Р-09.

## UC-Р-14 Empty shortlist

**As** an employer, **I want** to see neighbouring categories and «Показать неподтверждённых», **so that** unconfirmed people appear in a block below. FR-Р-05.

## UC-Р-15 Bank

**As** an employer, **I want** to set specialization, grade, category, stack, and FSP, **so that** I see 20 people per page by profile strength. FR-Р-10.

## UC-Р-16 Nothing found

**As** an employer, **I want** to see which filter narrows the most, **so that** I remove it with one button. FR-Р-10.

## UC-Р-17 Card before contact

**As** an employer, **I want** to look at category, score, skills, stack, experience, and FSP, **so that** I judge the person without contacts and hidden fields. FR-Р-11.

## UC-Р-18 Favourite

**As** an employer, **I want** to press «В избранное» and pick a need, **so that** the person is added there. FR-Р-13.

## UC-Р-19 After contact

**As** an employer, **I want** to see contacts and the full PDF, **so that** the view is written to the log. FR-О-08.

## UC-Р-20 Invite from favourites

**As** an employer, **I want** to press «Пригласить», **so that** a form filled from the need opens. FR-Р-13.

## UC-Р-21 Send

**As** an employer, **I want** to check the fields, look at the preview, and press «Отправить приглашение», **so that** the status becomes «Отправлено». FR-Р-14.

## UC-Р-22 Without a need

**As** an employer from the bank, **I want** to fill the offer, salary, and contact method, **so that** the system creates a one-off offer. FR-Р-15.

## UC-Р-23 Band error

**As** an employer, **I want** the field to highlight, **so that** I cannot send an empty band or a «до» below «от». FR-О-07.

## UC-Р-24 Repeat and limit

**As** an employer, **I want** to see the previous invitation's status or when the limit resets, **so that** I understand why sending is unavailable. FR-Р-16.

## UC-Р-25 Statuses

**As** an employer, **I want** to filter by need and status, **so that** I see counters and decline reasons. FR-Р-17.

## UC-Р-26 Withdraw

**As** an employer, **I want** to press «Отозвать» on «Отправлено» or «Просмотрено», **so that** the candidate receives «Отозвано». FR-Р-17.

## UC-Р-27 Publish

**As** an employer, **I want** to press «Опубликовать потребность», **so that** within a minute the vacancy appears in feeds of matching categories. FR-Р-19. Extra.

## UC-Р-28 Unpublish

**As** an employer, **I want** to unpublish or change the band and grade, **so that** the feed updates and applicants learn about a band or grade change. FR-Р-19. Extra.

## UC-Р-29 Review applications

**As** an employer, **I want** to open an application, see contacts and reasons, and press «Принять» or «Отклонить», **so that** acceptance opens a chat. FR-Р-20. Extra.

## UC-Р-30 Match

**As** an employer, **I want** to see «Взаимный интерес», **so that** a chat opens without a separate accept when the person is already favourited on this vacancy. FR-К-32. Extra.

## UC-Р-31 Meeting

**As** an employer, **I want** to press «Назначить встречу» with a date, duration, and a link, **so that** the meeting appears for both. Without a link sending is unavailable. FR-О-10. Extra.

## UC-Р-32 Take-home

**As** an employer, **I want** to press «Отправить тестовое», **so that** I see a preview of the variant for the need. If the candidate already has 2 active, sending explains the refusal. FR-Р-21. Extra.

## UC-Р-33 Result

**As** an employer, **I want** to open the result, **so that** I see the score, time, and solution. FR-Р-21. Extra.

## UC-Р-34 New task

**As** an employer, **I want** to write a task and pick a specialization and grades, **so that** it enters the shared pool. FR-Р-22. Extra.

## UC-Р-35 Answers

**As** an employer, **I want** to read anonymised answers and press «Пригласить» or «В избранное». FR-Р-22. Extra.

## UC-Р-36 Hire through the platform

**As** an employer, **I want** to choose «Наняли через платформу» and a candidate from an open chat, **so that** active invitations withdraw and the candidate gets a request. FR-Р-23, FR-О-15. Extra.

## UC-Р-37 Close another way

**As** an employer, **I want** to choose «Наняли вне платформы», «Найм отменён», or «Не нашли», **so that** the need closes and invitations withdraw. FR-Р-23. Extra.

## UC-Р-38 Limit

**As** an employer, **I want** to read the reason and the new limit, **so that** I can write to support. FR-А-13. Extra.

## UC-Р-39 Export to ATS

**As** an employer, **I want** to press «Выгрузить в ATS» for a person whose contacts are revealed, **so that** the card is exported. Without contacts the button stays unavailable. FR-Р-25. Extra.
