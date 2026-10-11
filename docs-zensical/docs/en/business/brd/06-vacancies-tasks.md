---
icon: lucide/list-todo
---

# Vacancies, mutual interest, and take-homes

An employer publishes a vacancy. A candidate likes it or skips it. A take-home is a separate assignment. External applications are screened by the ATS layer and are not written into the bank.

## FR-К-26. Vacancy feed

**Priority:** extra · К6 · **UC:** UC-К-20

The candidate sees published vacancies. Salary, format, city, and stack filters narrow the feed. There is a search box: a saved search reminds them about new vacancies. The feed has no «Отобрано», «Взаимно», or «Не интересно» tabs: those lists live on «Мои отклики» — «Мне понравились», «Взаимно», «Не понравились».

**UI strings:** «Сбросить фильтры», «Мои отклики», «Взаимно».

## FR-К-27. Candidate swipes

**Priority:** extra · К6 · **UC:** UC-К-19

One vacancy card. Right means interested, left means skip.

## FR-К-28. Mutual interest

**Priority:** extra · К1 · **UC:** UC-Р-10

Interest is mutual when the company marked the candidate and the candidate answered, or the candidate marked a vacancy and the company answered. Then a chat opens. Until the company presses «Ответить», the specialist's application («Откликнуться») is on the company's «Мои отклики» → «Я понравился». If that section is already open, the card appears without a reload. There is no separate application with a cover letter: the `/applications` route does not work.

**UI strings:** «Взаимно», «Я понравился», «Ответить», «Откликнуться».

## FR-Р-09. Publishing a vacancy

**Priority:** extra · К6 · **UC:** UC-Р-09

The employer creates a vacancy with a title, a description, a band, a format, and a city. The title and the description have to contain words, otherwise the system answers «Опишите вакансию словами». For office and hybrid work the city is chosen from the list of populated places. A draft is not in the feed. Publishing shows it to candidates. Taking it down removes it from the feed.

**UI strings:** «Опубликовать», «Опишите вакансию словами», «Укажите город для офиса или гибрида».

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
