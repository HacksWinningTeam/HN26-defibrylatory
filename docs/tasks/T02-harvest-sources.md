# `T02` — Harvester: discover & download all AED sources (dane.gov.pl + OSM)

- **Status:** `VERIFIED`
- **Layer:** `Backend`
- **UI Design Required:** `No`
- **Depends On:** `T01`
- **Traces To:** `REQ-03`, `REQ-04`, `DEC-002`, `DEC-004`

## Goal & User Outcome

One command finds every AED dataset on dane.gov.pl via its public API, downloads all their resources (raw), and fetches all AEDs in Poland from OpenStreetMap, storing everything with provenance.

## Scope & Non-Goals

- **In Scope:**
  - Models `SourceDataset`, `SourceResource` (+ migrations, admin registration)
  - `harvest.py`: dane.gov.pl client — `/1.4/search` + `/1.4/datasets?q=` for `defibrylator`, `defibrylatory`, `AED`; filter by title/description keywords; resolve resource → dataset; list `/datasets/{id}/resources`; download `file_url`/`link` with timeout + 3 retries; store raw file
  - Pick best resource per dataset (GeoJSON > CSV > XLSX > JSON > XML) as `selected`
  - Overpass client: `nwr[emergency=defibrillator]` in PL area, `out center tags;` with fallback mirror (`overpass.kumi.systems`)
  - Command `harvest_aed --fetch-only` (parsing comes in T03)
  - Copy fetched raw files into `apps/aed/fixtures/snapshot/` (labelled offline snapshot) via `--save-snapshot`
- **Out of Scope:**
  - Parsing/normalization (T03)
  - Scheduled refresh

## UI Design (Per-Task)

N/A — backend/infra only.

## Technical Implementation Plan

- **Backend (`backend/`):**
  - Deps: none (stdlib `urllib`).
  - `apps/aed/models.py` (`SourceDataset`, `SourceResource`), `admin.py`, `harvest.py`, `management/commands/harvest_aed.py`.
  - Unit Tests (`tests/test_harvest.py`): dane.gov.pl search response fixture → correct dataset ids discovered (dedup of dataset vs resource hits, irrelevant hits like "Baza pojazdów ZTM" filtered); best-format selection; Overpass response fixture → N elements; network errors retried then recorded as `parse_status=error` without crashing; idempotent re-run (no duplicate SourceDataset).
- **Config / Env:** `WARSAW_API_TOKEN` (DEC-009) in `.env.example`, `compose.yaml`, `compose.prod.yaml`.

## Acceptance Criteria

- [x] `harvest_aed --fetch-only` discovers ≥5 dane.gov.pl AED datasets (Krosno, Marki, Przemyśl, Legionowo, Warszawa link) + OSM
- [x] Raw payload for each resource stored and listed in Django admin
- [x] Re-running is idempotent
- [x] Snapshot saved to `apps/aed/fixtures/snapshot/` and committed (offline fallback)

## Verification Checklist

### Automated Checks
- [x] `make test` passes (including new/updated unit & API tests for `T02`)
- [x] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [x] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [x] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [~] `make build-prod` not required (no deps/frontend/compose changes) — run at M1 end (T04)

### Manual Verification
1. `docker compose exec backend python manage.py harvest_aed --fetch-only` → summary table: dataset, publisher, formats, selected resource, bytes
2. `/admin/aed/sourceresource/` lists resources with raw files downloadable
3. Run again → same counts, no duplicates

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-21 20:23
- **Notes / Follow-Ups:** Observed 2026-11-21 19:44: live harvest in 38 s → 6 sources: Krosno (CSV), Marki (CSV+XLSX), Przemyśl (GeoJSON selected; CSV/JSON/GML; one GML re-upload flagged duplicate by content hash), Legionowo (CSV from mixed dataset "Zdrowie", pharmacies skipped), Warszawa (link → HTML catalogue page → `not_machine_readable`), OSM 18,298 AEDs via OpenAEDMap GeoJSON (7.1 MB). Overpass is unreachable from this network (timeouts) → OpenAEDMap is the primary OSM source, Overpass kept as fallback. Raw payloads stored in DB (`BinaryField`, avoids prod media permissions). Snapshot (7.1 MB) in `backend/apps/aed/fixtures/snapshot/` + `harvest_aed --offline`. 36 tests pass (8 new). 20:11 (DEC-009): Warsaw adapter via token-protected city API + status `requires_api_key`; 39 tests pass; compose configs valid. 2026-11-21 20:21: with token in `.env` Warsaw fetched OK — 708 AEDs (437 KB JSON list; geometry `coordinates` nested `[[lon, lat]]`; props `defibrillator_id, device_access_description, device_availability (Tak/Nie/Ograniczona/free text), device_location, device_manufacturer, device_public_access (Publiczny/Prywatny), device_specifications, location_*`) → T03 parser. Snapshot refreshed (no token stored). Gotcha: `make build-prod` / `compose -f compose.prod.yaml build backend` re-tags the dev image name → rebuild dev with `docker compose build backend` afterwards.
