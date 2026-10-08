---
icon: lucide/clipboard-check
---

# Assessment and category

Refusing the test, the survey, 11 grades, proctoring, the AI interview, and assigning a category. Screens: П-К-04 through П-К-12.

## FR-К-07. Refusing the test

**Priority:** MVP · K2 · **UC:** UC-К-06, UC-К-07

The test is offered right after the first resume. A refusal is confirmed with «Без теста резюме видно работодателям, но всегда ниже кандидатов с подтверждённым грейдом». The status becomes «Не подтверждён», and «Приглашения» shows the banner «Пройти тест». A reminder email is sent at most once every 14 days.

## FR-К-08. Survey

**Priority:** MVP · K2 · **UC:** UC-К-08

At most 10 questions and 5 minutes: industries (up to 3), specialization (from the resume, can be changed), stack, experience, roles. Each answer is saved immediately and kept in the history. The stack decides which skills the test checks. The survey works on a phone. An interrupted survey continues from the same question.

## FR-К-09. Choosing a claimed grade

**Priority:** MVP · K2 · **UC:** UC-К-09

The candidate picks 1 of 11: Junior−, Junior, Junior+, Middle−, Middle, Middle+, Senior−, Senior, Senior+, Lead, Head. Each has a short description, a test duration, and an example of the tasks. The choice sets the test level: Junior, Middle, Senior, Lead, or Head. The resume grade is preselected with the mark «из резюме».

## FR-К-10. Test composition and adaptive order

**Priority:** MVP · K2 · **UC:** UC-К-12, UC-А-22

For Junior, Middle, and Senior the test is N_задач tasks from different patterns, one skill from the candidate's stack each, with code where the skill allows it. Inside a level there are three steps: lower («−»), middle, upper («+»). The first task is middle. A score of at least P_задача moves the next task up a step; otherwise it moves down. Lead and Head get one Senior+ coding task and two cases without code (architecture and management; Head also covers team and budget). Cases are scored by the pattern rubric. Duration is T_тест.

## FR-К-11. Unique variants

**Priority:** MVP · K2 · **UC:** UC-К-12, UC-А-05

A variant is not given to a second candidate while the pattern still has unused variants. Coding tasks have per-candidate inputs and a per-candidate correct answer. A candidate does not see a pattern they already saw if the skill has another active pattern.

## FR-К-12. Proctoring

**Priority:** MVP · K2 · **UC:** UC-К-10, UC-К-14, UC-А-13

A grade test starts only with the camera, the microphone, a full-screen share, and a separate consent to record. The system records leaving the tab, leaving fullscreen, a paste longer than 200 characters, a second face, no face for more than 10 seconds, another voice, and stopping the share. Stopping the share pauses for 60 seconds; after that the attempt is «Прервана». One high-severity flag or three low-severity flags send the attempt to the proctoring queue. Recurring tasks and employer take-homes are not proctored.

**UI strings:** «Начать тест», «Возобновить трансляцию».

## FR-К-13. Desktop only

**Priority:** MVP · K3 · **UC:** UC-К-11

On a phone, a tablet, or a browser that cannot share the screen, the button leads to «Нужен компьютер» and «Отправить ссылку на почту». The survey and the grade choice made on a phone are kept.

## FR-К-14. AI interview

**Priority:** MVP · K2 · **UC:** UC-К-15, UC-А-09

After each task the AI asks 2–3 voice questions about the solution: why this approach, what changes, where it is weak. An answer is up to 2 minutes. A question can be repeated once. Thirty seconds of silence repeats the question, then scores 0. The interview score enters the total with weight W_интервью. If a variant is marked «Только с интервью», the task score counts only when the interview score is at least P_интервью.

**UI strings:** «Закончить ответ», «Повторить вопрос».

## FR-К-15. Autosave and a dropped connection

**Priority:** MVP · K2 · **UC:** UC-К-13

The answer is saved every 10 seconds and on every step. A drop pauses the timer. An attempt allows 5 minutes of pause in total and 3 drops. Beyond that the status is «Прервана»: scoring uses the saved answers, and the attempt goes to the proctoring queue. The person can return by the same link in the same browser.

## FR-К-16. Score and sub-level

**Priority:** MVP · K2 · **UC:** UC-К-16, UC-К-17

The total is 0–100: task scores weighted by W_ступень and the interview weighted by W_интервью. Below P_минус the level is not confirmed. From P_минус to P_проход is «−». From P_проход to P_плюс is the base. From P_плюс is «+». Lead and Head have no sub-level: from P_проход the level is confirmed. The result is shown per skill.

## FR-К-17. Branches after the result

**Priority:** MVP · K2 · **UC:** UC-К-17, UC-К-18, UC-К-19

An unconfirmed level offers a test one level down. Until the first confirmation, N_первичных attempts in a row have no pause; after that the pause is T_пауза_попытки. Junior− has no lower level. If the sub-level is below the claim, the candidate accepts it or stays «Не подтверждён». A score of at least P_уверенно plus a solved upper-step task offers a test of the next level for 7 days, once, outside T_кулдаун. Failing the next level keeps the current grade.

**UI strings:** «Принять грейд», «Не принимать», «Пройти тест на уровень ниже», «Пройти тест на уровень выше».

## FR-К-18. Assigning a category

**Priority:** MVP · K2 · **UC:** UC-К-16, UC-К-20

A category is the resume specialization plus the confirmed grade. It is assigned after the candidate accepts the result and is visible to employers within 1 minute. While the attempt is in the proctoring queue the status is «Результат на проверке» and no category is assigned from it. Without a counted test the status is «Не подтверждён».

## FR-К-19. How often a grade can change

**Priority:** MVP · K2 · **UC:** UC-К-22

A confirmed grade can change no sooner than T_кулдаун after the last confirmation. A failed attempt does not change the grade; the next attempt waits T_пауза_попытки. The system never lowers a grade by itself. The dates are visible on «Категория и грейд».

**UI strings:** «Пройти тест на другой грейд».

## FR-К-20. Survey and test history

**Priority:** MVP · K2 · **UC:** UC-К-21

Each resume keeps surveys and attempts: date, target grade, score, sub-level, per-skill result, status («Идёт», «Прервана», «На проверке», «Засчитана», «Не засчитана», «Аннулирована»). Task texts and reference answers are not shown to the candidate after the test.

## FR-К-21. A proctoring violation

**Priority:** MVP · K2 · **UC:** UC-К-20, UC-А-13, UC-А-14

«Нарушения нет» counts the result. «Нарушение подтверждено» sets the attempt to «Аннулирована», keeps the previous grade, and the next attempt waits T_пауза_нарушение. The candidate receives the reason. A second confirmed violation within 12 months raises a ban question for the administrator. «Нужна повторная попытка» allows a test without cooldown for 14 days.

## FR-К-22. A leaked task

**Priority:** MVP · K2 · **UC:** UC-А-10, UC-А-12

A confirmed leak does not cancel grades automatically. Attempts after the first signal, where a task from the leaked pattern was solved and the interview score is below P_интервью, go to the queue. Affected candidates are offered a replacement task on the same skill without cooldown for 14 days.
