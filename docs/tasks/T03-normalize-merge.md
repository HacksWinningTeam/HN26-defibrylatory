# `T03` — Parse, normalize to standard schema, coverage report, merge & dedupe

- **Status:** `VERIFIED`
- **Layer:** `Backend`
- **UI Design Required:** `No`
- **Depends On:** `T02`
- **Traces To:** `REQ-05`, `REQ-06`, `DEC-004`

## Goal & User Outcome

Every harvested source is mapped to the standard schema with a per-source coverage report, and all sources are merged into one deduplicated national AED dataset with provenance.

## Scope & Non-Goals

- **In Scope:**
  - Models `SourceRecord`, `AED` (+ migrations)
  - Parsers: CSV (encoding/delimiter sniffing, BOM, row-wrapped quoting like Marki), XLSX, GeoJSON (Point + Przemyśl `geometry`), OSM elements (tags `defibrillator:location`, `opening_hours`, `access`, `indoor`, `level`, `operator`, `phone`, `addr:*`)
  - `mappings.py`: header synonyms → standard fields + per-source overrides
  - `normalize.py`: coords validation in PL bbox (49.0–54.9 N, 14.1–24.2 E), lat/lon swap detection, postcode regex `\d{2}-\d{3}`, address splitting (`ul. X 12, 00-000 Miasto`), `24/7` detection, quality flags
  - Coverage per resource: share of non-empty values per standard field + overall %
  - `merge.py`: dedupe (≤25 m, or ≤75 m + name/address similarity ≥0.6), precedence dane.gov.pl > OSM, stable `id_aed`
  - `harvest_aed` full pipeline (fetch → parse → merge); `--offline` uses snapshot
  - `GET /api/sources/` (sources + coverage + counts)
- **Out of Scope:**
  - Fancy fuzzy matching / PostGIS
  - Manual review UI

## UI Design (Per-Task)

N/A — backend/infra only.

## Technical Implementation Plan

- **Backend (`backend/`):**
  - `apps/aed/models.py` (`SourceRecord`, `AED`), `parsers/{csv_generic,xlsx,geojson,osm}.py`, `mappings.py`, `normalize.py`, `merge.py`, `serializers.py` (`SourceSerializer` with coverage), `views.py` (`SourceListView`), `urls.py`.
  - Unit Tests (`tests/test_parsers.py`, `test_normalize.py`, `test_merge.py`, `test_sources_api.py`): Krosno CSV (lon,lat order) parsed right; Marki broken quoting + swapped coords fixed; Przemyśl `;` CSV / GeoJSON parsed; Legionowo TERYT columns mapped 1:1; OSM tags mapped; point outside PL flagged; two points 10 m apart merged with both provenances; 500 m apart not merged; coverage % computed correctly; `/api/sources/` shape.

## Acceptance Criteria

- [x] `harvest_aed` (online) and `harvest_aed --offline` both produce a merged `AED` table
- [x] Each source shows coverage per standard field via `/api/sources/`
- [x] Duplicates between municipal sources and OSM are merged; every AED lists its sources
- [x] Records with invalid coordinates are flagged/excluded, never silently moved

## Verification Checklist

### Automated Checks
- [x] `make test` passes (including new/updated unit & API tests for `T03`)
- [x] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [x] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [x] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [~] `make build-prod` not required (no deps/frontend/compose changes) — run at M1 end (T04)

### Manual Verification
1. `docker compose exec backend python manage.py harvest_aed --offline` → summary: records per source, merged total, duplicates merged
2. `curl -s localhost:8000/api/sources/ | python3 -m json.tool` → coverage per field per source
3. Spot-check in admin: a Marki AED has correct (lat ≈ 52.3, lon ≈ 21.1) and is linked to an OSM duplicate if one exists

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-21 21:48
- **Notes / Follow-Ups:** Observed 2026-11-21 21:21: live `harvest_aed` (fetch + parse + merge) 33 s, `--offline` 10 s → 19,084 records → **18,769 AEDs, 315 confirmed by 2+ sources** (Warsaw∩OSM 257+, Krosno∩OSM 20, Przemyśl∩OSM 16, Legionowo∩OSM 8, Marki∩OSM 3). Coverage (overall / required): Warsaw 38% / 100%, Legionowo 31%, Marki 29%, Krosno 28%, Przemyśl 27%, OSM 26% / 88% (OSM lacks `miejscowosc`). Quality findings: Marki — 7 swapped coordinates, 1 record with Krosno's coordinates (excluded), repeated coordinates; Legionowo — 6-digit TERC, `cecha_ulicy`=`ulica`; Warsaw — 606 free-text hours. 59 tests pass (23 new in `test_normalize_merge.py`). See DEC-011 (merge rules, JSON records, OOM fix).
