---
icon: lucide/layout-grid
---

# Page map

One primary action per page. An empty state names the next step and contains the button for it. The rule for empty states is FR-О-14. Button labels stay in Russian.

## Shared

| ID | Page | Primary action | Empty and errors |
|----|------|----------------|------------------|
| П-О-01 | Home | «Я ищу работу» or «Я нанимаю» | None |
| П-О-02 | Registration | «Продолжить» | Email taken — sign-in and recovery; bad format — a hint |
| П-О-03 | Email confirmation | «Сохранить пароль» | Link older than 24 hours — «Отправить письмо ещё раз» |
| П-О-04 | Sign-in | «Войти» | 5 failures — a 15-minute lock; unconfirmed email — send again |
| П-О-05 | Password recovery | «Отправить ссылку» | An unknown address gets the same answer as a known one |
| П-О-06 | 2FA | «Подтвердить код» | Wrong code — a counter; no app — a backup code |
| П-О-07 | Chats | «Отправить» | The chat opens after acceptance; a file over 10 MB — an error on the field |
| П-О-08 | Calendar | Candidate: «Подтвердить». Employer: «Назначить встречу» | «Встреч пока нет. Встречу назначает рекрутер в чате» |
| П-О-09 | Notifications | «Открыть» | «Новых событий нет» |
| П-О-10 | Error | «На главную» or «Повторить» | 403, 404, 500, no connection |
| П-О-11 | Account banned | «Написать в поддержку» | Reason and term |
| П-О-12 | Report | «Отправить жалобу» | No reason — the button stays inactive |
| П-О-13 | Documents | «Скачать PDF» | Policy and consent texts with versions |

Candidate menu: Приглашения, Чаты, Расписание, Вакансии, Задачи, Категория и грейд, Резюме, Настройки.

| ID | Page | Primary action | Empty and errors |
|----|------|----------------|------------------|
| П-К-01 | Onboarding | «Создать резюме» | All steps done — straight to «Приглашения» |
| П-К-02 | Resume | «Сохранить резюме» | A hint about PDF; not a PDF, over 5 MB, or a scan — the manual form |
| П-К-03 | Profile | «Скачать PDF-профиль» | No category — «Не подтверждён» and «Пройти тест» |
| П-К-04 | Test offer | «Начать тест» | A refusal warns about the low rank |
| П-К-05 | Survey | «Далее» | Interrupted — continue from the same question |
| П-К-06 | Grade choice | «Выбрать и продолжить» | 11 grades |
| П-К-07 | Device check | «Начать тест» after 3 green checks | No permission — instructions; a tab instead of the screen — ask again |
| П-К-08 | Computer required | «Отправить ссылку на почту» | Phone or a browser without screen share |
| П-К-09 | Test | «Отправить решение» | A drop pauses; stopping the share — 60 seconds |
| П-К-10 | AI interview | «Закончить ответ» | 30 seconds of silence — repeat the question |
| П-К-11 | Test result | «Принять грейд» | Below — a test one level down; flags — «Результат на проверке» |
| П-К-12 | Category and grade | «Пройти тест на другой грейд» | Cooldown — the button is inactive and shows a date |
| П-К-13 | Invitations | «Открыть приглашение» | No category or no invitations — a banner and tips |
| П-К-14 | Invitation card | «Принять» | Expired or withdrawn — view only |
| П-К-15 | Take-homes | «Начать» | «Тестовые приходят только после того, как вы приняли приглашение» |
| П-К-16 | Recurring task | «Отправить решение» | «Следующая задача придёт <дата>» |
| П-К-17 | Vacancies | Swipe right or «Откликнуться» | No matches — «Сбросить фильтры» |
| П-К-18 | Vacancy card | «Откликнуться» | «Вакансия закрыта» |
| П-К-19 | My applications | «Открыть чат» | «Откликов нет» and «Смотреть вакансии» |
| П-К-20 | Hire confirmation | «Подтвердить» | A dialog |
| П-К-21 | Settings: privacy | «Сохранить» | The search pause lives here too |
| П-К-22 | Settings: consents | «Отозвать» | Dates and versions |
| П-К-23 | Settings: FSP | «Связать с ФСП» | No history — neutral text; service down — «Попробуйте позже» |
| П-К-24 | Settings: security | «Сохранить» | Wrong current password — an error on the field |

