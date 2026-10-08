# KADRY — frontend

React 19 + TypeScript + Vite, архитектура Feature-Sliced Design. Правила слоёв и импортов —
в [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).

## Требования

Node.js 22 LTS (`../.nvmrc`; `engines.node >= 22.12`), npm 10+.

## Команды

```bash
npm install          # install (+ husky pre-commit hook в корне репозитория)
npm run dev          # dev-сервер http://localhost:5173, /api проксируется на DEV_API_PROXY_TARGET
npm run build        # typecheck + production-сборка в dist/
npm run preview      # раздать dist/ на http://localhost:4173
npm run lint         # oxlint (+ FSD-границы, циклы, a11y) — предупреждения тоже валят
npm run lint:fix
npm run format       # prettier --write
npm run format:check
npm run typecheck    # tsc для src/tests и для vite.config.ts
npm test             # vitest run (jsdom)
npm run test:watch
```

## Переменные окружения

Vite читает `.env` из **корня репозитория** (`envDir: '..'`). В бандл попадают только `VITE_*` —
секреты туда не кладём.

| Переменная             | По умолчанию            | Назначение                                           |
| ---------------------- | ----------------------- | ---------------------------------------------------- |
| `VITE_API_URL`         | `/api/v1`               | база API (валидируется zod в `shared/config/env.ts`) |
| `DEV_API_PROXY_TARGET` | `http://localhost:8000` | куда dev-сервер проксирует `/api`                    |

## Структура

```
src/
  app/       точка входа, провайдеры, роутер и guard'ы, layout, глобальные стили
  pages/     landing, auth, profile (кабинет), feed (лента и свайпы), vacancies, company, candidate,
             matching, responses, calendar, testing, test-builder, fsp-callback, admin, not-found
  widgets/   site-header, landing-hero, candidate-feed, vacancy-feed, feed-swipe, candidate-deck,
             vacancies-table, invitations-inbox, responses-hub, messenger, meeting-calendar,
             assessment-runner, assessment-bank, assignment-inbox, assignment-review,
             attempt-interview
  features/  start-signup, auth-by-email, edit-account, edit-resume, edit-candidate-settings,
             edit-company, edit-vacancy, company-verification, link-fsp-id, download-resume,
             filter-candidates, filter-vacancies, feed-reaction, invite-candidate,
             respond-to-invitation, respond-to-like, manage-meeting, notification-stream,
             start-assessment, answer-quiz, answer-open, solve-code-task, take-assignment,
             send-test-assignment, review-assignment, edit-assessment-task
  entities/  user, session, category, candidate, company, vacancy, invitation, match, response,
             conversation, calendar-event, assessment
  shared/    api (http, ошибки, query-client), config (env, routes), lib, ui
tests/       setup, test-utils и интеграционные тесты по разделам (лента, фильтры, сохранённые
             поиски, кабинет, тестирование, ФСП, роутинг…)
```

Импорт только через public API slice'а: `import { CandidateCard } from '@/entities/candidate'`.
Алиас `@/*` → `src/*` настроен в `tsconfig.json` и `vite.config.ts` (его же используют vitest и IDE).

## Ленты и фильтры

Страница `/feed` — две ленты с общей раскладкой: у работодателя «Кандидаты»
(`widgets/candidate-feed`), у соискателя «Вакансии для вас» (`widgets/vacancy-feed`). Панели
фильтров — отдельные фичи: `features/filter-candidates` и `features/filter-vacancies`; строятся
они из общего набора `shared/ui/filter-kit` (режим со списком и поиском, чипы со счётчиками,
комбобокс с тегами, поле денег, «ослабить фильтр», «☆ Сохранить поиск»).

- **Состояние — в адресной строке.** Имена параметров совпадают с API (например, `grade=middle`, `stack=Python`,
  `workFormat=remote`), поэтому ссылка воспроизводит выдачу. Читают и пишут его хуки
  `useCandidateFilters` и `useVacancyFilters`; панель, список и запросы смотрят в одно место.
- **Счётчики и подсказки** приходят с бэкенда (`/facets`, `/presets`): фронтенд ничего не
  пересчитывает сам. Типы — в `entities/candidate` и `entities/vacancy`.
- **Из вакансии / из профиля.** Выбор режима подставляет фильтры, метки «из вакансии» показывают,
  что совпадает с источником, «изменено · вернуть» — что нет; тост даёт отменить выбор.
- **Сохранённые поиски** лежат в меню режима; новые результаты приходят событием
  `saved_search_new` через `features/notification-stream`.

Как устроен сам поиск и правила фильтров — в [`../search.md`](../search.md).

## Docker

Многостадийный образ: сборка на `node:22-alpine`, раздача `nginx:1.29-alpine`. nginx проксирует
`/api/` на `BACKEND_UPSTREAM` (по умолчанию `http://backend:8000`), остальное — SPA fallback.
