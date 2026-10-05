# KADRY — backend

FastAPI + SQLAlchemy 2 (async) + PostgreSQL. Архитектура и правила слоёв — в [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).

## Требования

- Python 3.12 (`.python-version`)
- [uv](https://docs.astral.sh/uv/) 0.8+
- PostgreSQL 17 (локально или `docker compose up db`)

## Запуск

```bash
cp ../.env.example ../.env   # один .env на весь репозиторий; заполните JWT_SECRET
uv sync                      # зависимости + dev-группа
uv run alembic upgrade head  # миграции
uv run uvicorn app.main:app --reload
```

Swagger: <http://localhost:8000/api/docs>, OpenAPI: `/api/openapi.json`.

Сгенерировать секрет: `uv run python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## Команды

| Команда                                         | Что делает                        |
| ----------------------------------------------- | --------------------------------- |
| `uv run ruff check .` / `uv run ruff check --fix .` | линтер                        |
| `uv run ruff format .` / `--check`              | форматирование                    |
| `uv run mypy`                                   | строгая проверка типов            |
| `uv run pytest`                                 | тесты (SQLite in-memory, без БД)  |
| `uv run alembic revision --autogenerate -m "…"` | новая миграция (проверяйте руками) |

## Структура

```
app/
  core/          config (env), security (JWT, Argon2), errors (единый формат), logging
  db/            Base, mixins, engine/session
  models/        ORM-модели
  schemas/       Pydantic-контракты API (camelCase на проводе)
  repositories/  доступ к данным, без бизнес-правил
  services/      бизнес-логика
  dependencies/  FastAPI DI: сессия, текущий пользователь, ролевые guard'ы
  api/routes/    HTTP-роутеры по доменам → api/router.py (/api/v1)
  main.py        create_app()
migrations/      Alembic (async), URL берётся из настроек
tests/
```

## Статус доменов

Реализованы: health, auth (регистрация/вход), users/me, categories/dictionary, admin/users.
Остальные эндпоинты (кандидаты, компании, вакансии, приглашения, отклики, мэтчинг, календарь,
тестирование) имеют финальный контракт (пути, схемы, роли) и возвращают `501 not_implemented`
до реализации сервисов. Ролевые проверки работают уже сейчас.
