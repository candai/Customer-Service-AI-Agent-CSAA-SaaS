# Luron

A full-stack application implementing user accounts, conversational/agent features, analytics, billing hooks, and webhook integrations — built as a Python backend with a TypeScript/JavaScript frontend and containerized deployment support.

## What this is
Luron is an integrated system for running conversational agents and managing related user and billing workflows. It provides account management, agent/conversation handling, analytics, billing-related endpoints, and webhook support to integrate with external services.

### Stack
- **Language(s):** Python (backend), TypeScript / JavaScript / CSS / HTML (frontend)
- **Framework / runtime:** Python web app (Django-style layout; `manage.py` present)
- **Datastores & runtime services:** SQLite (`db.sqlite3`) for local persistence, Redis (snapshot `dump.rdb`) for ephemeral data/cache
- **Containerization & deployment:** Docker (Dockerfile, `entrypoint.sh`), Railway configuration (`railway.toml`)
- **Notable tooling:** `requirements.txt` (Python deps), pytest-style tests

## Features implemented
- User accounts and authentication scaffolding (backend `apps/accounts`)
- Agent management and conversational features (backend `apps/agents`, `apps/conversations`)
- Analytics collection and reporting surfaces (backend `apps/analytics`)
- Billing integration and billing-related endpoints (backend `apps/billing`)
- Webhook receiver/handler endpoints for external integrations (backend `apps/webhooks`)
- Background services structure (backend `services`, `core`)
- Static asset handling and web UI support (backend `staticfiles`)
- Basic test coverage and broadcast test (`test_broadcast.py` + `tests/`)
- Containerized development / production support (Dockerfile + entrypoint script)
- Local/dev-friendly data files included for quick demos (`db.sqlite3`, `dump.rdb`)

## How it's organized
Top-level layout (annotated):

```
README.progressplan.md/    Planning docs and technical report (progress plan, phases)
backend/                   Python backend (Django-style)
  .env                    environment template (sensitive values omitted in repo)
  Dockerfile              container build file for backend
  entrypoint.sh           container entrypoint script
  requirements.txt        Python dependencies
  manage.py               Django-style management script (app entrypoints)
  db.sqlite3              local SQLite database (development/demo)
  dump.rdb                Redis dump file (snapshot)
  apps/
    accounts/             user account models, views, auth
    agents/               agent definitions and management
    analytics/            data collection & reporting code
    billing/              billing endpoints & integrations
    conversations/        conversation/chat models and handlers
    webhooks/             webhook receivers and handlers
  core/                   core application utilities and shared logic
  services/               background services / integrations
  staticfiles/            served static assets for the backend UI
  tests/                  automated tests
frontend/                  Frontend application (TypeScript/JS/CSS/HTML)
.claude/                   project metadata / assistant config (internal)
.vscode/                    editor settings
.gitignore
```

How it fits together:
- The backend (Python) exposes HTTP endpoints for accounts, agents/conversations, analytics, billing, and webhooks. It owns persistence (SQLite for demo) and relies on Redis for ephemeral state or pub/sub.
- The frontend is a TypeScript/JavaScript-based UI that talks to the backend APIs and serves the user-facing experience (assets are kept under `frontend/` and `backend/staticfiles` for production serving).
- Containerization (Dockerfile + `entrypoint.sh`) and Railway config make it straightforward to run the app locally or deploy to platforms that accept Docker images.

## How to run it (shortest path)
Backend (local, development):

```bash
# from repo root
cd backend

# create a venv and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# apply migrations (if using Django ORM)
python manage.py migrate

# run dev server
python manage.py runserver
```

Backend (Docker):

```bash
# build and run backend container
docker build -t luron-backend ./backend
docker run -e DJANGO_SETTINGS_MODULE=... -p 8000:8000 luron-backend
```

Frontend (typical):

```bash
cd frontend
# install deps (npm / yarn / pnpm depending on project)
npm install
# dev server
npm run dev
# or build for production
npm run build
```

Notes:
- Environment variables and secrets should be set from `.env` before running in non-demo environments.
- The repository contains `railway.toml` for Railway deployment hints and an `entrypoint.sh` to help container lifecycle management.
- For quick demos the repository includes `db.sqlite3` and `dump.rdb`; in production replace these with managed Postgres/Redis instances and update settings.

## Tests
Run backend tests:

```bash
cd backend
pytest
# or
python manage.py test
```

## Contributing
- Follow the existing app layout under `backend/apps/` when adding new domain areas.
- Add unit tests under `backend/tests/` or the app-specific `tests` packages.
- Keep environment secrets out of the repo (use `.env` or CI secret management).

## Try asking
- How are conversations persisted and where is the conversation model defined? (look in backend/apps/conversations)
- Where is agent configuration and scheduling logic implemented? (look in backend/apps/agents and backend/services)
- Which endpoints support webhooks and what event formats do they expect? (check backend/apps/webhooks and the technical_report.MD in README.progressplan.md)
