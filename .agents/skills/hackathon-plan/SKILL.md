---
name: hackathon-plan
description: >-
  Generate the system architecture (docs/03-architecture.md) and break the MVP into ordered,
  verifiable vertical-slice tasks (docs/05-plan.md and docs/tasks/TXX-*.md). Use after
  docs/01-brief.md is approved or when creating an initial development plan.
---

# Hackathon System Planning

Break the approved brief into small, end-to-end verifiable vertical slices ordered by demo value and the deadline. Defer per-task UI design until just before each UI-facing task is built.

## Steps

1. **Load Context**
   - Read `AGENTS.md`, `docs/01-brief.md` (especially **Timeline**), `docs/02-ui-system.md`, and `docs/04-decisions.md`.
   - Check the current codebase (`backend/`, `frontend/`, `compose.yaml`, `compose.prod.yaml`) so architecture builds directly on existing files.

2. **Write `docs/03-architecture.md`**
   - Define High-Level Data Flow, Backend Apps & Data Models (`backend/apps/...`), DRF API Endpoints + `drf-spectacular` schemas, Frontend Routes (`frontend/src/app/...`), required env vars (to mirror in `.env.example`, `compose.yaml`, `compose.prod.yaml`), and explicit Hackathon Simplifications.

3. **Create Master Task Board (`docs/05-plan.md`) & Task Specs (`docs/tasks/TXX-*.md`)**
   - **Remove every `<Example: ...>` placeholder row** from `docs/05-plan.md` (routing treats any remaining example row as "plan not created yet").
   - Organize into milestones (`M1: Core Vertical Slice`, `M2: Core Features`, `M3: Demo Polish`).
   - Order tasks by demo value: the primary happy path must be demoable end-to-end as early as possible. Estimate each task (ideally 1–3 hours) and check the total against the time left until the code freeze in `docs/01-brief.md`; move anything that does not fit into M3 or Nice-to-Have and tell the user.
   - **M3 must always include:**
     - A clearly labelled demo seed-data command (e.g. `python manage.py seed_demo`, idempotent, records marked as demo data).
     - A written demo script (`docs/demo-script.md`: the click-through, talking points, fallback if something fails).
     - A production check: `make build-prod` passes, and after the user pushes, the live Hetzner URL works through the full happy path.
   - For each task `TXX`, create `docs/tasks/TXX-<slug>.md` modeled on `docs/tasks/_template.md`:
     - `Status: TODO`.
     - Trace to `REQ-XX` and `DEC-XXX`.
     - `UI Design Required`: `No` for backend/infra-only tasks, `Yes` for UI-facing tasks (leave `## UI Design (Per-Task)` as `PENDING` — do not over-specify screen mocks upfront).
     - List exact backend/frontend files, unit test cases, acceptance criteria, automated checks (`make test`, `make lint`, `make schema-check`, `make migrations-check`, plus `make build-prod` when frontend/Docker/deps change), and concrete manual verification steps.
   - In the `docs/05-plan.md` table, link each row's `Spec` to its real `tasks/TXX-<slug>.md` file (never `tasks/_template.md`).
   - Back-fill the `Target Task(s)` column of the requirements table in `docs/01-brief.md`; every `Must` requirement needs at least one task.
   - Log a `DEC-XXX` entry in `docs/04-decisions.md` if planning introduces major architectural choices (timestamp from `date '+%Y-%m-%d %H:%M'`).

4. **Review Gate**
   - Present the milestone plan, dependency order, time estimates vs. code freeze, and `UI Design?` markers to the user.
   - Wait for user approval before running `hackathon-ui-design` or `hackathon-run-task`.
