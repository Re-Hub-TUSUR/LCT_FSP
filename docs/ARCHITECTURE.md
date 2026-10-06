# Архитектура KADRY

## 1. Контекст и принципы

Кейс (ТЗ «ФСП, спецтрек»): платформа, где ИТ-специалисты проходят тестирование и получают
**категорию = специализация + грейд**, а работодатели ищут кандидатов в банке, отправляют
приглашения с **обязательной вилкой зарплаты** и получают контакты только после согласия
кандидата. Дополнительно: мэтчинг свайпами с объяснимыми рекомендациями, календарь (интервью,
слоты тестирования, дедлайны), привязка к FSP ID, согласие на обработку ПДн (152-ФЗ),
подтверждение email, админка.

Принципы:

1. **Монолит, два деплоймент-юнита.** `frontend/` (SPA + nginx) и `backend/` (API) в одном
   репозитории, общий `.env`, общий CI. Без monorepo-тулинга (workspaces/turbo): у частей разные
   экосистемы, общего JS-кода нет.
2. **Контракт — OpenAPI бэкенда.** camelCase на проводе, единый формат ошибок
   `{"error": {"code", "message", "details"}}`, префикс `/api/v1`.
3. **Честные заглушки.** Не реализованные сценарии имеют финальные пути, схемы и ролевые guard'ы,
   но отвечают `501 not_implemented` — без фиктивной бизнес-логики. Фронтенд показывает
   «Раздел ещё в разработке».
4. **Безопасность по умолчанию.** Секреты только из env, валидация конфигурации при старте,
   одинаковый ответ на «нет пользователя» и «неверный пароль», роли перечитываются из БД.
5. **Минимум структуры.** Слои/папки создаются только когда в них есть код.

## 2. Frontend: Feature-Sliced Design

```
app → pages → widgets → features → entities → shared
```

| Слой       | Назначение | Slices |
| ---------- | ---------- | ------ |
| `app`      | вход, провайдеры (QueryClient), роутер, guard'ы, layout, глобальные стили | — |
| `pages`    | экран на маршрут, композиция виджетов/фич | `landing`, `auth` (выбор роли, `EmployerAuthPage`, `CandidateAuthPage`), `profile`, `vacancies`, `company`, `candidate`, `calendar`, `matching` (`MatchingSwipePage`, `MatchingProfilePage`), `testing`, `admin`, `not-found` |
| `widgets`  | крупные самостоятельные блоки | `site-header`, `landing-hero`, `vacancies-table`, `invitations-inbox`, `candidate-deck` (свайпы) |
| `features` | пользовательские действия | `start-signup`, `auth-by-email`, `invite-candidate`, `respond-to-invitation` |
| `entities` | бизнес-сущности: DTO, query-ключи, карточки | `user`, `session`, `category`, `candidate`, `company`, `vacancy`, `invitation`, `match`, `calendar-event`, `assessment` |
| `shared`   | инфраструктура без бизнес-логики | `api` (http-клиент, `ApiError`, query-client), `config` (env, routes), `lib` (формат, валидация), `ui` (Button, TextField, Loader/Error/Empty, QueryState, Page) |

Сегменты: `ui/`, `api/`, `model/`, `lib/`, `config/` — только существующие.

### Маршруты

| Путь | Страница | Доступ |
| ---- | -------- | ------ |
| `/` | лендинг | все |
| `/auth`, `/auth/employer`, `/auth/candidate` | вход/регистрация | все |
| `/profile` | личная страница (по роли) | авторизованные |
| `/vacancies` | общая таблица вакансий | все |
| `/companies/:companyId` | внешняя страница компании | все |
| `/candidates/:candidateId` | внешняя страница сотрудника | все (контакты — по правилам бэкенда) |
| `/calendar` | календарь | авторизованные |
| `/matching` | свайпы | работодатель |
| `/matching/:kind/:id` | открытый профиль кандидата/компании | авторизованные |
| `/testing` | тестирование | кандидат |
| `/admin` | админка | админ |

Страницы грузятся лениво (`lazy` в `app/router/routes.tsx`), доступ — `RequireAuth({ roles })`.
Guard'ы на клиенте — это UX; авторизация обеспечивается бэкендом.

