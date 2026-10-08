---
icon: lucide/table
---

# What we know about a user

For whoever builds ranking. «Confirmed» means the value came from a check, not from the person's own words. Until there are real users, the data is synthetic.

## Candidate

| Field | Source | Confirmed? | Example |
|-------|--------|------------|---------|
| Email | Registration | Yes, by letter | ivanov@mail.ru |
| Name, phone, city, format | Resume | No | Kazan, hybrid |
| Expected salary from | Resume, optional | No | 220 000 ₽ net |
| Specialization | Resume and survey | Yes, once a test on it is counted | Backend |
| Stack | Resume, PDF, survey | No | Python, PostgreSQL |
| Skills and a score for each | Test | Yes | Python — 9 of 10 |
| Experience, roles, soft skills, industries, jobs | Resume or survey | No | 4 years, fintech |
| Resume grade and claimed grade | PDF, form, choice before the test | No | Middle, Middle+ |
| Confirmed grade and category | An accepted test | Yes | Backend · Middle |
| Confirmation status | System | Yes | Подтверждён, Не подтверждён, Результат на проверке |
| Test score and interview score | Test | Yes | 74 of 100, interview 68 |
| FSP link and results | FSP registry | Yes, by the registry | ID 104582, 2nd place |
| No FSP history | Registry or no link | Yes | Нет данных ФСП |
| Recurring-task answers | Candidate | No verdict | 3 answers in 60 days |
| Employer take-homes | Autocheck or rubric | Yes, as a task score | 81 of 100 |
| Freshness | Latest event | Yes | Active 5 days ago |
| Privacy and search pause | Candidate | Yes, their choice | Не ищу работу |
| Consents | Candidate, version and date | Yes | Publication, version 1.2 |

## Employer

| Field | Source | Confirmed? | Example |
|-------|--------|------------|---------|
| Email | Registration | Yes, by letter | hr@company.ru |
| Name, industry, description, city, site, contact method | Profile | No, no verification in the MVP | ООО «Технологии» |
| Need: specialization, grades, skills, team, band | Form | No | Backend, Middle–Middle+ |
| Whether the need is published | Employer's action | Yes | Vacancy |
| Closing count and hire share | Closing and the candidate's reply | Partial: a hire through the platform is confirmed by the candidate | 12 closed, 5 hired |
| Reports | Candidates | No, until an administrator decides | 2 in 30 days |
| Company status | Administrator and FR-Р-24 | Yes | Активен |

## Events we record

Registration (role, date, method). Survey (answers and time). Test attempt (grade, patterns, scores, interview, total, status). Proctoring flags. A shortlist impression (position, reasons, score, version). A card view. Swipes on both sides. Filters. A need change. Invitation and application with statuses. A match. Chat: open date, message counts, time to first reply — **not the text**. A meeting. A take-home. A recurring task. A hire. A report.

## What ranking does not use

Name, photo, contacts, sex and age (we do not collect them), chat text, proctoring recordings. The resume grade and the claimed grade do not enter ranking (FR-К-03). City and format are filters only, not parts of the score.
