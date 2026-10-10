---
icon: lucide/terminal
---

# Локальный запуск

Команды из корневого `README.md`. Нужны Node.js 22, Python 3.12, uv 0.8+ и Docker с Compose, если база в контейнере.

```bash
cp .env.example .env
```

Заполните `POSTGRES_PASSWORD` и `JWT_SECRET` не короче 32 символов.

## Всё в Docker

```bash
docker compose up --build
docker compose exec backend python -m app.seed
```

SPA: `http://localhost:8080`. Документация: `http://localhost:8081`. Админка: `http://localhost:8082` (поддомен `admin`, как документация на `docs`). API: `http://localhost:8000/api/docs`.

Для окна браузера в `.env` нужны `ADMIN_GATE_USERS` (`имя:пароль` через запятую), `ADMIN_GATE_SECRET` и `ADMIN_EMAIL`. Аккаунт администратора: `docker compose exec backend python -m app.admin.create_admin` (`ADMIN_PASSWORD` от 12 символов).

## По частям

```bash
docker compose up -d db
cd backend && uv sync && uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload
```

Во втором терминале: `cd frontend && npm install && npm run dev`. Сайт на `http://localhost:5173`, `/api` проксируется на `:8000`.

Повторный `python -m app.seed` заменяет демо-записи. Демо-почты: `candidate@example.com`, `employer@example.com`, `employer2@example.com`. Пароль — в `backend/README.md`.

Администратор создаётся отдельно: `ADMIN_EMAIL` и `ADMIN_PASSWORD` (от 12 символов) и `uv run python -m app.admin.create_admin`.

«Войти через Яндекс» появляется, когда в `.env` заданы `YANDEX_CLIENT_ID` и `YANDEX_CLIENT_SECRET`. Как завести приложение: [регистрация клиента](https://yandex.ru/dev/id/doc/ru/register-client). Адрес возврата для этого стенда — `http://localhost:8080/auth/yandex/callback`.

Проверки перед сдачей: во frontend `lint`, `format:check`, `typecheck`, `test`, `build`; в backend `ruff`, `mypy`, `pytest`.
