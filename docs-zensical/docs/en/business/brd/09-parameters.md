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

Proctoring pauses, one-prompt weights, application caps, and recurring-task limits are not set in the product: those flows do not exist.
