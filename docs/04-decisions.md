# 04 — Decision & Change Log

> Append-only log of architecture decisions, requirement clarifications, UI pivots, and mid-hackathon scope changes. Every agent must read this file before designing or implementing any task.

## When to Add a Decision (`DEC-XXX`)

- At kickoff when establishing initial MVP scope and constraints (`DEC-001`).
- Whenever new organizer info, mentor feedback, or extra user notes arrive.
- Whenever a task's UI design requires adding/changing API endpoints, models, or shared UI primitives.
- Whenever a planned task is split, modified, or `CANCELLED`.

## Decisions

### `DEC-000` — Template Baseline & Architecture Invariants
- **Date:** Initial template setup
- **Status:** Accepted
- **Context:** Full-stack hackathon template targeting fast vertical slices and automatic Hetzner deployment.
- **Decision:** Keep single-port Next.js 16 proxying (`frontend/src/proxy.ts` + `skipTrailingSlashRedirect`), PostgreSQL 18 (`/var/lib/postgresql`), `uv` (`/opt/venv`), WCAG 2.2 AA light UI baseline, mandatory unit tests + lint/typecheck/schema checks, and manual `git push`.
- **Affected Docs & Tasks:** `AGENTS.md`, `docs/02-ui-system.md`, `docs/03-architecture.md`.

<!-- Template for new entries:
### `DEC-XXX` — `<Short Title>`
- **Date:** `<YYYY-MM-DD HH:MM from date '+%Y-%m-%d %H:%M'>`
- **Status:** Accepted | Superseded by DEC-YYY
- **Context / New Info:** `<What changed or what was decided>`
- **Decision:** `<Exact choice made>`
- **Affected Docs & Tasks:** `<e.g., docs/01-brief.md, docs/03-architecture.md, T03, T04>`
-->
