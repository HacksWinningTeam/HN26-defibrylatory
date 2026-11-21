# `T12` — Mirror AED source datasets from dane.gov.pl into the fork (files + connected APIs)

- **Status:** `TODO`
- **Layer:** `Backend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T11`
- **Traces To:** `REQ-03, REQ-04, REQ-15, DEC-014, DEC-009`
- **Estimate:** 1.5 h

## Goal & User Outcome

The fork contains the real AED datasets as separate datasets of their own institutions (Marki, Krosno, Przemyśl, Legionowo, Warszawa) plus an OpenStreetMap dataset — some as uploaded files, some as connected API resources — all tagged `AED`, so the portal shows "many different AED datasets" before aggregation.

## Scope & Non-Goals

- **In Scope:**
  - `manage.py aed_import_sources` (in `mcod.aed`): search `api.dane.gov.pl/1.4` for AED datasets (same query rules as the old harvester), create/update institution + dataset (title, description, licence, tags `AED`, `defibrylatory`, category HEAL, `ext_ident` = dane.gov.pl id) and resources: downloadable files are uploaded as `ResourceFile`; Warsaw = API link resource to `dane.um.warszawa.pl` (connector needs `WARSAW_API_TOKEN`); OSM = API link resource to the OpenAEDMap PL GeoJSON
  - Offline fallback: `--offline` uses the committed raw snapshot (`backend/apps/aed/fixtures/snapshot/`, copied into `fork-config/mcod_aed/fixtures/`), clearly labelled demo/offline
  - Every imported dataset gets "Standard danych" = `aed-pl` (DEC-015), so automatic validation runs on its resources (some real sources may end up blocked → `draft`, which is part of the demo story)
  - Idempotent (match by `ext_ident`), prints a summary table
- **Out of Scope:**
  - Parsing / aggregation (T13)

## UI Design (Per-Task)

N/A — backend/infra only (portal pages are the fork's existing UI).

## Technical Implementation Plan

- Reuse T06 publishing helpers (`ResourceFile` uploads, API-type link resources with `forced_api_type`) moved from `fork-config/publish_aed.py` into `mcod.aed/publishing.py`.
- `WARSAW_API_TOKEN` added to `fork-config/backend.env` (empty in git; real token only in the untracked fork `.env`).

## Acceptance Criteria

- [ ] Portal search `https://mcod.local/pl/dataset?q=AED` lists ≥ 6 source datasets from different institutions
- [ ] At least one file resource and two API resources (Warsaw, OSM) among them
- [ ] Re-run does not duplicate datasets/resources

## Verification Checklist

### Automated Checks
- [ ] `fork-config/test.sh` passes (pytest for `mcod.aed` inside the fork's `mcod-admin` container, incl. new tests for `T12`)
- [ ] `make test` / `make lint` still pass for the repo (no regressions; `backend/` frozen)
- [ ] Fork boots cleanly after `fork-config/setup.sh` (admin, api, celery healthy; `manage.py check` OK; `mcod.aed` migrations applied)
- [~] `make build-prod` — not required (no app/frontend change) unless compose files change
### Manual Verification
1. `docker exec mcod-admin python manage.py aed_import_sources` → summary table
2. Open the portal search for "AED" → separate institution datasets; open Warsaw → API resource
3. Run again → "exists/unchanged"

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
