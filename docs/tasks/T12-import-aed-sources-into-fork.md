# `T12` — Mirror AED source datasets from dane.gov.pl into the fork (files + connected APIs)

- **Status:** `VERIFIED`
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

- [x] Portal search lists 6 mirrored source datasets from 6 institutions (Krosno 4219, Marki 4220, Przemyśl 4221, Warszawa 4222, Legionowo 4223, OSM 4224), all with `data_standard: aed-pl`
- [x] 4 file resources (CSV ×3, GeoJSON) + 2 connected API resources: Warsaw city API (708 AEDs, token) and OpenAEDMap/OSM (18,310 AEDs)
- [x] Re-run does not duplicate anything (`unchanged`), keeps blocked resources as drafts; online discovery with `--offline` snapshot fallback
- [x] DEC-016: Legionowo original blocked (24/24 rows: "ulica", 6-digit TERC) and hidden from the public API; corrected copy (40232) published, 0 invalid rows

## Verification Checklist

### Automated Checks
- [x] `fork-config/test.sh` passes — 49 tests (6 new: snapshot specs, corrected vs original Legionowo, frequency/institution mapping, XLSX digest, Warsaw token required, idempotent import with standard + API resource in a rolled-back transaction)
- [x] `make test` (83) / `make lint` still pass
- [x] Fork healthy (containers recreated with `WARSAW_API_TOKEN`, no hook errors, no missing migrations)
- [~] `make build-prod` — not required (no app/frontend change) unless compose files change
### Observed Results (2026-11-22 ~02:05)
- `aed_import_sources` (online, 16–21 s): 6 datasets / 7 resources; automatic validation (Celery): Krosno 21 rows, Marki 8, Przemyśl 21, Warszawa 708 (live API), OSM 18,310 (live API) → `warnings` (published); Legionowo original → `invalid`, blocked (draft); corrected copy → 24 rows, 0 invalid, published.
- Token for Warsaw: `fork-config/fork-compose.sh` reads `WARSAW_API_TOKEN` from the untracked repo `.env` and passes it to admin/api/celery (compose override) — never stored in tracked files.

### Manual Verification
1. `docker exec mcod-admin python manage.py aed_import_sources` → table (Tryb: online, 6 datasets, 7 resources); run again → `unchanged`
2. https://mcod.local/pl/dataset?q=defibrylator → the six institution datasets; open Warszawa → resource type API; OpenStreetMap → API
3. https://admin.mcod.local → Zbiory danych → "Zdrowie" (Legionowo) → Zasoby: original = szkic with red "ZASÓB ZABLOKOWANY", corrected = published, green/yellow message; https://api.mcod.local/1.4/datasets/4223/resources shows only the corrected one
4. https://api.mcod.local/1.4/datasets/4222 → `data_standard: aed-pl`; https://api.mcod.local/1.4/resources/40229/standard-validation → 708 rows from the Warsaw API
5. Offline fallback: `docker exec mcod-admin python manage.py aed_import_sources --offline --no-osm` → "Tryb: offline", nothing duplicated

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-22 02:05
- **Notes / Follow-Ups:** —