### Правила импортов (проверяются `oxlint`, `frontend/.oxlintrc.json`)

- Только public API: `@/entities/candidate`, не `@/entities/candidate/ui/candidate-card`
  (`no-restricted-imports`, шаблон `@/*/*/**`). Внутри slice — относительные импорты.
- Слой не импортирует вышележащие слои (overrides по `src/shared/**`, `src/entities/**` и т.д.).
- Feature не импортирует другую feature, page — другую page, widget — другой widget
  (виджеты комбинируются через слоты, например `<LandingHero header={<SiteHeader />} />`).
- Сущности ссылаются друг на друга только через `@x`-API: `entities/category/@x/candidate.ts`
  экспортирует ровно то, что нужно `candidate`.
- `import/no-cycle` — ошибка.
- `shared/api` не знает о сессии: `app/providers/setup-http.ts` передаёт `getAccessToken` и
  `onUnauthorized` через `configureHttp` (инверсия зависимости).

### Данные и состояние

- Серверное состояние — TanStack Query. В entity: `<entity>Keys` (ключи), `<entity>Queries`
  (`queryOptions`) и `<entity>Api` (мутации). Жизненный цикл мутаций и инвалидация — в features.
- Сессия — маленький внешний store (`useSyncExternalStore`) в `entities/session`.
- Формы — контролируемые компоненты + zod-схемы в `model/` фичи (покрыты unit-тестами).
- Ошибки: `ApiError` → `getErrorMessage` (501/403/404/сеть) → `ErrorState`; `QueryState`
  унифицирует loading/error/empty; `errorElement` на корневом маршруте ловит падения рендера.
- Безопасность UI: `redirect` после логина принимается только как внутренний путь
  (`isSafeInternalPath`), сайт компании рендерится ссылкой только для `http(s)`.

### Инструменты

Vite 8, TypeScript 7 (strict, `noUncheckedIndexedAccess`), Vitest + Testing Library (jsdom),
oxlint (вместо ESLint, см. компромиссы), Prettier, husky + lint-staged. Алиас `@/*` объявлен в
`tsconfig.json` и `vite.config.ts`; vitest использует конфиг Vite, IDE — tsconfig, oxlint
сопоставляет шаблоны по строке импорта.

## 3. Backend

FastAPI выбран потому, что: асинхронность из коробки, OpenAPI как контракт для фронтенда,
Pydantic для валидации (вилка зарплаты, согласие ПДн), простой DI для ролевых guard'ов.

```
api/routes/*   HTTP: пути, статусы, DI. Без бизнес-логики.
dependencies/  сессия БД, настройки, текущий пользователь, require_roles(...)
services/      сценарии (AuthService, словарь категорий)
repositories/  запросы к БД, без правил
models/        ORM (SQLAlchemy 2, typed), не отдаются наружу
schemas/       публичные контракты (Pydantic, camelCase)
core/          config (pydantic-settings), security (Argon2id, JWT), errors, logging
db/            Base + naming convention, mixins, engine/session (commit/rollback на запрос)
migrations/    Alembic (async), URL из настроек
```

### Модули API (`/api/v1`)

| Тег | Пути | Статус |
| --- | ---- | ------ |
| health | `/health`, `/health/ready` | ✅ |
| auth | `/auth/register`, `/auth/login`, `/auth/verify-email`, `/auth/resend-verification`; `/auth/refresh` | ✅ / 501 |
| users | `/users/me` | ✅ |
| categories | `/categories/dictionary` | ✅ (статический MVP-словарь) |
| candidates (employees) | поиск (Elasticsearch), `/{id}`, реакции ✅; `/me`, резюме PDF, `fsp-link` — 501 | ✅ / 501 |
| companies (employers) | `/{id}` ✅; `/me` GET/PUT — 501 | ✅ / 501 |
| vacancies | список, `feed`, `mine`, `/{id}`, реакции ✅; создание и правка — 501 | ✅ / 501 |
| invitations | создание, `incoming`, `outgoing`, `accept`/`decline` | 501 |
| applications | отклики кандидата | 501 |
| matching | `needs`, `recommendations` | 501 |
| calendar | `/calendar/events?from&to` | 501 |
| assessments (testing) | статус, анкета, попытки, ответы | 501 |
| admin | `/admin/users` | ✅ |

