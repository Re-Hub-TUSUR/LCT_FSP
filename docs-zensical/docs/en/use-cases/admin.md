---
icon: lucide/shield
---

# Administrator scenarios

Normative text: [admin](../business/brd/07-admin.md).

## UC-А-01 Mechanic health

**As** an administrator, **I want** to pick a specialization and a level, **so that** I see K2 and K1 with colour: green means the target is met, red means it is not. FR-А-18, FR-А-19.

## UC-А-02 A red metric

**As** an administrator, **I want** to open a metric, **so that** I see the patterns and variants pulling it down. FR-А-18.

## UC-А-03 Reference set

**As** an administrator, **I want** to upload personas or pairs and press «Пересчитать метрики», **so that** the dashboard updates. A format error lists the bad rows. FR-А-20.

## UC-А-04 New pattern

**As** an administrator, **I want** to press «Создать паттерн» and fill the card, **so that** it is saved as «Черновик». FR-А-02.

## UC-А-05 Variants

**As** an administrator, **I want** to set a count and press «Сгенерировать варианты», **so that** only variables change and duplicates are dropped. FR-А-04.

## UC-А-06 Activation

**As** an administrator, **I want** to press «Активировать», **so that** the pattern turns on or the missing checks are listed. FR-А-03.

## UC-А-07 Calibration

**As** an administrator, **I want** to press «Запустить калибровку», **so that** I see the estimated sub-level of each variant. FR-А-05.

## UC-А-08 Rejection

**As** an administrator, **I want** to exclude out-of-tolerance variants with one button. FR-А-05.

## UC-А-09 One-shot

**As** an administrator, **I want** to press «Запустить проверку», **so that** I see the pass rate and the mark «Только с интервью» where it is at least P_one_shot. FR-А-07.

## UC-А-10 Leak

**As** an administrator, **I want** to press «Подтвердить утечку», **so that** the pattern becomes «Утёк» and affected attempts enter the queue. FR-А-08, FR-А-10.

## UC-А-11 False alarm

**As** an administrator, **I want** to press «Ложная тревога» with a comment, **so that** the alert closes and the baseline is recomputed. FR-А-08.

## UC-А-12 A hit in search

**As** an administrator, **I want** to open the link and press «Подтвердить совпадение», **so that** the pattern becomes «Утёк», as in UC-А-10. FR-А-09. Extra.

## UC-А-13 Attempt decision

**As** an administrator, **I want** to watch the recording and the transcript and pick a decision with a reason, **so that** the candidate is notified. FR-А-12.

## UC-А-14 Retake

**As** an administrator, **I want** to choose «Нужна повторная попытка», **so that** the candidate can take the test without cooldown for 14 days. FR-А-12.

## UC-А-15 Company signal

**As** an administrator, **I want** to choose «Снять подозрение», «Предупредить», «Ограничить», or «Заблокировать», **so that** the decision is written to the log. FR-А-13. Extra.

## UC-А-16 Ban

**As** an administrator, **I want** to find a person by email or ID, pick a term and a reason, **so that** sign-in closes under FR-О-13. FR-А-14.

## UC-А-17 Unban

**As** an administrator, **I want** to press «Разблокировать» with a comment, **so that** access returns and withdrawn invitations are not restored. FR-А-14.

## UC-А-18 Report

**As** an administrator, **I want** to look at an invitation, a vacancy, or a chat fragment and choose «Отклонить», «Предупредить», or «Заблокировать», **so that** the author learns a decision exists, without the details. FR-А-15. Extra.

## UC-А-19 New value

**As** an administrator, **I want** to press «Добавить значение», **so that** it appears in forms within a minute. FR-А-16.

## UC-А-20 Archive

**As** an administrator, **I want** to press «В архив», **so that** the value hides in new forms and stays in old data. FR-А-16.

## UC-А-21 Parameter

**As** an administrator, **I want** to enter a value with a comment, **so that** it applies to new events and is written to the log. Out of range is an error. FR-А-17.

## UC-А-22 Assemble a test

**As** an administrator, **I want** to pick a demo need and press «Собрать тест», **so that** I see skills, patterns, order, and two variants. FR-А-21.

## UC-А-23 Audit log

**As** an administrator, **I want** to filter by person, type, and date, **so that** I read rows I cannot edit. FR-А-22.

## UC-А-24 New administrator

**As** an administrator, **I want** to enter an email, **so that** a colleague receives an invitation and sets up 2FA on the first sign-in. FR-А-01.
