---
icon: lucide/layout-grid
---

# Page map

An empty list names the next step. The rule is FR-О-11.

## Shared

| ID | Page | Primary action | Empty and errors |
|----|------|----------------|------------------|
| П-О-01 | Home | «Я ищу работу» or «Я нанимаю» | None |
| П-О-02 | Sign-up | «Продолжить» | Email taken — offer sign-in |
| П-О-03 | Email confirmation | Enter the code | Wrong code — «Отправить письмо ещё раз» |
| П-О-04 | Sign-in | «Войти» | Email not confirmed — the code again |
| П-О-05 | Chats | «Отправить» | The chat opens after acceptance or mutual interest |
| П-О-06 | Calendar | «Подтвердить» or «Назначить встречу» | «Встреч пока нет» |
| П-О-07 | Error | «На главную» | Someone else's object is unavailable |
| П-О-08 | Return from Yandex | The session opens on its own | «Сначала зарегистрируйтесь» |

Candidate menu: vacancy feed and swipes, mutual interest, testing, calendar, cabinet.

| ID | Page | Primary action | Empty and errors |
|----|------|----------------|------------------|
| П-К-01 | Resume | «Сохранить резюме» | A PDF without a model key — the form by hand |
| П-К-02 | Cabinet | Open the resume or FSP | No category — take the test |
| П-К-03 | Testing | «Начать тест» | Cooldown — the date of the next attempt |
| П-К-04 | Grade choice | Pick intern, junior, middle, senior, or lead | Five grades |
| П-К-05 | Test | «Отправить решение» | The draft is saved on leave |
| П-К-06 | AI interview | «Отправить ответы» | Without a model key this step does not hold the grade |
| П-К-07 | My categories | «Пройти тест на другой грейд» | Cooldown — the button waits for the date |
| П-К-08 | Invitations | «Открыть приглашение» | «Приглашений нет» |
| П-К-09 | Invitation card | «Принять» | Already answered — view only |
| П-К-10 | Take-homes | «Начать» | «Тестовых пока нет» |
| П-К-11 | Vacancies | Like or skip | No matches — «Сбросить фильтры» |
| П-К-12 | Mutual interest | «Открыть чат» | Nobody has answered yet |
| П-К-13 | Job search | «Не ищу работу» | The profile leaves the bank |
| П-К-14 | FSP | «Связать с ФСП» | An empty registry is not an error |

Employer menu: swipes, feed, responses, vacancies, ATS, take-homes, calendar, cabinet.

| ID | Page | Primary action | Empty and errors |
|----|------|----------------|------------------|
| П-Р-01 | Company profile | «Сохранить» | Without a profile an invitation does not go out |
| П-Р-02 | Swipes | «Интересно» or «Пропустить» | The deck is finished |
| П-Р-03 | Candidate feed | Open the card | A filter narrowed the feed to zero |
| П-Р-04 | Candidate card | «Пригласить» | Contacts after «Принять» |
| П-Р-05 | Invitation form | «Отправить приглашение» | There is already an unanswered invitation |
| П-Р-06 | Invitations | «Открыть чат» | «Приглашений нет» |
| П-Р-07 | Vacancies | «Опубликовать» | A draft is not in the feed |
| П-Р-08 | Take-homes | «Отправить тестовое» | «Тестовых пока нет» |
| П-Р-09 | ATS | «Опросить» | First «Подключить демо» |

Administrator menu: tasks, analytics, companies, ban list, dictionaries, parameters, journal.

| ID | Page | Primary action |
|----|------|----------------|
| П-А-01 | Task bank | «Добавить задание» |
| П-А-02 | Task analytics | Take a snapshot |
| П-А-03 | Company check | Confirm or refuse |
| П-А-04 | Ban list | Block |
| П-А-05 | Dictionaries | Add a value |
| П-А-06 | Parameters | Save with a comment |
| П-А-07 | Journal | Open a record |
