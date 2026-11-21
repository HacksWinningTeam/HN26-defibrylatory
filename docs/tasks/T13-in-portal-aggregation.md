# `T13` — In-portal aggregation: convert sources to the standard structure + publish the common dataset natively

- **Status:** `TODO`
- **Layer:** `Backend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T12`
- **Traces To:** `REQ-05, REQ-06, REQ-09, REQ-15, DEC-014, DEC-011`
- **Estimate:** 2.5 h

## Goal & User Outcome

One command / admin action in the portal reads every AED source resource (files and connected APIs), converts it to the standard structure, merges and deduplicates the records and publishes "Defibrylatory AED – zbiór ogólnopolski" with fork-generated CSV/XLSX/GeoJSON/schema resources (table + map preview); each source dataset also gets its converted "wersja zgodna ze wzorcem AED" resource.

## Scope & Non-Goals

- **In Scope:**
  - Models (`mcod.aed`): `AedImportRun` (started/finished, status, report JSON), `AedSourceRecord` (FK Resource, row_no, raw JSON, data JSON keyed by schema fields, lat/lon, valid, quality_flags, FK AedDevice), `AedDevice` (`id_aed`, data JSON, lat/lon, sources_count) + migrations
  - Source selection (DEC-015): datasets with "Standard danych" = `aed-pl`, published, non-blocked resources only; invalid rows excluded and listed in the run report
  - Connectors: file resource -> main file; link/API resource -> fetch (generic URL, OpenAEDMap GeoJSON, Warsaw POST API with token; missing token -> source reported as `requires_api_key`, run continues)
  - Merge rules from DEC-011 (≤ 25 m or ≤ 75 m + similarity ≥ 0.6, never two records of one resource per cluster, dane.gov.pl > OSM precedence, coordinate checks)
  - Publishing: common dataset (org Misja AED, HEAL, ODbL note) with CSV (string columns + map columns label/b/l), XLSX, GeoJSON, schema XLSX as `ResourceFile`s; converted CSV resource added to each source dataset (first item to cut, DEC-015); idempotent (re-upload only on change)
  - Triggers: `manage.py aed_aggregate`, Celery task `mcod.aed.tasks.aggregate_task`, Django admin page "Agregacja AED" (run button + last run report)
  - `GET /1.4/aed/sources` (per-source status, record counts, coverage per field, quality flags) and `GET /1.4/aed/devices` (GeoJSON FeatureCollection with the DEC-008 property contract; `?bbox`, `?q`)
- **Out of Scope:**
  - Scheduling (manual trigger only), editing records in the UI

## UI Design (Per-Task)

N/A — backend/infra only (portal pages are the fork's existing UI).

## Technical Implementation Plan

- Port `backend/apps/aed/merge.py` + `sources_report.py`; exports (CSV/XLSX/GeoJSON writers) from `backend/apps/aed/exports.py`.
- Large OSM payload: stream/parse once, never store raw payload per record (DEC-011 OOM lesson).

## Acceptance Criteria

- [ ] `aed_aggregate` finishes in < 5 min; report shows every source with status + coverage
- [ ] Common dataset page in the portal: 4 resources, CSV with Tabela + Mapa, ~18.7k rows
- [ ] Each source dataset shows its converted "wersja zgodna ze wzorcem AED" CSV
- [ ] `/1.4/aed/sources` and `/1.4/aed/devices` return data; re-run does not duplicate

## Verification Checklist

### Automated Checks
- [ ] `fork-config/test.sh` passes (pytest for `mcod.aed` inside the fork's `mcod-admin` container, incl. new tests for `T13`)
- [ ] `make test` / `make lint` still pass for the repo (no regressions; `backend/` frozen)
- [ ] Fork boots cleanly after `fork-config/setup.sh` (admin, api, celery healthy; `manage.py check` OK; `mcod.aed` migrations applied)
- [~] `make build-prod` — not required (no app/frontend change) unless compose files change
### Manual Verification
1. Admin → "Agregacja AED" → Run → report (or `docker exec mcod-admin python manage.py aed_aggregate`)
2. Portal: common dataset → CSV → Tabela/Mapa; a source dataset (e.g. Krosno) → converted CSV resource
3. `curl -k https://api.mcod.local/1.4/aed/sources` and `/1.4/aed/devices?per_page=...`

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
