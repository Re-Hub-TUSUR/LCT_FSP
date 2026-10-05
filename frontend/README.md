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
  pages/     landing, auth (+ employer/candidate), profile, vacancies, company, candidate,
             calendar, matching (swipe + profile), testing, admin, not-found
  widgets/   site-header, landing-hero, vacancies-table, invitations-inbox, candidate-deck
  features/  start-signup, auth-by-email, invite-candidate, respond-to-invitation
  entities/  user, session, category, candidate, company, vacancy, invitation, match,
             calendar-event, assessment
  shared/    api (http, ошибки, query-client), config (env, routes), lib, ui
tests/       setup, test-utils, интеграционные тесты роутинга
```

Импорт только через public API slice'а: `import { CandidateCard } from '@/entities/candidate'`.
Алиас `@/*` → `src/*` настроен в `tsconfig.json` и `vite.config.ts` (его же используют vitest и IDE).

## Docker

Многостадийный образ: сборка на `node:22-alpine`, раздача `nginx:1.29-alpine`. nginx проксирует
`/api/` на `BACKEND_UPSTREAM` (по умолчанию `http://backend:8000`), остальное — SPA fallback.
