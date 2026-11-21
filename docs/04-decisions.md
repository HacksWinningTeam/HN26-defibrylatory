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

### `DEC-001` — Appearance, i18n, and WCAG 2.2 AA Accessibility Configuration
- **Date:** 2026-11-21 14:36
- **Status:** Accepted
- **Context / New Info:** User requested an exact copy of the appearance, language (i18n), and WCAG accessibility configuration from `/Users/kubamilcarz/Developer/HackNation-2026/HN26-PCI`.
- **Decision:** Imported the full `appearance/` (`system`, `light`, `dark`, `hc-black-white`, `hc-black-yellow`, `grayscale`), `i18n/` (`pl-PL` default, `en-US`), and `components/accessibility/` + `/settings/accessibility` WCAG 2.2 AA system (pre-hydration script, CSS semantic tokens, `AccessibilityProvider`, `AccessibilityMenu`, `textScale` 25%–200%, `underlineLinks`, `Read aloud` via `speechSynthesis`, and `node --test` unit tests).
- **Affected Docs & Tasks:** `docs/02-ui-system.md`, `docs/accessibility-system.md`, `frontend/package.json`, `frontend/src/app/`, `frontend/src/appearance/`, `frontend/src/i18n/`, `frontend/src/components/`, `frontend/src/lib/`.

<!-- Template for new entries:
### `DEC-XXX` — `<Short Title>`
- **Date:** `<YYYY-MM-DD HH:MM from date '+%Y-%m-%d %H:%M'>`
- **Status:** Accepted | Superseded by DEC-YYY
- **Context / New Info:** `<What changed or what was decided>`
- **Decision:** `<Exact choice made>`
- **Affected Docs & Tasks:** `<e.g., docs/01-brief.md, docs/03-architecture.md, T03, T04>`
-->