Employer menu: Потребности, Банк кандидатов, Приглашения, Вакансии и отклики, Чаты, Расписание, Задачи, Профиль компании, Настройки.

| ID | Page | Primary action | Empty and errors |
|----|------|----------------|------------------|
| П-Р-01 | Onboarding | «Настроить 2FA» | Then the profile and the first need |
| П-Р-02 | Company profile | «Сохранить» | Without a profile, invitations are unavailable |
| П-Р-03 | Needs | «Описать потребность» | «Опишите, кого ищете — подборка появится сразу» |
| П-Р-04 | Need form | «Показать подборку» | No salary — the button stays inactive |
| П-Р-05 | Shortlist | «Пригласить» or a swipe | No confirmed people — neighbouring categories and «Показать неподтверждённых» |
| П-Р-06 | Candidate bank | «Открыть кандидата» | A hint about which filter narrows the most |
| П-Р-07 | Candidate card | Before contact «Пригласить», after «Открыть чат» | «Профиль недоступен» |
| П-Р-08 | Favourites and hidden | «Пригласить» | «Свайпните кандидата вправо в подборке» |
| П-Р-09 | Invitation form | «Отправить приглашение» | Band, daily limit, repeat |
| П-Р-10 | Invitations | «Открыть чат» | «Приглашений нет» and «Открыть подборку» |
| П-Р-11 | Vacancies | «Опубликовать потребность» | A hint to publish so applications can arrive |
| П-Р-12 | Applications | «Принять» | «Откликов пока нет» and «Открыть подборку» |
| П-Р-13 | Take-homes | «Открыть результат» | «Отправьте тестовое из чата» |
| П-Р-14 | Recurring tasks | «Создать задачу» | A hint about a task with no correct answer |
| П-Р-15 | Close a need | «Закрыть потребность» | «Наняли через платформу» without a candidate — the button stays inactive |
| П-Р-16 | Account status | «Написать в поддержку» | Limits and reasons |
| П-Р-17 | ATS integration | «Выгрузить в ATS» | Extra, a concept |

Administrator menu: Дашборд валидации, Задания, Утечки, Прокторинг, Работодатели и жалобы, Банлист, Справочники, Параметры, Эталонные наборы, Журнал, Администраторы.

| ID | Page | Primary action |
|----|------|----------------|
| П-А-01 | Validation dashboard | «Открыть метрику». Empty: «Загрузите эталонный набор» |
| П-А-02 | Reference sets | «Пересчитать метрики» |
| П-А-03 | Pattern bank | «Создать паттерн» |
| П-А-04 | Pattern card | «Сгенерировать варианты», then «Активировать» |
| П-А-05 | LLM-persona calibration | «Запустить калибровку» |
| П-А-06 | One-prompt check | «Запустить проверку» |
| П-А-07 | Leak analytics | «Разобрать алерт» |
| П-А-08 | Search monitoring | «Подтвердить совпадение» |
| П-А-09 | Proctoring queue | «Принять решение» |
| П-А-10 | Suspicious employers | «Принять решение» |
| П-А-11 | Ban list | «Заблокировать» |
| П-А-12 | Reports | «Рассмотреть» |
| П-А-13 | Dictionaries | «Добавить значение». A value in use can only be archived |
| П-А-14 | Parameters | «Сохранить». Out of range — an error on the field |
| П-А-15 | Assemble a test for a need | «Собрать тест» |
| П-А-16 | Audit log | «Найти» |
| П-А-17 | Administrators | «Добавить администратора». The last one cannot be removed |
