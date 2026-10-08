---
icon: lucide/terminal
---

# Local start

Commands from the root `README.md`. You need Node.js 22, Python 3.12, uv 0.8+, and Docker with Compose if the database runs in a container.

```bash
cp .env.example .env
```

Set `POSTGRES_PASSWORD` and a `JWT_SECRET` of at least 32 characters.

## Everything in Docker

```bash
docker compose up --build
docker compose exec backend python -m app.seed
```

SPA: `http://localhost:8080`. Documentation: `http://localhost:8081`. API: `http://localhost:8000/api/docs`.

## In parts

```bash
docker compose up -d db
cd backend && uv sync && uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload
```

In a second terminal: `cd frontend && npm install && npm run dev`. The site is at `http://localhost:5173`. `/api` is proxied to `:8000`.

Running `python -m app.seed` again replaces the demo rows. Demo emails: `candidate@example.com`, `employer@example.com`, `employer2@example.com`. The password is in `backend/README.md`.

An administrator is created separately: `ADMIN_EMAIL` and `ADMIN_PASSWORD` (at least 12 characters) and `uv run python -m app.admin.create_admin`.

Checks before handing work over: on the frontend `lint`, `format:check`, `typecheck`, `test`, `build`; on the backend `ruff`, `mypy`, `pytest`.
