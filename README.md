# Django + DRF + Next.js Docker Template

A Docker-first full-stack application template combining **Django 5.2 LTS**, **Django REST Framework**, **`drf-spectacular`** (OpenAPI 3, Swagger UI, ReDoc), **PostgreSQL 18**, and **Next.js 16** (App Router, React 19, TypeScript, Tailwind CSS v4).

## Stack & Tooling

- **Backend**: Python 3.12, Django 5.2 LTS, DRF, `drf-spectacular`, `django-cors-headers`, `django-environ`, `psycopg[binary]`, Gunicorn + WhiteNoise (`prod` target), managed with **`uv`**
- **Database**: PostgreSQL 18 (`postgres:18-alpine`)
- **Frontend**: Node 22, Next.js 16 (App Router + `output: "standalone"`), React 19, TypeScript, Tailwind CSS v4, ESLint 9 flat config, managed with **`npm`**
- **Orchestration**: Docker Compose (`compose.yaml`) with multi-stage `dev` and `prod` Dockerfile targets

## Project Structure

```text
.
├── .agents/skills/          # Shared Antigravity + Claude Code workflow skills
├── .claude/
│   ├── rules/
│   │   └── deploy-and-docker.md # Path-scoped Docker/CI guardrails for Claude Code
│   └── skills/              # Symlinks pointing to ../../.agents/skills/*
├── .github/workflows/
│   └── deploy.yml           # Self-hosted Hetzner deploy on push to main
├── docs/
│   ├── inputs/              # Organizer PDFs, UI sketches/assets, and my-notes.md
│   ├── tasks/               # Per-task specs, UI designs & verification checklists
│   ├── 01-brief.md – 05-plan.md # Distilled brief, UI system, architecture, DEC log, roadmap
│   └── README.md            # Step-by-step hackathon workflow guide
├── backend/
│   ├── apps/core/           # Healthcheck API endpoint, OpenAPI schema & pytest suite
│   ├── config/              # Django settings, URLs (admin, API, Swagger, ReDoc), ASGI/WSGI
│   ├── AGENTS.md            # Backend rules (Django, DRF, uv, pytest, ruff)
│   ├── CLAUDE.md            # Lazy-loaded adapter importing backend/AGENTS.md
│   ├── Dockerfile           # Multi-stage uv build (dev + non-root gunicorn prod)
│   ├── entrypoint.sh        # Optional migration runner on container startup
│   ├── manage.py
│   └── pyproject.toml       # Dependencies, pytest, and ruff configuration
├── frontend/
│   ├── public/              # Static assets copied into Next.js standalone image
│   ├── src/app/             # App Router pages & WCAG 2.2 AA baseline light layout
│   ├── src/components/      # Interactive API healthcheck client component
│   ├── src/lib/api.ts       # SSR-aware API client (internal DNS vs same-origin proxy)
│   ├── src/proxy.ts         # Next.js 16 proxy forwarding /api, /admin, /static to Django
│   ├── AGENTS.md            # Frontend rules (Next.js 16, Tailwind v4, WCAG 2.2 AA)
│   ├── CLAUDE.md            # Lazy-loaded adapter importing frontend/AGENTS.md
│   ├── Dockerfile           # Multi-stage npm build (dev + standalone prod)
│   ├── eslint.config.mjs    # ESLint 9 flat config
│   ├── next.config.ts
│   ├── postcss.config.mjs
│   └── tsconfig.json
├── .env.example
├── AGENTS.md                # Shared root rules for Antigravity & Claude Code
├── CLAUDE.md                # Root adapter importing @AGENTS.md
├── compose.yaml             # Local hot-reload development stack
├── compose.prod.yaml        # Single-port production stack (ports 3000-3100)
└── Makefile
```

## Quick Start

1. **(Optional) Copy environment configuration:**

   ```bash
   cp .env.example .env
   ```

   All services have safe local development defaults in `compose.yaml`, so `docker compose up --build` works even without a `.env` file.

