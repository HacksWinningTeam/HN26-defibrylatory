# `T14` — Validation API: `POST /1.4/aed/validate` against the standard structure

- **Status:** `TODO`
- **Layer:** `Backend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T11`
- **Traces To:** `REQ-16, REQ-01, DEC-014`
- **Estimate:** 2 h (incl. DEC-015 automatic validation + blocking)

## Goal & User Outcome

Anyone (a data owner before publishing, or the portal itself) can send AED data to `https://api.mcod.local/1.4/aed/validate` and get a machine-readable report of how it matches the standard structure: per-row/per-field errors and warnings, detected column mapping and field coverage.

## Scope & Non-Goals

- **In Scope:**
  - Inputs: multipart upload (`file`: CSV/XLSX/JSON/GeoJSON/XML), JSON body `{"url": "..."}` (fetched server-side, size/time limits), or `{"resource_id": N}` (resource already in the portal); optional `?strict=true` (only exact schema column names)
  - Checks per field from `schema.py`: required present + non-empty, type (number/integer/boolean/date/string), allowed values, pattern, min/max, max_length; coordinates inside Poland + swap detection; duplicate `id_aed`
  - Response (JSON:API envelope, `type: "aed_validation"`): `attributes{valid, schema_version, rows_total, rows_valid, rows_with_errors, column_mapping{source_column: field|null}, unknown_columns[], missing_required_fields[], coverage{field: ratio}, errors[{row, field, code, message, value}] (first 500), warnings[...]}`; HTTP 200 for a completed validation (valid or not), 400 for unreadable input, 413 too large
  - `GET /1.4/aed/validate` returns usage/help (fields accepted) for discoverability
  - **Automatic validation (DEC-015):** resources of datasets with a standard are validated (a) synchronously in the admin resource form on file upload — blocking errors reject the save with the error list; (b) after the fork's file/data Celery tasks (link/API resources, revalidation, imports) — blocking → resource set to `draft`; result stored in `ResourceStandardValidation`, shown in admin and at `GET /1.4/resources/{id}/standard-validation`
  - Blocking = unreadable file, required columns missing/unmappable, or invalid rows > `max_invalid_ratio` (0.2)
- **Out of Scope:**
  - UI form for validation (could be a later nice-to-have in the Next.js app)

## UI Design (Per-Task)

N/A — backend/infra only (portal pages are the fork's existing UI).

## Technical Implementation Plan

- Shared with T13: parsers + mapping + normalisation from T11; validation rules generated from `FieldSpec`.
- Limits: 20 MB upload, 30 s fetch timeout, 100k rows.

## Acceptance Criteria

- [ ] Valid sample (schema CSV template filled with 3 rows) → `valid: true`, 0 errors
- [ ] Broken sample (missing coords, bad enum, wrong date) → errors with row + field + code
- [ ] Real source (e.g. Krosno CSV via `url`, a portal `resource_id`) → report with column mapping and coverage
- [ ] Unreadable file → 400 with JSON:API `errors[]`
- [ ] Admin: uploading an invalid CSV to an `aed-pl` dataset is rejected with errors; a valid one publishes and shows "zgodny ze standardem"
- [ ] An `aed-pl` link resource whose data is invalid ends up `draft` with a stored report

## Verification Checklist

### Automated Checks
- [ ] `fork-config/test.sh` passes (pytest for `mcod.aed` inside the fork's `mcod-admin` container, incl. new tests for `T14`)
- [ ] `make test` / `make lint` still pass for the repo (no regressions; `backend/` frozen)
- [ ] Fork boots cleanly after `fork-config/setup.sh` (admin, api, celery healthy; `manage.py check` OK; `mcod.aed` migrations applied)
- [~] `make build-prod` — not required (no app/frontend change) unless compose files change
### Manual Verification
1. `curl -k -F file=@samples/aed-valid.csv https://api.mcod.local/1.4/aed/validate` → `valid: true`
2. `curl -k -F file=@samples/aed-invalid.csv ...` → errors listed per row/field
3. `curl -k -H 'Content-Type: application/json' -d '{"resource_id": <Krosno CSV id>}' https://api.mcod.local/1.4/aed/validate` → mapping + coverage

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
