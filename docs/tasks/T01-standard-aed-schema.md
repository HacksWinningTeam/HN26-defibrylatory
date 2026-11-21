# `T01` — Standard AED schema (wzorcowy zakres danych) + downloads

- **Status:** `VERIFIED`
- **Layer:** `Backend`
- **UI Design Required:** `No`
- **Depends On:** None
- **Traces To:** `REQ-01`, `REQ-02`, `REQ-08`, `DEC-002`, `DEC-004`

## Goal & User Outcome

The standard AED schema exists once in code and can be downloaded as `.xlsx`, CSV template, JSON Schema and Frictionless Table Schema, so every data owner can publish AED data the same way on dane.gov.pl. This is the most important deliverable (user, DEC-002).

## Scope & Non-Goals

- **In Scope:**
  - `apps.aed` app skeleton registered in settings/urls
  - `apps/aed/schema.py`: ordered `FieldSpec` list (name, type, required, PL/EN description, example, allowed values, format/regex) covering identification, location (WGS84 + TERYT address), availability, device, owner/contact, metadata groups (see `docs/03-architecture.md`)
  - Field choices justified against real sources (Krosno, Marki, Przemyśl, Legionowo, OSM `emergency=defibrillator` tags) — short rationale in `docs/schema-aed.md`
  - Generators: `.xlsx` (sheet *Schemat* with field table + sheet *Przykład* with 2–3 example rows + sheet *Słowniki* with allowed values), CSV template (header + example row), JSON Schema (draft 2020-12), Table Schema
  - Endpoints `GET /api/schema-standard/` + downloads
  - Command `export_schema` writing files to `docs/deliverables/` (for submission)
- **Out of Scope:**
  - Models for records (T02/T03)
  - UI page (T08)

## UI Design (Per-Task)

N/A — backend/infra only.

## Technical Implementation Plan

- **Backend (`backend/`):**
  - Deps: add `openpyxl` to `backend/pyproject.toml`.
  - `apps/aed/apps.py`, `schema.py` (`FieldSpec` dataclass + `FIELDS`), `schema_export.py` (xlsx / csv / json-schema / table-schema builders), `views.py`, `serializers.py` (`FieldSpecSerializer`), `urls.py`, `management/commands/export_schema.py`.
  - Unit Tests (`apps/aed/tests/test_schema.py`): field names unique & snake_case ASCII; required set includes `nazwa`, `szerokosc_geograficzna`, `dlugosc_geograficzna`, `zrodlo`; xlsx opens and header row == field names; JSON Schema validates the example row and rejects a row with lat=200 / bad postcode / unknown `dostep`; API returns 200 + correct content types.
- **Frontend:** none.
- **Config / Env:** none.

## Acceptance Criteria

- [x] `GET /api/schema-standard/` returns the ordered field list with PL/EN descriptions
- [x] All 4 downloads return correct `Content-Type` and `Content-Disposition`
- [x] `make export-schema`-equivalent command writes files to `docs/deliverables/` (xlsx = submission deliverable)
- [x] `docs/schema-aed.md` explains each field group and maps source columns → standard fields

## Verification Checklist

### Automated Checks
- [x] `make test` passes (including new/updated unit & API tests for `T01`)
- [x] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [x] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [x] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [~] `make build-prod`: backend prod image built OK; frontend prod image **not run** (no frontend changes; Docker Hub anonymous pull limit 429 hit during T05 builds) — run at M1 end
  (required: new dependency)

### Manual Verification
1. `curl -sI http://localhost:8000/api/schema-standard/aed-schema.xlsx` → 200, xlsx content type; open the file in LibreOffice/Excel: 3 sheets, readable Polish descriptions
2. `curl -s http://localhost:8000/api/schema-standard/aed-schema.json | python3 -m json.tool` → valid JSON Schema
3. Review the field list in `docs/schema-aed.md` with the user (schema is the key deliverable)

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-21 19:33
- **Notes / Follow-Ups:** Observed 2026-11-21 18:47: 27 tests passed (16 new in `apps/aed/tests/test_schema.py`), ruff OK, OpenAPI valid, no migrations. Schema v1.0.0 = 37 fields, 8 required; extended per DEC-007 (19:31) to 42 fields, 8 required — 28 tests pass, all checks green, deliverables re-exported. Deliverables in `docs/deliverables/`. Base image `python:3.12-slim` was re-tagged from `mirror.gcr.io` because of Docker Hub rate limiting (no Dockerfile change).
