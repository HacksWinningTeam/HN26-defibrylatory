---
name: hackathon-run-task
description: >-
  Implement and verify a single task TXX from docs/05-plan.md and docs/tasks/TXX-*.md, enforcing
  UI design gates, writing unit tests, running make test/lint/schema-check/migrations-check (and
  build-prod when needed), and handing off manual verification steps. Use when executing a planned task.
---

# Implement & Verify Task `TXX`

Execute one task end-to-end against its spec and verification checklist while protecting all repository invariants.

## Pre-Flight Gates

1. **Load Specs & Rules**
   - Read `AGENTS.md`, `docs/04-decisions.md`, `docs/05-plan.md`, `docs/03-architecture.md`, and `docs/tasks/TXX-*.md`.
   - Read `backend/AGENTS.md` before editing `backend/` and `frontend/AGENTS.md` before editing `frontend/`.
2. **Check Dependencies & UI Gate**
   - Verify all tasks in `Depends On` are `VERIFIED` (unless the user explicitly waives a dependency).
   - If `UI Design Required` is `Yes` and `Status` is not `DESIGN_READY` or `IN_PROGRESS` (or **Approved** is empty), **stop**: run `hackathon-ui-design` (or re-present a `DESIGN_REVIEW` design) and get explicit user approval before writing UI code.
3. **Make Sure the Stack Is Running**
   - Run `docker compose ps`; if `db`, `backend`, or `frontend` are not running, start them with `make up-d` and wait until `GET /api/health/` responds.

## Implementation & Verification Steps

1. **Mark `IN_PROGRESS`**
   - Update `Status` to `IN_PROGRESS` in `docs/tasks/TXX-*.md` and `docs/05-plan.md`.

2. **Build the Vertical Slice + Unit Tests**
   - Implement backend models/migrations (`make makemigrations`, `make migrate`), DRF serializers/views with `@extend_schema`, and `pytest` unit/API tests covering happy paths and key validation/error cases.
   - Implement frontend Server/Client components via `frontend/src/lib/api.ts` (same-origin proxy; `export const dynamic = "force-dynamic";` on SSR pages querying Django), honoring the approved `## UI Design (Per-Task)` spec and WCAG 2.2 AA light baseline.
   - If adding/renaming env vars, mirror them in `.env.example`, `compose.yaml`, and `compose.prod.yaml`, and validate with `docker compose config --quiet` and `DJANGO_SECRET_KEY=ci-check docker compose -f compose.prod.yaml config --quiet`.
   - If `frontend/package.json` or `backend/pyproject.toml` changed, rebuild appropriately (`docker compose up -V --build` for frontend dependency updates, `docker compose up -d --build backend` for backend).

3. **Run All Automated Checks**
   - Run and verify zero failures/warnings:
     - `make test` (`docker compose exec -T backend pytest`)
     - `make lint` (`ruff check .`, `npm run typecheck`, `npm run lint`)
     - `make schema-check` (`python manage.py spectacular --validate --fail-on-warn`)
     - `make migrations-check` (`python manage.py makemigrations --check --dry-run`)
     - `make build-prod` if frontend code, Dockerfiles, dependencies, or Compose files changed, and always for the last task of a milestone (a push to `main` deploys immediately; a broken prod build breaks the live demo).
   - If a check cannot run, report it as **not run** with the reason — never as passed.
   - Check off passing automated items and Acceptance Criteria in `docs/tasks/TXX-*.md`.

4. **Hand Off for Manual Verification**
   - Update `docs/tasks/TXX-*.md` with observed command results and exact manual verification instructions (URLs, payloads, UI flows, and persistence checks).
   - Ask the user to run the manual checks and confirm. Keep `Status` at `IN_PROGRESS` until they do.
   - **Only after the user explicitly confirms** the manual checks passed: set `Status` to `VERIFIED` in `docs/tasks/TXX-*.md` and `docs/05-plan.md`, and fill **Sign-Off** (verifier + `date '+%Y-%m-%d %H:%M'`). If the user reports a problem, fix it and repeat steps 3–4.

5. **Checkpoint & Next Task**
   - Offer a local checkpoint commit (`TXX: <title>`) of the task's changes; commit only with the user's OK, and never include `.env` or secrets.
   - **Never run `git push`** — deployment to Hetzner runs automatically when the user manually pushes to `main`. If this was the last task of a milestone, remind the user that the milestone is ready to push and to check the live URL afterwards.
   - Inspect `docs/05-plan.md`, propose the next task `TYY` (stating whether `hackathon-ui-design` or `hackathon-run-task` comes next), and ask if the user is ready to proceed.