Домены «employers/employees» из задания реализованы как `companies` (профиль работодателя)
и `candidates` (профиль соискателя) — так они называются в ТЗ и в UI; роль пользователя —
`candidate | employer | admin`.

Модели: `User`, `EmailVerificationCode`, `CandidateProfile` (категория и балл теста,
предпочтения для ленты: город, форматы работы, ожидания по зарплате; контакты),
`FspAchievement` (результаты соревнований ФСП по FSP ID), `Company`, `Vacancy`, `Invitation`
(CHECK на вилку `0 < from ≤ to`). Таблицы для откликов, потребностей мэтчинга, событий
календаря и попыток тестирования появятся вместе с их сервисами.

Ленты подбора: соискатель видит только релевантные вакансии (`/vacancies/feed`), рекрутер
ищет по банку кандидатов (`/candidates`) — Elasticsearch с резервным поиском по базе, одна
объяснимая модель ранжирования (`app/services/matching.py`), лайки/пропуски для свайпов и
избранного (`vacancy_reactions`, `candidate_reactions`). Пагинация во всём API —
`page`/`perPage`. Подробности — `backend/README.md`.

Демо-данные (`app/seed`, `python -m app.seed`): 20 компаний, 97 вакансий, 124 соискателя всех
специализаций и грейдов. JSON собирает детерминированный генератор; поле `track` в фикстурах —
эталонная разметка для оценки качества подбора (подробнее — `backend/README.md`).

### Аутентификация

JWT HS256 с claims в форме Keycloak (`sub`, `email`, `realm_access.roles`, `iss`, `typ`), чтобы
позже принимать токены FSP ID (RS256 через JWKS) той же зависимостью. Пароли — Argon2id;
для несуществующего email выполняется проверка «пустого» хэша (выравнивание времени ответа).
Ошибки валидации не возвращают `input` (не эхоим пароли).

Регистрация не выдаёт токен, пока почта не подтверждена 6-значным кодом (письмо через Resend,
`RESEND_API_KEY` / `RESEND_FROM`). Код хранится как HMAC, живёт 15 минут, повторная отправка —
не чаще раза в минуту. Без ключа в development код пишется в лог API; в production отправка
без ключа завершается ошибкой.

## 4. Окружение

Единый `.env` в корне (шаблон `.env.example`): compose подставляет переменные, backend читает
`../.env` и `.env`, Vite — `envDir: '..'`. Backend падает при старте, если нет `DATABASE_URL`
или `JWT_SECRET` короче 32 символов; compose — если не заданы `POSTGRES_PASSWORD`/`JWT_SECRET`.
В браузерный бандл попадают только `VITE_*`.

## 5. CI/CD

`ci.yml` (PR, push в `main`, ручной запуск) вызывает переиспользуемые `frontend.yml` и
`backend.yml`:

- frontend: `npm ci` → format:check → lint → typecheck → test → build (артефакт `dist`);
- backend: `uv sync --frozen` → ruff check → ruff format --check → mypy → pytest;
  отдельный job поднимает PostgreSQL 17 и прогоняет `alembic upgrade head`, `alembic check`,
  `downgrade base`;
- `docker`: сборка обоих образов без публикации + `docker compose config`;
- `publish`: push в GHCR только на `main` и только если в репозитории задана переменная
  `PUBLISH_IMAGES=true` (используется встроенный `GITHUB_TOKEN`);
- `deploy`: environment `production`, выполняется только при наличии секрета
  `DEPLOY_WEBHOOK_URL`, иначе пишет notice и пропускается.

Версии зафиксированы: Node из `.nvmrc` (22), Python 3.12, uv 0.8.22, `ubuntu-24.04`,
базовые образы `node:22-alpine`, `nginx:1.29-alpine`, `python:3.12-slim`, `postgres:17-alpine`.
Права `GITHUB_TOKEN` — `contents: read`, `packages: write` только у `publish`.
В workflow нет реальных секретов: значения в job `migrations` — одноразовые для CI-контейнера.

