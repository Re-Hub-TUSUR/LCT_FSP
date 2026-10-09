---
icon: lucide/clipboard-check
---

# Assessment and category

The candidate picks a grade, takes a test from the task bank, and, when the code works, answers written questions. Screens: П-К-03, П-К-04, П-К-05 … П-К-07.

Grades: intern, junior, middle, senior, lead. There are no «−» and «+» steps and no Head grade.

## FR-К-12. The test is not required for a resume

**Priority:** MVP · К2 · **UC:** UC-К-05

Employers can see a resume without a test. Until a test is counted, the category is not confirmed. The candidate starts the test from the testing page.

**UI strings:** «Начать тест».

## FR-К-13. Choosing a grade

**Priority:** MVP · К2 · **UC:** UC-К-06

The candidate picks one of five grades: intern, junior, middle, senior, lead. That grade's template sets the contents, the time, and the pass score. A grade written in the resume does not set a category.

## FR-К-14. What the test contains

**Priority:** MVP · К2 · **UC:** UC-К-07

An attempt is built from the task bank for the chosen grade. It has questions and, where the skill allows it, a coding task. Code runs on the open tests. Finishing checks the hidden tests and sets a score. There is no adaptive «harder / easier» step inside the attempt.

**UI strings:** «Отправить решение».

## FR-К-15. A variant of the candidate's own

**Priority:** MVP · К2 · **UC:** UC-К-07

The task in the attempt is a variant for this candidate. A later edit of the bank card does not change an attempt that was already issued.

## FR-К-16. Written interview

**Priority:** MVP · К2 · **UC:** UC-К-09

If the test passes on points, the hidden tests of the code pass, and a model key is set, the grade waits for an interview. The candidate opens it and sees 2–3 questions about their code. Answers are text, the button is «Отправить ответы». There is a time limit `interview_minutes` (the start value is 15 minutes). A mean score of at least `interview_pass_score` (the start value is 60 out of 100) confirms the grade. Otherwise the grade is not confirmed, and a retry waits for the attempt pause.

Without a model key the interview does not hold the grade back: a test that passed on points is confirmed at once.

There are no voice questions, no repeat-on-silence, and no «Только с интервью» mark.

**UI strings:** «Собеседование с ИИ», «Отправить ответы», «К тестам».

## FR-К-17. Answer draft

**Priority:** MVP · К2 · **UC:** UC-К-08

A quiz answer and a code draft are saved during the attempt. Leaving the page sends the unsaved draft. A hidden tab does not add to the task timer: that timer is for bank analytics, not for proctoring. There is no disconnect pause and no recording-review queue.

## FR-К-18. Score

**Priority:** MVP · К2 · **UC:** UC-К-10

The attempt result is a score. The pass score comes from the grade template. There are no «−» and «+» sublevels.

## FR-К-19. The next grade and a retry

**Priority:** MVP · К2 · **UC:** UC-К-11, UC-К-13

A failed attempt does not change the grade. The next one in the same specialization is not earlier than `assessment_retry_days` (the start value is 7 days). A high score, at least `assessment_recommend_score` (the start value is 85), opens the test of the next grade. There is no step above lead. The system does not lower a grade by itself.

## FR-К-20. Category

**Priority:** MVP · К2 · **UC:** UC-К-10

A category is a specialization and a confirmed grade. It appears when the attempt is counted (and the interview, if one was required, is passed). Without a counted test the category is not confirmed. The candidate chooses which confirmed category employers see.

## FR-К-21. Changing a grade

**Priority:** MVP · К2 · **UC:** UC-К-13

A confirmed grade in a specialization changes no earlier than `assessment_grade_change_days` (the start value is 90 days). The date is on «Мои категории».

**UI strings:** «Пройти тест на другой грейд».

## FR-К-22. Attempt history

**Priority:** MVP · К2 · **UC:** UC-К-12

Per specialization the product keeps attempts: date, target grade, score, and status. Attempt statuses: in progress, interview, counted, not counted, time ran out. Reference answers are not shown to the candidate after the test.
