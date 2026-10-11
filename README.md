# KADRY — платформа подбора ИТ-специалистов ФСП

Монолитный full-stack проект для кейса «ФСП, спецтрек»: банк категоризированных кандидатов
(специализация + грейд по результатам тестирования, результаты ФСП), поиск и приглашения от
работодателей с обязательной вилкой зарплаты, ленты подбора с фильтрами и сохранёнными поисками,
мэтчинг в формате свайпов, чат, календарь, резюме в PDF, админка на отдельном поддомене, вход
по почте или через Яндекс ID, интеграция с внешними ATS, справочник городов (GeoNames).

- `frontend/` — React 19 + TypeScript + Vite, Feature-Sliced Design ([README](frontend/README.md))
- `backend/` — Python 3.12, FastAPI, SQLAlchemy 2 async, PostgreSQL, Alembic ([README](backend/README.md))
- [`search.md`](search.md) — как работает поиск: кандидатов для работодателей и вакансий для соискателей
- `docs/ARCHITECTURE.md` — архитектура, правила импортов, компромиссы, следующие шаги
- `docs-zensical/` — продуктовая и инженерная документация на [Zensical](https://zensical.org/) (RU/EN). В Docker она на `http://localhost:8081`; отдельно — `pip install zensical && zensical serve` из этой папки
- `.github/workflows/` — CI (проверки, Docker-сборка, опциональная публикация и деплой)

## Требования

| Инструмент | Версия                         |
| ---------- | ------------------------------ |
| Node.js    | 22 LTS (`.nvmrc`)              |
| Python     | 3.12 (`backend/.python-version`) |
| uv         | 0.8+                           |
| Docker     | 24+ с Compose v2 (опционально) |

## Быстрый старт

```bash
cp .env.example .env        # заполните POSTGRES_PASSWORD и JWT_SECRET (≥ 32 символов)
```

### Всё в Docker

```bash
docker compose up --build   # SPA: http://localhost:8080, документация: http://localhost:8081, админка: http://localhost:8082, API: http://localhost:8000/api/docs
docker compose exec backend python -m app.seed   # перезалить демо-данные (на пустой базе грузятся сами)
```

### Локально

```bash
docker compose up -d db     # или свой PostgreSQL; поправьте DATABASE_URL в .env

cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.seed.cities --if-missing  # справочник городов GeoNames (нужен фильтрам по городу)
uv run python -m app.seed                # демо-данные (см. ниже)
uv run uvicorn app.main:app --reload     # http://localhost:8000

cd ../frontend
npm install
npm run dev                               # http://localhost:5173 (/api → :8000)
```

### Демо-данные

`python -m app.seed` загружает вымышленные данные: 20 компаний, 97 вакансий (3 черновика) и
124 соискателя всех специализаций и грейдов — с результатами ФСП и без, с пройденным тестом и
без. Повторный запуск заменяет демо-записи, не дублируя их. Контейнер при старте грузит их
только в пустую базу, поэтому после изменений в демо-данных перезалейте их: `python -m app.seed`.
Демо-аккаунты: `candidate@example.com` (соискатель), `employer@example.com` и
`employer2@example.com` (работодатели, компании «ПэйФлоу» и «Северный код»); пароль и остальные
учётки — в [backend/README.md](backend/README.md#демо-данные).

## Проверки

```bash
# frontend
cd frontend && npm run lint && npm run format:check && npm run typecheck && npm test && npm run build
# backend
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

Pre-commit (husky + lint-staged) прогоняет oxlint и prettier по изменённым frontend-файлам.
Правила, как не ломать CI (для людей и ИИ-агентов), — в [ci_rules.md](ci_rules.md).

## Переменные окружения

Один `.env` в корне используют docker compose, backend (pydantic-settings) и Vite. Шаблон —
[`.env.example`](.env.example); `.env` в git не попадает.

| Переменная                 | Где               | Обязательна | Описание                                  |
| -------------------------- | ----------------- | ----------- | ----------------------------------------- |
| `POSTGRES_DB/USER/PASSWORD/PORT` | compose     | пароль — да | учётка и порт БД контейнера `db`          |
| `DATABASE_URL`             | backend           | да          | `postgresql+asyncpg://…` (в compose собирается сам) |
| `JWT_SECRET`               | backend           | да          | подпись access-токенов, ≥ 32 символов     |
| `ACCESS_TOKEN_TTL_MINUTES` | backend           | нет (30)    | срок жизни access-токена                  |
| `APP_ENV`, `LOG_LEVEL`     | backend           | нет         | `development`/`test`/`production`, уровень логов |
| `CORS_ORIGINS`             | backend           | нет         | список через запятую; пусто — CORS выключен |
| `RESEND_API_KEY`           | backend           | нет         | ключ Resend для кода подтверждения почты. Пусто — код в логе API (только не в production) |
| `RESEND_FROM`              | backend           | нет         | отправитель письма, по умолчанию `onboarding@resend.dev` |
| `SEED_USER_PASSWORD`       | backend (seed)    | нет         | пароль демо-аккаунтов `python -m app.seed`; пусто — пароль из backend/README |
| `ELASTICSEARCH_URL`        | backend           | нет         | поиск кандидатов; в compose задан, пусто — поиск по базе ([search.md](search.md#два-движка-elasticsearch-и-база)) |
| `SAVED_SEARCH_ALERT_MINUTES` | backend         | нет (5)     | как часто проверять сохранённые поиски и слать уведомления о новых результатах; `0` — выключено |
| `BROKER_URL`               | backend           | нет         | брокер публикации/подписки живых уведомлений (`app/services/broker.py`); пусто — в памяти одного процесса, `redis://host:6379/0` — Redis pub/sub для нескольких воркеров |
| `ONLINECOMPILER_API_KEY`   | backend           | нет         | запуск кода в тестировании ([OnlineCompiler](https://onlinecompiler.io/docs)); пусто — вопросы работают, задачи на код отвечают 503 |
| `FSP_ID_MODE`              | backend           | нет (`mock`)| FSP ID и реестр ФСП: `mock` — эмуляция внутри API, `keycloak` — настоящие системы; остальные `FSP_ID_*` и `FSP_REGISTRY_URL` — [docs/FSP_INTEGRATION.md](docs/FSP_INTEGRATION.md) |
| `UPLOAD_DIR`               | backend           | нет         | каталог вложений чата, по умолчанию `/data/uploads`; в compose — том `upload-data` |
| `ROUTERAI_API_KEY`         | backend           | нет         | ключ [RouterAI](https://routerai.ru/settings/keys) для распознавания резюме и ИИ-собеседования; пусто — поля заполняются вручную, грейд подтверждается без собеседования |
| `RESUME_PARSER_MODEL`      | backend           | нет         | модель распознавания резюме, по умолчанию `yandex/aliceai-llm-flash` (только российские модели) |
| `INTERVIEW_MODEL`          | backend           | нет         | модель ИИ-собеседования по коду после теста, по умолчанию `yandex/aliceai-llm-flash` |
| `ATS_MODE`                 | backend           | нет (`mock`)| интеграция с ATS: `mock` — демо внутри процесса, `fixture` — JSON-провайдер; `ATS_POLL_SECONDS` — интервал фонового опроса, `0` — выключен |
| `YANDEX_CLIENT_ID/SECRET`  | backend           | нет         | вход через Яндекс ID; пустой id скрывает кнопку и закрывает `/auth/yandex/*`. `YANDEX_REDIRECT_URI` — адрес возврата, регистрация приложения — [docs-zensical/docs/ru/technical/local-start.md](docs-zensical/docs/ru/technical/local-start.md) |
| `ADMIN_GATE_USERS/SECRET`  | compose + backend | для поддомена `admin` | браузерный пароль админ-поддомена (`имя:пароль` через запятую) и общий секрет nginx↔API |
| `ADMIN_EMAIL/PASSWORD`     | backend           | для поддомена `admin` | аккаунт, который открывает поддомен `admin` после пароля; создаётся `python -m app.admin.create_admin` |
| `VITE_API_URL`             | frontend (build)  | нет         | база API, по умолчанию `/api/v1`          |
| `DEV_API_PROXY_TARGET`     | frontend (dev)    | нет         | цель прокси `/api` dev-сервера            |

## Структура

```
backend/    app/{api,core,db,models,schemas,services,repositories,dependencies}, migrations/, tests/
frontend/   src/{app,pages,widgets,features,entities,shared}, tests/
docs/       ARCHITECTURE.md, FSP_INTEGRATION.md, ADMIN.md
search.md   как работает поиск (кандидаты и вакансии)
ci_rules.md правила, как не ломать CI (для людей и ИИ-агентов)
docs-zensical/  сайт документации (BRD, use cases, user flows, инженерия)
.github/    workflows/{ci,frontend,backend}.yml
.cursor/    skills для агентов (design-taste-frontend, frontend-design, ui-ux-pro-max), см. skills-lock.json
```
