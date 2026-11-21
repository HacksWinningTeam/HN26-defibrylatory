# AI Agent Rules

Shared workspace rules for **Antigravity** and **Claude Code** on this hackathon template (`CLAUDE.md` imports this file via `@AGENTS.md`).

## Hackathon Project Brief (Fill In At Kickoff)

- **Problem & Demo Goal:** `<1-2 sentences describing what the app proves in the demo>`
- **Primary User Flow:** `<step-by-step happy path from UI to DB and back>`
- **Core Models & API Endpoints:** `<key models and /api/... routes>`
- **Out of Scope for MVP:** `<features intentionally skipped during the hackathon>`
- **Deadline / Demo / Code Freeze:** `<YYYY-MM-DD HH:MM submission deadline, demo slot, code-freeze time>`

## Stack & Repository Map

- `backend/`: Python 3.12, Django 5.2 LTS, Django REST Framework, `drf-spectacular`, `psycopg[binary]`, Gunicorn + WhiteNoise (`prod`), managed with **`uv`** (`backend/pyproject.toml`).
- `frontend/`: Node 22, Next.js 16 (App Router + `output: "standalone"`), React 19, TypeScript, Tailwind CSS v4, ESLint 9 flat config, managed with **`npm`** (`frontend/package.json`).
- `compose.yaml`: Local hot-reload development (`db`, `backend`, `frontend`).
- `compose.prod.yaml`: Single-port production stack (`target: prod`) for Hetzner.
- `.github/workflows/deploy.yml`: Automatic Hetzner CI/CD pipeline triggered on push to `main`.
- `Makefile` & `.env.example`: Standard dev/verify commands and environment variable template.

## Hackathon Engineering Principles

- **Ship vertical slices:** Implement DB model -> DRF serializer/view/tests -> Next.js UI end-to-end before adding polish.
- **Keep it simple:** Prefer direct Django/DRF and Next.js patterns over speculative abstractions. Do not add unrequested infrastructure (Redis, Celery, auth systems, theme toggles) unless asked.
- **No silent fake data:** Never silently stub production API responses; clearly label any explicit demo/seed data.

## Non-Negotiable Architecture Invariants

- **Single-port proxy:** In prod each app exposes exactly one host port, chosen from the `3000–3100` range (`FRONTEND_PORT`, default `3000`). Browser requests and links use same-origin paths (`/api/...`, `/admin/`, `/static/...`) rewritten by `frontend/src/proxy.ts` with `skipTrailingSlashRedirect: true` in `frontend/next.config.ts`. Keep `NEXT_PUBLIC_API_URL` empty by default, never hardcode `http://localhost:8000` (or any backend origin) in browser-executed code — the only allowed fallback is the server-side one inside `getApiBaseUrl()` in `frontend/src/lib/api.ts`, and never add deprecated `middleware.ts`.
- **Internal-only prod DB & backend:** Only `frontend` publishes `FRONTEND_PORT` in `compose.prod.yaml`. Keep `localhost,127.0.0.1,backend` in `DJANGO_ALLOWED_HOSTS` so Next.js SSR (`API_INTERNAL_URL=http://backend:8000`) and healthchecks work.
- **Docker paths:** Keep PostgreSQL 18 mounted at `/var/lib/postgresql` (never `/var/lib/postgresql/data`) and the `uv` virtualenv at `/opt/venv` (never `/app/.venv`).
- **Git & secrets:** Never commit `.env` or real secrets. Keep `/lib/` and `/lib64/` anchored in `.gitignore` so `frontend/src/lib/` stays tracked. Mirror any new env var in `.env.example`, `compose.yaml`, and `compose.prod.yaml`.
- **UI baseline:** Follow the **WCAG 2.2 AA** light baseline; do not add dark mode or theme switchers unless explicitly requested.

## Testing, Verification & Quality Bar

- **Write unit tests:** Add or update `pytest` unit/API tests for every new or changed backend model, serializer, or endpoint (and unit tests for frontend logic if a test runner is configured).
- **Always verify before finishing:** Run all checks and report what passed or could not run:
  - `make test` (`docker compose exec -T backend pytest`)
  - `make lint` (`ruff check .`, `npm run typecheck`, `npm run lint`)
  - `make schema-check` (`python manage.py spectacular --validate --fail-on-warn`)
  - `make migrations-check` (`python manage.py makemigrations --check --dry-run`)
  - `make build-prod` (production Docker images, including `next build`) whenever frontend code, Dockerfiles, dependencies, or Compose files changed, and always at the end of a milestone — a push to `main` deploys immediately, so a broken prod build breaks the live demo.
- **Stack must be running:** All `make` checks use `docker compose exec`. If the containers are down, start them with `make up-d` first; if a check still cannot run, say so explicitly instead of reporting it as passed.- **Common workflow commands:** `make up` / `make up-d`, `make makemigrations`, `make migrate`, and `docker compose up -V --build` whenever `frontend/package.json` changes.

## CI/CD Deployment & Git Policy