2. **Build and start all containers:**

   ```bash
   docker compose up --build
   # or: make up
   ```

3. **Open the application and docs (single-port via Next.js proxy or direct backend in dev):**

| Service / Endpoint | Single-Port URL (Dev & Prod) | Direct Backend URL (Dev Only) | Notes |
| --- | --- | --- | --- |
| Next.js Frontend | http://localhost:3000 | — | Server-side + browser API healthcheck UI |
| Healthcheck API | http://localhost:3000/api/health/ | http://localhost:8000/api/health/ | Verifies Django + PostgreSQL (`SELECT 1`) |
| Swagger UI | http://localhost:3000/api/docs/ | http://localhost:8000/api/docs/ | Interactive OpenAPI 3 UI (`drf-spectacular`) |
| ReDoc | http://localhost:3000/api/redoc/ | http://localhost:8000/api/redoc/ | API reference UI (`drf-spectacular`) |
| OpenAPI Schema | http://localhost:3000/api/schema/ | http://localhost:8000/api/schema/ | Raw OpenAPI 3 schema |
| Django Admin | http://localhost:3000/admin/ | http://localhost:8000/admin/ | Admin interface (`make createsuperuser`) |

## Container Networking (SSR, Proxy & Browser)

Each app exposes only **one public port** (`FRONTEND_PORT`, default `3000`) in production via Next.js 16 proxying:

- **`API_INTERNAL_URL=http://backend:8000`**: Used inside Docker by both Next.js Server Components (`src/lib/api.ts`) and Next.js 16's network-boundary proxy (`src/proxy.ts` + `skipTrailingSlashRedirect: true` in `next.config.ts`), which forwards `/api/*`, `/admin/*`, and `/static/*` requests to Django over the internal Docker network.
- **`NEXT_PUBLIC_API_URL=` (empty by default)**: Keeps browser requests and documentation links same-origin (`/api/...`, `/admin/`), avoiding cross-origin issues and keeping PostgreSQL and Django unexposed in `compose.prod.yaml`. Set `NEXT_PUBLIC_API_URL` only if you host Django on a separate public origin.

## Common Workflows

Using `Makefile` (or the equivalent `docker compose` commands):

- **Run migrations / create migrations:**
  ```bash
  make makemigrations
  make migrate
  ```
- **Create a Django admin superuser:**
  ```bash
  make createsuperuser
  ```
- **Run backend tests (`pytest`):**
  ```bash
  make test
  ```
- **Run linters & typechecks (`ruff`, `tsc`, `eslint`):**
  ```bash
  make lint
  ```
- **Validate the OpenAPI schema with zero warnings:**
  ```bash
  make schema-check
  ```
- **Update dependencies:**
  - Backend: edit `backend/pyproject.toml`, rebuild (`docker compose up --build backend`), or generate a lockfile inside the container with `docker compose run --rm backend uv lock`.
  - Frontend: update `frontend/package.json` (or run `npm install <pkg>` inside `frontend/`), then renew the anonymous `node_modules` volume with:
    ```bash
    docker compose up -V --build
    ```

## AI Agent Rules (Antigravity & Claude Code)

Shared hackathon instructions live in [`AGENTS.md`](AGENTS.md) (with scoped guides in [`backend/AGENTS.md`](backend/AGENTS.md) and [`frontend/AGENTS.md`](frontend/AGENTS.md)) as a single source of truth:

- **Antigravity** automatically discovers `AGENTS.md` files from the workspace up to the repository root.
- **Claude Code** loads [`CLAUDE.md`](CLAUDE.md) (`@AGENTS.md`) at startup, lazy-loads [`backend/CLAUDE.md`](backend/CLAUDE.md) and [`frontend/CLAUDE.md`](frontend/CLAUDE.md) when touching those folders, and applies [`.claude/rules/deploy-and-docker.md`](.claude/rules/deploy-and-docker.md) when editing Docker/CI files.
- **Hackathon kickoff:** Fill in the short `Hackathon Project Brief` at the top of [`AGENTS.md`](AGENTS.md) before generating features so both tools share the same MVP scope, test requirements (`make test`, `make lint`, `make schema-check`), and manual-push deployment policy.

