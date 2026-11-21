# `T03` — Parse, normalize to standard schema, coverage report, merge & dedupe

- **Status:** `TODO`
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

- [ ] `harvest_aed` (online) and `harvest_aed --offline` both produce a merged `AED` table
- [ ] Each source shows coverage per standard field via `/api/sources/`
- [ ] Duplicates between municipal sources and OSM are merged; every AED lists its sources
- [ ] Records with invalid coordinates are flagged/excluded, never silently moved

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `T03`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes

### Manual Verification
1. `docker compose exec backend python manage.py harvest_aed --offline` → summary: records per source, merged total, duplicates merged
2. `curl -s localhost:8000/api/sources/ | python3 -m json.tool` → coverage per field per source
3. Spot-check in admin: a Marki AED has correct (lat ≈ 52.3, lon ≈ 21.1) and is linked to an OSM duplicate if one exists

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
