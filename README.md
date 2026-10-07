# KADRY — платформа подбора ИТ-специалистов ФСП

Монолитный full-stack проект для кейса «ФСП, спецтрек»: банк категоризированных кандидатов
(специализация + грейд по результатам тестирования), поиск и приглашения от работодателей с
обязательной вилкой зарплаты, мэтчинг в формате свайпов, календарь, админка.

- `frontend/` — React 19 + TypeScript + Vite, Feature-Sliced Design ([README](frontend/README.md))
- `backend/` — Python 3.12, FastAPI, SQLAlchemy 2 async, PostgreSQL, Alembic ([README](backend/README.md))
- `docs/ARCHITECTURE.md` — архитектура, правила импортов, компромиссы, следующие шаги
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
docker compose up --build   # SPA: http://localhost:8080, API: http://localhost:8000/api/docs
docker compose exec backend python -m app.seed   # перезалить демо-данные (на пустой базе грузятся сами)
```

### Локально

```bash
docker compose up -d db     # или свой PostgreSQL; поправьте DATABASE_URL в .env

cd backend
uv sync
uv run alembic upgrade head
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

## Переменные окружения

Один `.env` в корне используют docker compose, backend (pydantic-settings) и Vite. Шаблон —
[`.env.example`](.env.example); `.env` в git не попадает.

| Переменная                 | Где               | Обязательна | Описание                                  |
| -------------------------- | ----------------- | ----------- | ----------------------------------------- |
| `POSTGRES_DB/USER/PASSWORD`| compose           | пароль — да | учётка БД контейнера `db`                 |
| `DATABASE_URL`             | backend           | да          | `postgresql+asyncpg://…` (в compose собирается сам) |
| `JWT_SECRET`               | backend           | да          | подпись access-токенов, ≥ 32 символов     |
| `ACCESS_TOKEN_TTL_MINUTES` | backend           | нет (30)    | срок жизни access-токена                  |
| `APP_ENV`, `LOG_LEVEL`     | backend           | нет         | `development`/`test`/`production`, уровень логов |
| `CORS_ORIGINS`             | backend           | нет         | список через запятую; пусто — CORS выключен |
| `RESEND_API_KEY`           | backend           | нет         | ключ Resend для кода подтверждения почты. Пусто — код в логе API (только не в production) |
| `RESEND_FROM`              | backend           | нет         | отправитель письма, по умолчанию `onboarding@resend.dev` |
| `SEED_USER_PASSWORD`       | backend (seed)    | нет         | пароль демо-аккаунтов `python -m app.seed`; пусто — пароль из backend/README |
| `ELASTICSEARCH_URL`        | backend           | нет         | поиск кандидатов; в compose задан, пусто — поиск по базе |
| `UPLOAD_DIR`               | backend           | нет         | каталог вложений чата, по умолчанию `/data/uploads`; в compose — том `upload-data` |
| `VITE_API_URL`             | frontend (build)  | нет         | база API, по умолчанию `/api/v1`          |
| `DEV_API_PROXY_TARGET`     | frontend (dev)    | нет         | цель прокси `/api` dev-сервера            |

## Структура

```
backend/    app/{api,core,db,models,schemas,services,repositories,dependencies}, migrations/, tests/
frontend/   src/{app,pages,widgets,features,entities,shared}, tests/
docs/       ARCHITECTURE.md
.github/    workflows/{ci,frontend,backend}.yml
.cursor/    skills для агентов (design-taste-frontend, frontend-design, ui-ux-pro-max), см. skills-lock.json
```