- **Automatic deploy on `main`:** Deployment to the Hetzner production server is **automatic** via GitHub Actions CI/CD (`.github/workflows/deploy.yml`) whenever code is pushed to `main` (it syncs files excluding `.git` and `.env` and runs `docker compose -f compose.prod.yaml up -d --build --remove-orphans`).
- **Never run `git push`:** The user pushes code manually to control when live deployments happen. Do not push branches or tags automatically.
- **Deploy sync safety:** Preserve `--exclude='.git' --exclude='.env'` and the `.git` cleanup in `.github/workflows/deploy.yml` so read-only `.git/objects/*` files do not cause permission errors and the server's `.env` stays intact. Keep non-root `prod` stages in both Dockerfiles and `DJANGO_SECRET_KEY` required in `compose.prod.yaml`; `db` and `backend` get no `ports:` mapping in prod.
- **Validate Compose edits:** `docker compose config --quiet` and `DJANGO_SECRET_KEY=ci-check docker compose -f compose.prod.yaml config --quiet`.
- **Local checkpoint commits:** After a task is `VERIFIED`, offer a local commit (`TXX: <title>`) and commit only with the user's OK. Never commit `.env` or secrets.
- **No destructive resets:** Never run `docker compose down -v` or drop databases/volumes without explicit user confirmation. Keep the repo ready to build cleanly under `compose.prod.yaml`.

## Scoped Guides

When working from the repository root, read the matching scoped guide before editing files inside that service:
- Backend (`backend/`): read `backend/AGENTS.md`
- Frontend (`frontend/`): read `frontend/AGENTS.md`

## Development Workflow & Project Memory (`docs/`)

- **Inputs & living specs:** Raw organizer PDFs (`docs/inputs/organizer-brief/`), UI assets (`docs/inputs/ui/`), and rough user notes (`docs/inputs/my-notes.md`) are distilled into `docs/01-brief.md`–`docs/05-plan.md` and `docs/tasks/TXX-*.md` (see `docs/README.md`).
- **Read before coding:** Before working on any task, read `docs/04-decisions.md`, `docs/05-plan.md`, and the active `docs/tasks/TXX-*.md`.
- **Task status (single source of truth):** A task's state lives only in its `Status` field (`docs/tasks/TXX-*.md`), mirrored in the `docs/05-plan.md` table: `TODO` -> (`DESIGN_REVIEW` -> `DESIGN_READY`, UI tasks only) -> `IN_PROGRESS` -> `VERIFIED`, or `CANCELLED`. `UI Design Required` is just `Yes` / `No`.
- **Per-task UI design gate:** For UI-facing tasks (`UI Design Required: Yes`), design the task's `## UI Design (Per-Task)` section (`hackathon-ui-design`, sets `DESIGN_REVIEW`) and get the user's explicit approval (sets `DESIGN_READY`) before writing UI code. `DESIGN_REVIEW` is never permission to implement.
- **User-owned gates:** Only the user can approve a design (`DESIGN_READY`) or confirm manual verification (`VERIFIED`). Never set these statuses without the user's explicit confirmation in the conversation.
- **Timestamps:** Get the current date/time from the shell (`date '+%Y-%m-%d %H:%M'`) for `DEC-XXX` entries, approvals, and notes — never guess.
- **Mid-hackathon updates:** Whenever requirements, feedback, or plans change, record a numbered `DEC-XXX` in `docs/04-decisions.md` and update affected docs/tasks (`hackathon-update-plan`).
- **Workflow skills:** `.agents/skills/` (symlinked to `.claude/skills/`): `hackathon-kickoff`, `hackathon-plan`, `hackathon-ui-design`, `hackathon-run-task`, `hackathon-update-plan`.
- **Guided workflow routing:** When the user says *"let's start"*, *"continue"*, *"what's next?"*, or adds new requirements without naming a skill, check these rules **in order** and follow the first match:
  1. The message (or new entries in `docs/inputs/my-notes.md`) brings new requirements, mentor feedback, or scope/design changes -> run `hackathon-update-plan` first, then continue routing.
  2. `docs/01-brief.md` still has template placeholders -> run `hackathon-kickoff`.
  3. `docs/05-plan.md` still has example tasks (`<Example: ...>`) -> run `hackathon-plan`.
  4. Pick the next task in `docs/05-plan.md` order (an `IN_PROGRESS` task first, otherwise the first `TODO` / `DESIGN_REVIEW` / `DESIGN_READY` task whose `Depends On` are all `VERIFIED`), then:
     - `IN_PROGRESS` -> resume `hackathon-run-task`.
     - `DESIGN_REVIEW` -> re-present its UI design and ask for approval (`hackathon-ui-design`, step 5); do not implement.
     - `TODO` with `UI Design Required: Yes` -> run `hackathon-ui-design`.
     - `TODO` with `UI Design Required: No`, or `DESIGN_READY` -> run `hackathon-run-task`.
  Always close each stage by stating the next stage and waiting for user approval before proceeding.
