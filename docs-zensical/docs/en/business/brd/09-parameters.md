---
icon: lucide/sliders-horizontal
---

# Parameters and open questions

An administrator changes parameters on «Параметры» (FR-А-17). The starting values are the team's proposal for the demo and still need confirmation. The questions below are not closed by this documentation.

## Starting values

| Parameter | What it sets | Start |
|-----------|--------------|-------|
| T_кулдаун | Pause between changes of a confirmed grade | 90 days |
| T_пауза_попытки | Pause after an attempt that did not confirm a grade | 30 days |
| N_первичных | Attempts in a row with no pause before the first confirmation | 3 |
| T_пауза_нарушение | Pause after a confirmed violation | 90 days |
| N_задач | Tasks in a Junior, Middle, or Senior test | 4 (allowed 3–5) |
| T_тест | Test time including the interview | Junior 60 min, Middle 75, Senior / Lead / Head 90 |
| P_задача | Score after which the next task is harder | 70% |
| P_минус, P_проход, P_плюс | Bounds for «−», base, «+» | 50, 65, 80 of 100 |
| P_уверенно | Score that offers a higher test | 90 of 100 |
| W_ступень | Weights of the lower, middle, and upper step | 0.7; 1.0; 1.3 |
| W_интервью | Interview share of the total | 30% |
| P_интервью | Minimum interview score for «Только с интервью» | 60 of 100 |
| P_one_shot | Pass rate that marks «Только с интервью» | 40% |
| P_one_shot_паттерн | Median above which a pattern cannot be activated | 60% |
| R_one_shot | Runs per model | 5 |
| R_персон | Runs per persona | 5 |
| N_эмп | Attempts before difficulty uses real solutions | 30 |
| Δ_утечка | Rise in solve rate over 7 days that raises an alert | 25 percentage points |
| T_проверки | Deadline for a proctoring decision | 48 hours |
| T_ответ | Deadline to answer an invitation or an application | 14 days |
| T_повтор_приглашения | Pause before a repeat after a decline | 30 days |
| L_приглашений | Invitations per day per company | 50 |
| L_приглашений_огр | The same while «Ограничен» | 10 |
| L_откликов | Candidate applications per day | 30 |
| L_тестовых | Active take-homes per candidate | 2 |
| L_задач | Active recurring tasks per company | 5 |
| F_регуляр | How often a recurring task arrives | Once every 14 days |
| T_регуляр | Suggested time for it | 30 minutes |
| T_актуальность | Window in which a profile counts as fresh | 60 days |
| W_категория, W_стек, W_профиль, W_ФСП, W_свежесть | Match-score weights | 0.25; 0.30; 0.25; 0.10; 0.10 |
| K_вилка | Maximum «до» / «от» | 2 |
| N_резюме | Resumes per candidate | 3 |
| T_подтверждение_найма | How long the candidate has to answer a hire | 14 days |
| N_фикт | Minimum share of closings with a hire | 30% |
| M_мин_закрытий | How many closings before the rule applies | 10 |

## Defaults waiting for the product owner

1. The candidate's home screen is «Приглашения».
2. A take-home only after an invitation is accepted, up to 90 minutes.
3. Fake vacancies: 30% from 10 closings, a hire counts only with the candidate's confirmation, an administrator decides the ban. Open: whether «Наняли вне платформы» should count with weight 0.5.
4. 2FA is required for the employer and the administrator.
5. No FSP history means no bonus and no penalty.
6. Unconfirmed people always rank lower. «Только подтверждённые» is on.
7. A chat opens after an accepted invitation, a match, or an accepted application.
8. The recruiter schedules the meeting. The candidate confirms or asks to move it.

## Forks already chosen

1. **11 grades.** The test runs at a level. The sub-level comes from steps and score bounds. Lead and Head: one Senior+ task and two cases. Risk: an LLM scores the cases. A suggested check is an expert review of 10% of those attempts.
2. **Invitation without a vacancy.** Everything hangs off a private need. A vacancy is a published need. From the bank without a need the system creates a one-off offer. Matches exist only on published vacancies.
3. **Hire outside the platform.** A separate outcome. In the fake-vacancy rule it is a closing without a confirmed hire.
4. **Phone.** The grade test is unavailable. The survey and the grade choice are available.
5. **Violation and leak.** A violation cancels the attempt and does not touch the grade. A leak does not cancel grades in bulk.
6. **Recurring tasks and take-homes.** They refresh freshness (up to 10% of the score) and do not change the grade. After the MVP: three take-homes in a row above the grade may offer a promotion test without cooldown.

## Still open

A text interview mode for people with hearing or speech impairments. A lawyer on camera recordings as biometrics. GDPR if the product later serves the EU. Agree the FSP result fields with FSP. A reference set of 200 personas and 10 needs with 30 candidates each. Which 2–3 models run the one-shot check. Whether expected salary is visible by default. Whether 5 seconds of swipe undo is enough. A starting list of 10 industries.
