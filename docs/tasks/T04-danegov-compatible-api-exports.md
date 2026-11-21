# `T04` — dane.gov.pl-compatible API (/api/1.4) + open exports

- **Status:** `TODO`
- **Layer:** `Backend`
- **UI Design Required:** `No`
- **Depends On:** `T03`
- **Traces To:** `REQ-07`, `REQ-08`, `DEC-004`

## Goal & User Outcome

The merged dataset is available through endpoints that look like the dane.gov.pl API (`/1.4` JSON:API envelope) and as CSV / JSON / GeoJSON / XLSX exports with metadata, ready to be linked from the dane.gov.pl fork.

## Scope & Non-Goals

- **In Scope:**
  - `GET /api/1.4/datasets`, `/api/1.4/datasets/{id}`, `/api/1.4/datasets/{id}/resources`, `/api/1.4/resources/{id}`, `/api/1.4/resources/{id}/data` — envelope `data/attributes/relationships/links/meta`, pagination `page/per_page`, `q` search on data, attribute names as in dane.gov.pl (`title`, `notes`, `format`, `media_type`, `file_url`, `download_url`, `license_name`, `created`, `modified`, `openness_score`, …), rows `type: row` with `col1..colN` + `meta.headers_map`
  - Exports `GET /api/exports/aed.{csv,json,geojson,xlsx}` in standard schema column order (CSV UTF-8, comma, numeric lat/lon; JSON `{meta, data}`; GeoJSON FeatureCollection; XLSX with *Dane* + *Metadane* sheets)
  - Metadata block: title, description, owner, licence (CC BY 4.0 for merged + ODbL note for OSM-derived), update frequency, sources list, generated_at
  - `GET /api/aed/?bbox=&q=` lightweight GeoJSON for the map (T07)
- **Out of Scope:**
  - Full dane.gov.pl API surface (search facets, showcases, etc.)
  - Write endpoints

## UI Design (Per-Task)

N/A — backend/infra only.

## Technical Implementation Plan

- **Backend (`backend/`):**
  - `apps/aed/jsonapi.py` (envelope + pagination helpers), `exports.py`, `views_portal.py`, `urls.py` (`api/1.4/...`, `api/exports/...`, `api/aed/`), serializers + `@extend_schema` for each.
  - Unit Tests (`tests/test_portal_api.py`, `test_exports.py`): envelope keys match a recorded dane.gov.pl response fixture (`tests/fixtures/danegov_dataset.json`); pagination links; `/data` headers_map vs export columns; CSV parse round-trip (numeric lat/lon); GeoJSON valid; XLSX opens; `/api/aed/?bbox=` filters correctly.

## Acceptance Criteria

- [ ] Responses of `/api/1.4/datasets/{id}` and `/api/1.4/resources/{id}/data` share top-level structure and key attribute names with `https://api.dane.gov.pl/1.4/...`
- [ ] All 4 exports download and open; columns follow the standard schema
- [ ] OpenAPI docs list all endpoints with schemas

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `T04`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes

### Manual Verification
1. Open `http://localhost:8000/api/docs/` → endpoints under tags `dane.gov.pl compatible` and `exports`
2. Compare side by side: `curl -s https://api.dane.gov.pl/1.4/resources/2625221 | jq 'keys, .data|keys'` vs `curl -s localhost:8000/api/1.4/resources/1 | jq 'keys, .data|keys'`
3. Download `aed.csv`, `aed.xlsx`, `aed.geojson` (drop the GeoJSON on geojson.io → points over Poland)

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
