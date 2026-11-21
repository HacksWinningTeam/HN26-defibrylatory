# `T09` — Demo readiness: offline snapshot seed, demo script, production check

- **Status:** `TODO`
- **Layer:** `Infra`
- **UI Design Required:** `No`
- **Depends On:** `T13`, `T14`, `T15` (was T06, T07, T10 — DEC-014)
- **Traces To:** `REQ-12`, `DEC-002`

> **Updated by DEC-014 (2026-11-22):** demo = local fork with `mcod.aed` (source datasets → aggregation → common dataset → validation API → map). Also decide whether to drop the retired `backend/` from `compose*.yaml`/CI (keep the live deploy working) and refresh the offline snapshot inside `fork-config/mcod_aed/fixtures/`.

## Goal & User Outcome

The demo works even if external sources are down, has a written click-through script, and the production build/deploy works end-to-end.

## Scope & Non-Goals

- **In Scope:**
  - Demo seed: `python manage.py load_aed_snapshot` (idempotent, uses committed snapshot from T02, records marked `zrodlo` + `snapshot` flag — clearly labelled demo/offline data)
  - `docs/demo-script.md`: click-through (harvest → sources coverage → API compare with dane.gov.pl → fork dataset page/table/map → Next.js map), talking points per judging criterion, fallback paths
  - Screenshot list for the ≥5-slide presentation
  - Production: `make build-prod` passes; after user pushes, live Hetzner URL shows `/mapa` and `/api/1.4/...`; harvest run on server documented
- **Out of Scope:**
  - Branding/slides content itself (separate deliverable)

## UI Design (Per-Task)

N/A — backend/infra only.

## Technical Implementation Plan

- `backend/apps/aed/management/commands/load_aed_snapshot.py` + test; `docs/demo-script.md`; optional `compose.prod.yaml` note on running harvest after deploy.

## Acceptance Criteria

- [ ] `load_aed_snapshot` on an empty DB produces the merged dataset offline; second run changes nothing
- [ ] `docs/demo-script.md` complete with fallbacks
- [ ] `make build-prod` passes; live URL verified by user after push

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `T09`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes
  (required: milestone end)

### Manual Verification
1. `docker compose exec backend python manage.py load_aed_snapshot` twice → same counts
2. Dry-run the demo script end to end with a timer
3. After push: open live URL `/mapa`, `/api/1.4/datasets`

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
