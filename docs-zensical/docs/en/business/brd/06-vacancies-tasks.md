---
icon: lucide/list-todo
---

# Vacancies, mutual interest, and take-homes

An employer publishes a vacancy. A candidate likes it or skips it. A take-home is a separate assignment. External applications are screened by the ATS layer and are not written into the bank.

## FR-К-26. Vacancy feed

**Priority:** extra · К6 · **UC:** UC-К-20

The candidate sees published vacancies. Salary, format, city, and stack filters narrow the feed. There is a search box: a saved search reminds them about new vacancies.

**UI strings:** «Сбросить фильтры».

## FR-К-27. Candidate swipes

**Priority:** extra · К6 · **UC:** UC-К-19

One vacancy card. Right means interested, left means skip.

## FR-К-28. Mutual interest

**Priority:** extra · К1 · **UC:** UC-Р-10

Interest is mutual when the company marked the candidate and the candidate answered, or the candidate marked a vacancy and the company answered. Then a chat opens. There is no separate «Откликнуться» application with a cover letter: the `/applications` route does not work.

**UI strings:** «Взаимно».

## FR-Р-09. Publishing a vacancy

**Priority:** extra · К6 · **UC:** UC-Р-09

The employer creates a vacancy with a title, a description, a band, a format, and a city. A draft is not in the feed. Publishing shows it to candidates. Taking it down removes it from the feed.

**UI strings:** «Опубликовать».

## FR-К-29. A take-home for the candidate

**Priority:** extra · К6 · **UC:** UC-К-18

A company sends a test. The candidate takes it or refuses. A refusal and the result do not change the platform grade.

**UI strings:** «Начать».

## FR-Р-10. An employer's take-home

**Priority:** extra · К6 · **UC:** UC-Р-12

The employer builds an assignment from their tasks and sends it to a candidate. The result is that attempt's score. It does not change the platform category.

**UI strings:** «Отправить тестовое».

## FR-Р-11. Polling an external ATS

**Priority:** extra · К6 · **UC:** UC-Р-13

The employer connects an ATS and polls it. Applications are screened with the platform's filters: required skills, the salary band, and the city. The card shows a score, a decision, and reasons. A tag, a note, and the score are written back to the ATS. These people do not become KADRY users and do not appear in the bank.

The provider now is `ATS_MODE=mock`. A live vendor is one more adapter.

**UI strings:** «Подключить демо», «Опросить».
