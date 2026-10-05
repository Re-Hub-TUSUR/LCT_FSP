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
uv run python -m app.seed    # демо-данные (необязательно)
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
| `uv run python -m app.seed`                     | загрузить демо-данные (заменяет прежние демо-записи) |
| `uv run python -m app.seed.assessment`          | добавить стартовый банк задач и тесты на грейд (только недостающие строки) |
| `uv run python -m app.seed.generate`            | пересобрать `app/seed/data/*.json` из `app/seed/content.py` |

## Демо-данные

Все компании и люди вымышленные; почты — на зарезервированном домене `example.com`.

| Файл | Что внутри |
| ---- | ---------- |
| `app/seed/data/companies.json` | 20 компаний из разных отраслей и городов, у каждой аккаунт работодателя |
| `app/seed/data/vacancies.json` | 97 вакансий (3 черновика): все специализации словаря и все грейды, вилка зарплаты обязательна |
| `app/seed/data/candidates.json` | 124 соискателя: все 10 специализаций, грейды от стажёра до лида, 38 треков стека (Go-бэкенд, Unity, SOC…) |

Граничные случаи, на которых стоит проверять ленты и поиск: соискатели без истории ФСП (ТЗ:
обязательный случай), с привязанным FSP ID, но без результатов, без пройденного теста
(`assessmentScore = null`: грейд заявлен самим кандидатом), скрытые от работодателей
(`is_visible_to_employers = false`), вакансии-черновики (`published_at = null`).

**Аккаунты.** Пароль у всех демо-аккаунтов один: `kadry-demo-2026` (на публичном стенде задайте
свой через `SEED_USER_PASSWORD`).

- `candidate@example.com` — соискатель: Middle Python-разработчик из Москвы с результатами ФСП;
- `employer@example.com` — работодатель, компания «ПэйФлоу»;
- остальные работодатели — `recruiter@<key>.example.com`, соискатели — поле `email` в
  `candidates.json`.

**Как устроено.**

- JSON собирает детерминированный генератор (`generate.py`, фиксированный seed) из курируемого
  контента (`content.py`): треки специальностей со стеком и формулировками, города, вузы,
  компании и планы вакансий. Правьте `content.py` и пересобирайте JSON; тест сверяет файлы с
  генератором.
- Даты хранятся как «дней назад» и отсчитываются от момента загрузки, поэтому демо не устаревает.
- Id записей — UUIDv5 от ключа фикстуры: повторная загрузка удаляет прежние демо-записи
  (вместе с приглашениями к ним) и создаёт их с теми же id, ссылки не ломаются.
- Поле `track` (например, `go-backend`) в БД не пишется: это эталонная разметка для оценки
  качества подбора — пары «вакансия — кандидат» одного трека и соседнего грейда релевантны.
- С `APP_ENV=production` загрузка требует флага `--force`; если демо-почта уже занята чужим
  аккаунтом, загрузка останавливается без изменений.

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
  seed/          демо-данные: JSON, генератор, загрузчик (`python -m app.seed`)
  main.py        create_app()
migrations/      Alembic (async), URL берётся из настроек
tests/
```

## Статус доменов

Реализованы: health, auth (регистрация/вход), users/me, categories/dictionary, admin/users.
Остальные эндпоинты (кандидаты, компании, вакансии, приглашения, отклики, мэтчинг, календарь,
тестирование) имеют финальный контракт (пути, схемы, роли) и возвращают `501 not_implemented`
до реализации сервисов. Ролевые проверки работают уже сейчас.
