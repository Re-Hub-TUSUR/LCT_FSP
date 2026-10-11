---
icon: lucide/sliders-horizontal
---

# Parameters

Values the code reads. An administrator can change some of them on «Параметры» (FR-А-07). The start value is what the API settings use until a parameter is overridden.

| Parameter | What it sets | Start |
|-----------|----------------|-------|
| Password length | Minimum characters at sign-up | 8 |
| Refresh lifetime | How long a session lives without a new sign-in | 30 days |
| `assessment_retry_days` | Pause after an attempt that did not confirm the grade | 7 days |
| `assessment_grade_change_days` | Pause before changing an already confirmed grade | 90 days |
| `assessment_recommend_score` | Score that opens the next grade | 85 out of 100 |
| `interview_minutes` | Time for the written answers | 15 minutes |
| `interview_pass_score` | Mean answer score that confirms the grade | 60 out of 100 |
| Chat attachment | Maximum file size | 10 MB |
| `reaction_flap_min` | Mark changes on one candidate within 10 minutes before the company is under suspicion | 5 |
| `requisites_churn_min` | Requisite changes within a day | 5 |
| `junk_vacancy_min` | Vacancies without words within a day | 2 |
| `meeting_cancel_min` | Meeting cancellations within a day | 5 |
| `chat_media_min` | Employer files in chat within an hour | 10 |
| `invalid_industry_min` | Attempts to name an industry outside the list | 1 |

Proctoring pauses, one-prompt weights, application caps, and recurring-task limits are not set in the product: those flows do not exist.
