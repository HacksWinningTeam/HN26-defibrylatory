# `T09` — Demo readiness: offline snapshot seed, demo script, production check

- **Status:** `VERIFIED`
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

> Adapted to DEC-014/017: the offline seed is now `fork-config/aed-demo.sh --offline` in the portal (the old backend `load_aed_snapshot` is not needed — the backend keeps its own `harvest_aed --offline`).

- [x] `fork-config/aed-demo.sh` (import → wait for automatic validation → aggregation, ~45 s, idempotent; `--offline` uses the committed snapshot) → 6 sources → 18,776 AEDs
- [x] `docs/demo-script.md`: 10-step click-through with timings, talking points per judging criterion, fallbacks, limitations, screenshot list
- [x] Screenshots for the slides: `docs/demo/screenshots/T09-s01…s12-*.png` (+ T07/T15 map)
- [x] Admin sidebar section "Standardy danych" (DEC-017)
- [x] `make build-prod` passes; retired `backend/` kept as the Hetzner fallback data source (DEC-017) — live URL to be checked by the user after push

## Verification Checklist

### Automated Checks
- [x] `make test` passes — 83 (backend started only for the checks); fork `fork-config/test.sh` 57 OK; frontend `npm test` 20 OK
- [x] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [x] `make schema-check` passes
- [x] `make migrations-check` passes (no changes); fork `makemigrations aed --check` clean
- [x] `make build-prod` passes; `docker compose config`, prod config, `fork-compose.sh config` valid
  (required: milestone end)

### Manual Verification
1. `fork-config/aed-demo.sh` → table of 6 sources + "Agregacja …: 6 źródeł … -> 18776 urządzeń AED"; run again → same counts
2. Dry-run `docs/demo-script.md` end to end with a timer (≈ 6–7 min), incl. the invalid-file upload in the admin and "Uruchom agregację"
3. Admin sidebar shows "Standardy danych" (refresh the admin once)
4. After your push to `main`: open the live Hetzner URL → map loads (data from the old backend, DEC-017)

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-22 02:42
- **Notes / Follow-Ups:** —
