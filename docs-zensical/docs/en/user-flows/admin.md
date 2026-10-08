---
icon: lucide/route
---

# Administrator path

Normative text: [admin](../business/brd/07-admin.md).

## Pattern life cycle

1. Sign-in → 2FA → «Дашборд валидации».
2. «Создать паттерн»: specialization, level, skill, load-bearing elements, variables, how it is checked → «Черновик».
3. «Сгенерировать варианты» → calibration → rejection → one-prompt check → the mark «Только с интервью» → «Активировать» → «Активен».
4. A leak alert or a search hit → «Подтвердить утечку» → «Утёк», new attempts do not receive the pattern → affected attempts enter the queue → the pattern is replaced.
5. «Эталонные наборы» → «Пересчитать метрики» → the dashboard.

## Proctoring

The queue from oldest to newest → a recording with marks and the transcript → «Нарушения нет», «Нарушение подтверждено», or «Нужна повторная попытка» → a notification to the candidate.

## Fake vacancies

«Работодатели под подозрением» → signals → «Снять подозрение», «Предупредить», «Ограничить», or «Заблокировать». A ban writes a row to the ban list.

## Branches

No calibration or one-shot check — «Активировать» stays unavailable. A median pass rate at or above P_one_shot_паттерн returns the pattern to «Черновик». Fewer than 2 active patterns for a skill and a step — a warning. Unused variants below 20% — «Заканчиваются варианты». After N_эмп attempts, difficulty is computed from real solutions.

## Failures

A parameter outside its range does not save. A dictionary value already in use can only be archived. An administrator cannot ban themselves or remove the last administrator.
