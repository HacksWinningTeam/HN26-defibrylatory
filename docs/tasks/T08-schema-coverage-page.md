# `T08` — Schema & source coverage page (/schemat)

- **Status:** `TODO`
- **Layer:** `Frontend`
- **UI Design Required:** `Yes`
- **Depends On:** `T04`
- **Traces To:** `REQ-01`, `REQ-02`, `REQ-05`, `REQ-10`, `DEC-004`

## Goal & User Outcome

Judges and data owners see the standard schema (field table, descriptions, examples) with download buttons, plus a coverage matrix showing which standard fields each harvested source fills.

## Scope & Non-Goals

- **In Scope:**
  - `/schemat`: field table grouped by section, download buttons (xlsx / csv / JSON Schema / Table Schema)
  - Coverage matrix: sources × field groups with % + text labels (non-color cues)
- **Out of Scope:**
  - Editing the schema in UI

## UI Design (Per-Task)

- **Approved:** `—`
- **Route(s):** `/schemat`
- **Reference Sketch / Assets:** None
- **Layout & Information Hierarchy:** PENDING (`hackathon-ui-design`)
- **Components (Reused vs. New):** PENDING
- **Interactive States:** PENDING (loading / empty / error / success)
- **API Fields & Contracts Consumed:** `GET /api/schema-standard/`, `GET /api/sources/`
- **WCAG 2.2 AA Checks:** PENDING — contrast, `:focus-visible`, `>= 44px` targets, semantic headings, non-color cues.

## Technical Implementation Plan

- **Frontend (`frontend/`):** `src/app/schemat/page.tsx` (server, `force-dynamic`), `src/components/schema/SchemaTable.tsx`, `CoverageMatrix.tsx`; `src/lib/api.ts` helpers.

## Acceptance Criteria

- [ ] Schema table matches `/api/schema-standard/`
- [ ] Downloads work through the same-origin proxy
- [ ] Coverage matrix readable without color

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `T08`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes
  (required: frontend code)

### Manual Verification
1. Open `http://localhost:3000/schemat` → fields + downloads; click xlsx → file downloads
2. Coverage shows e.g. Legionowo high on address fields, OSM high on access hours

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** First task to cut if time runs out (schema files are still delivered via T01).
