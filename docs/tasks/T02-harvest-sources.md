# `T02` — Harvester: discover & download all AED sources (dane.gov.pl + OSM)

- **Status:** `TODO`
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
  - Deps: `requests` (or stdlib `urllib`); add to `pyproject.toml` if used.
  - `apps/aed/models.py` (`SourceDataset`, `SourceResource`), `admin.py`, `harvest.py`, `management/commands/harvest_aed.py`.
  - Unit Tests (`tests/test_harvest.py`): dane.gov.pl search response fixture → correct dataset ids discovered (dedup of dataset vs resource hits, irrelevant hits like "Baza pojazdów ZTM" filtered); best-format selection; Overpass response fixture → N elements; network errors retried then recorded as `parse_status=error` without crashing; idempotent re-run (no duplicate SourceDataset).
- **Config / Env:** none (constants in `harvest.py`).

## Acceptance Criteria

- [ ] `harvest_aed --fetch-only` discovers ≥5 dane.gov.pl AED datasets (Krosno, Marki, Przemyśl, Legionowo, Warszawa link) + OSM
- [ ] Raw payload for each resource stored and listed in Django admin
- [ ] Re-running is idempotent
- [ ] Snapshot saved to `apps/aed/fixtures/snapshot/` and committed (offline fallback)

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `T02`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes

### Manual Verification
1. `docker compose exec backend python manage.py harvest_aed --fetch-only` → summary table: dataset, publisher, formats, selected resource, bytes
2. `/admin/aed/sourceresource/` lists resources with raw files downloadable
3. Run again → same counts, no duplicates

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