**Подключение деплоя:** (1) выбрать хостинг; (2) завести environment `production` с
required reviewers; (3) задать `PUBLISH_IMAGES=true` и секрет `DEPLOY_WEBHOOK_URL` (или заменить
шаг на действие провайдера); (4) runtime-секреты (`JWT_SECRET`, `DATABASE_URL`) хранить на
стороне хостинга; (5) миграции запускать отдельным шагом релиза до переключения трафика.

## 6. Компромиссы

| Решение | Почему | Цена |
| ------- | ------ | ---- |
| oxlint вместо ESLint | typescript-eslint не поддерживает TypeScript 7 (проект уже был на TS 7) | нет `eslint-plugin-boundaries`; FSD-границы выражены через `no-restricted-imports` по слоям |
| Access-токен в `sessionStorage` | MVP без refresh-эндпоинта | уязвим к XSS; план — короткий access в памяти + refresh в httpOnly cookie (`/auth/refresh`) |
| 501-заглушки | фронт и бэк развиваются параллельно по контракту | часть экранов показывает «в разработке» |
| Словарь категорий в коде | ТЗ: составить из общепринятых терминов | правка требует релиза; позже — таблица и админка |
| SQLite in-memory в тестах | быстрые тесты без Docker | различия диалектов; закрыто job'ом миграций на PostgreSQL |
| `candidate`/`company` вместо `employee`/`employer` | терминология ТЗ и UI | расхождение с формулировкой задания |
| Без monorepo-тулинга | две разные экосистемы | общие типы API не генерируются автоматически |

## 7. Следующие шаги

1. Профиль кандидата и компании (CRUD) → банк кандидатов с поиском и ранжированием
   (балл тестирования, затем подтверждённые достижения ФСП).
2. Приглашения: статусы, раскрытие контактов только после `accept`, уведомления.
3. Тестирование: банк заданий по грейдам, варианты на кандидата, cooldown смены грейда.
4. Подключить домен в Resend и прописать `RESEND_API_KEY`. Дальше — refresh-токены и FSP ID.
5. Разбор PDF-резюме, объяснимый мэтчинг, календарь.
6. Генерация TS-типов из OpenAPI (`openapi-typescript`) вместо ручных DTO.
7. Наблюдаемость (Sentry/OTel), rate limiting на `/auth/*`, e2e-тесты (Playwright).

## 8. Reference analysis

Изучен `C:\Users\artem\WebstormProjects\istock-dev\web-client` (Next.js App Router, yarn +
turbo, Redux Toolkit + TanStack Query + axios, Jest, ESLint, GitLab CI, Sentry).

**Перенесено:**

- FSD-словарь слоёв (`pages/features/entities/shared`) и public API через `index.ts`;
- тонкие маршруты, делегирующие страницам (в референсе — `src/app/**/page.tsx` → модульные pages;
  у нас — `app/router/routes.tsx` → `@/pages/*`);
- выделенный «платформенный» слой инфраструктуры (`core/api`, `core/session`,
  `core/permissions`) → у нас `shared/api`, `entities/session`, ролевые guard'ы в `app/router`;
- серверное состояние через TanStack Query, сгруппированные по сущности ключи и запросы;
- `.env.example`, `.editorconfig`, `.gitattributes`, husky, многостадийный Dockerfile.

**Адаптировано:**

- В референсе FSD применён внутри каждого бизнес-модуля (`admin/`, `pdm/`, `mdm/` со своими
  `entities/features/pages/shared`) плюс много несистемных папок (`components/`, `common/`,
  `store/`) и десяток алиасов по модулям. Для небольшого продукта — один FSD-корень и единый
  алиас `@/*`.
- В референсе `import/no-cycle` выключен и границы слоёв не проверяются линтером; здесь циклы и
  межслойные импорты — ошибки линтера.
- Next.js/SSR не нужен (SPA за nginx, SEO — только лендинг) → Vite.
- Redux не нужен: глобального клиентского состояния — только сессия.
- axios заменён тонким `fetch`-клиентом с типизированной `ApiError`.
- Скрипты запуска по стендам (`STAND=test11` …) заменены env-переменными + compose.
- GitLab CI → GitHub Actions с теми же этапами (install → lint → types → test → build → docker).
- Jest → Vitest (общий конфиг с Vite, тот же алиас).