## Hackathon Workflow

A structured, spec-driven workflow lives in [`docs/README.md`](docs/README.md) with 5 shared skills in `.agents/skills/` (symlinked to `.claude/skills/`):

1. **Inputs:** Put organizer PDF(s) in `docs/inputs/organizer-brief/`, UI sketches/assets in `docs/inputs/ui/`, and rough notes in [`docs/inputs/my-notes.md`](docs/inputs/my-notes.md).
2. **Kickoff (`hackathon-kickoff`):** Distill raw PDFs and notes into [`docs/01-brief.md`](docs/01-brief.md), lightweight [`docs/02-ui-system.md`](docs/02-ui-system.md), and `DEC-001` in [`docs/04-decisions.md`](docs/04-decisions.md).
3. **System Plan (`hackathon-plan`):** Design [`docs/03-architecture.md`](docs/03-architecture.md) and split the MVP into verifiable vertical-slice tasks in [`docs/05-plan.md`](docs/05-plan.md) and `docs/tasks/TXX-*.md`.
4. **Per-Task UI Design & Implementation (`hackathon-ui-design` → `hackathon-run-task`):** Before each UI-facing task `TXX`, design its screen layout, states, API contract, and WCAG 2.2 AA checks in `docs/tasks/TXX-*.md`, get approval, then implement code + unit tests and run `make test`, `make lint`, `make schema-check`, plus manual verification.
5. **Mid-Hackathon Changes (`hackathon-update-plan`):** Whenever new info or pivots arrive, log a numbered `DEC-XXX` in [`docs/04-decisions.md`](docs/04-decisions.md) and propagate updates across affected docs and tasks.

## Deploying to Hetzner (GitHub Actions)

Pushes to `main` trigger [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) on a `self-hosted` runner, syncing the repository to `/home/github/apps/<repo-name>` (excluding `.git` and `.env`) and running `docker compose -f compose.prod.yaml up -d --build --remove-orphans`.

- **Single open port per app (`3000–3100`):** In `compose.prod.yaml`, only `frontend` publishes a host port (`FRONTEND_PORT`, default `3000`); `db` and `backend` stay private on the Docker network and are reached via Next.js's proxy (`src/proxy.ts`). Each repository deployed to the same Hetzner host can set its own unique port in `3000–3100` via `FRONTEND_PORT`.
- **One-time server `.env` setup:** Because the deploy step excludes `.git` and `.env` when syncing to `$APP_DIR`, an existing `/home/github/apps/<repo-name>/.env` is preserved across deploys. Create it once on the Hetzner machine before the first deploy:
  ```dotenv
  DJANGO_DEBUG=False
  DJANGO_SECRET_KEY=<generate-a-long-random-secret>
  POSTGRES_PASSWORD=<generate-a-strong-db-password>
  FRONTEND_PORT=3000
  DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend,<server-ip-or-domain>
  DJANGO_CSRF_TRUSTED_ORIGINS=http://<server-ip>:3000
  DJANGO_CORS_ALLOWED_ORIGINS=http://<server-ip>:3000
  ```

## Production Docker Builds

Both Dockerfiles provide hardened, non-root `prod` targets (`gunicorn` + WhiteNoise for Django; `output: "standalone"` for Next.js):

```bash
docker build --target prod -t django-nextjs-backend:prod ./backend
docker build --target prod -t django-nextjs-frontend:prod ./frontend
```

For production deployments:
- Set `DJANGO_DEBUG=False` and provide a strong random `DJANGO_SECRET_KEY` (startup fails if `DJANGO_SECRET_KEY` is missing or left as the development placeholder).
- Configure `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, and `DATABASE_URL` (or `POSTGRES_*`).
- Run `python manage.py migrate --noinput` (or pass `RUN_MIGRATIONS=true`) before serving traffic.
