---
icon: lucide/shield
---

# Administrator

The pattern bank, leaks, proctoring, employer protection, and K1/K2 validation. Screens: П-А-01 through П-А-17.

## Tasks

### FR-А-01. Administrator role

**Priority:** MVP · K4 · **UC:** UC-А-24

One role with every right. Only another administrator can add one. 2FA is required. The last administrator cannot be removed, and an administrator cannot ban themselves.

### FR-А-02. Pattern card

**Priority:** MVP · K2 · **UC:** UC-А-04

Fields: specialization, level and step, skill, format (code, open answer, case, survey), load-bearing elements, variables, how it is checked, interview prompts, time, source of the idea. LeetCode, Codeforces, and Coderun are only an idea: the pattern's text and data are original.

### FR-А-03. Pattern statuses

**Priority:** MVP · K2 · **UC:** UC-А-06

«Черновик» → «Калибровка» → «Активен» → «Отключён» or «Утёк». Only «Активен» enters tests. Activation requires calibration, the one-prompt check, and a median one-shot pass rate below P_one_shot_паттерн. Editing the load-bearing elements of an active pattern returns it to «Черновик».

**UI strings:** «Активировать», «Создать паттерн».

### FR-А-04. Generating variants

**Priority:** MVP · K2 · **UC:** UC-А-05

From 10 to 500 at a time. Only variables change. A coding variant has its own inputs and an answer checked by a reference solution. Duplicates are dropped. If unused variants fall below 20%, the alert is «Заканчиваются варианты».

### FR-А-05. Calibration on LLM personas

**Priority:** MVP · K2 · **UC:** UC-А-07, UC-А-08

A persona solves tasks at one sub-level. Each variant is solved by personas of its level and neighbouring levels, R_персон runs each. Estimated difficulty is the lowest sub-level whose personas reached a passing score in at least half the runs. The tolerance is 1 sub-level; otherwise the variant is rejected.

### FR-А-06. Difficulty from real solutions

**Priority:** MVP · K2 · **UC:** UC-А-02

After N_эмп counted attempts, difficulty is computed from the confirmed grades of the people who solved it. A gap of more than 1 sub-level versus the personas is marked on the dashboard.

### FR-А-07. One-prompt check

**Priority:** MVP · K2 · **UC:** UC-А-09

A variant is sent as one request to 2–3 models, R_one_shot times each. The one-shot pass rate is the share of runs with a passing score. At or above P_one_shot the mark is «Только с интервью», and scoring follows FR-К-14.

### FR-А-08. Leak alerts

**Priority:** MVP · K2 · **UC:** UC-А-10, UC-А-11

Per pattern and variant, by day: share solved, median time, count of similar solutions. An alert fires if, over 7 days with at least 20 attempts, the share rose by Δ_утечка points against the previous 30 days, or median time fell by 40% or more, or 3 or more solutions match by 90% or more. Statuses: «Новый», «В работе», «Утечка подтверждена», «Ложная тревога».

### FR-А-09. Search monitoring

**Priority:** extra · K2 · **UC:** UC-А-12

Once every 24 hours the system searches open sources for distinctive phrases of the load-bearing elements of active patterns. A hit is shown with a link. Confirming it is the same as confirming a leak.

### FR-А-10. What a leak does

**Priority:** MVP · K2 · **UC:** UC-А-10, UC-А-12

«Утёк» stops the pattern from entering new attempts within 1 minute. Attempts already started are not interrupted. Affected attempts follow FR-К-22. The pattern is replaced by a new one with different load-bearing elements for the same skill.

### FR-А-11. Pattern reserve

**Priority:** MVP · K2 · **UC:** UC-А-04

Each skill the test checks has at least 2 active patterns per difficulty step. A shortage is a warning in the bank and on the dashboard.

### FR-А-12. Proctoring queue

**Priority:** MVP · K2 · **UC:** UC-А-13, UC-А-14

Oldest first. The card has screen, camera, and audio with event marks, the interview transcript, flags, and the candidate's violation history. Decisions: «Нарушения нет», «Нарушение подтверждено» (a reason is required), «Нужна повторная попытка». The deadline is T_проверки.

## Protection

### FR-А-13. Suspicious employers

**Priority:** extra · K6 · **UC:** UC-А-15, UC-Р-38

Signals: FR-Р-24; 3 or more reports from different candidates in 30 days; 30% or more declines with «Подозрительное предложение»; the same invitation text to 30 or more people in a day; an invitation band 30% or more below the vacancy band. Decisions: «Снять подозрение», «Предупредить», «Ограничить», «Заблокировать». Company statuses: «Активен», «Под подозрением», «Ограничен», «Заблокирован». While limited, the employer sees the reason and the limit on «Статус аккаунта».

### FR-А-14. Ban list

**Priority:** MVP · K6 · **UC:** UC-А-16, UC-А-17

Search by email or ID. A ban of 7, 30, or 90 days, or indefinite, with a reason. Unban with a comment. Effects follow FR-О-13. Withdrawn invitations are not restored after an unban.

### FR-А-15. Reports

**Priority:** extra · K6 · **UC:** UC-А-18

A queue with filters, context, and decisions «Отклонить», «Предупредить», «Заблокировать». The author learns that a decision was made, without the details.

### FR-А-16. Dictionaries

**Priority:** MVP · K5 · **UC:** UC-А-19, UC-А-20

Specializations, the 11 grades with descriptions, industries, skills, FSP disciplines and event levels, reasons for decline, closing, and reports. A value already in use can only be archived. A new value appears in forms within 1 minute.

### FR-А-17. Parameters

**Priority:** MVP · K2 · **UC:** UC-А-21

Every parameter from [chapter 09](09-parameters.md) is on one page: description, unit, range, value. A change requires a comment, applies only to new events, and is written to the log with the old and new value.

## Validation

### FR-А-18. K2 dashboard

**Priority:** MVP · K2 · **UC:** UC-А-01, UC-А-02

By specialization and level, against NFR-19 through NFR-23: difficulty, discrimination, consistency, variant equivalence, match to the reference labels, categorization correctness, one-shot pass-rate distribution. CSV export.

### FR-А-19. K1 dashboard

**Priority:** MVP · K1 · **UC:** UC-А-01

Share of relevant people in the top 10 and top 20, share of needs with a relevant person in the top 3, share of accepted invitations, share of declines «Не подходит стек». Targets are NFR-24.

### FR-А-20. Reference sets

**Priority:** MVP · K2 · **UC:** UC-А-03

Personas with an expert grade (K2) and need–candidate pairs labelled «релевантен», «частично», «не релевантен» (K1). Upload a file or edit the table. «Пересчитать метрики» runs the set and updates the dashboard.

### FR-А-21. Assembling a test for a need

**Priority:** MVP · K2 · **UC:** UC-А-22

For any need, including three demo needs (Backend, Frontend, Data/ML), the page shows skills, patterns, step order, two variants of one pattern with the changed variables highlighted, the one-shot pass rate, and the estimated difficulty.

### FR-А-22. Audit log

**Priority:** MVP · K4 · **UC:** UC-А-23

The log stores administrator actions, views of proctoring recordings, views of contacts, sign-ins and failed sign-ins, and 2FA resets. A row is time, who, action, object, old value, new value. Rows cannot be edited or deleted. Retention is NFR-18.
