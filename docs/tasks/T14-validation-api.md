# `T14` — Validation API: `POST /1.4/aed/validate` against the standard structure

- **Status:** `VERIFIED`
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

- [x] Valid sample (`docs/demo/samples/aed-bydgoszcz-demo.csv`, 3 rows) → `valid: true`, `status: valid`, 0 errors
- [x] Broken sample (`aed-invalid-demo.csv`: missing coords, point in Germany, bad enum, wrong date, empty name) → 5 errors with row + field + code + Polish message, `blocking: true`
- [x] Real source: Krosno CSV from production dane.gov.pl via `url` → `warnings` (columns recognised under non-standard names, derivable required fields), not blocking; portal `resource_id` 40212 (18,769 rows) → 552 invalid rows (bad phone numbers) = 2.9 %, not blocking, ~3 s
- [x] Unreadable / empty input → 400 with JSON:API `errors[]`; unknown `resource_id` → 404
- [x] Admin: uploading `aed-invalid-demo.csv` to the `aed-pl` dataset 4212 is refused with the error list at the file field; `aed-bydgoszcz-demo.csv` publishes (resource 40218) and Celery stores "zgodny ze standardem"
- [x] A resource created outside the form (import path) with invalid data → validated by Celery after the portal's processing → set to `draft` (resource 40219), public `/1.4/resources/40219` → 404, report stored

## Verification Checklist

### Automated Checks
- [x] `fork-config/test.sh` passes — 43 tests (16 new: validator rules/formats/strict/threshold, `/1.4/aed/validate` multipart/raw/errors, stored validation 404, automatic blocking + admin form rule in rolled-back transactions)
- [x] `make test` (83) / `make lint` still pass for the repo
- [x] Fork healthy (`manage.py check` OK, migration `0003_validation_reasons_format` applied, `makemigrations --check` clean, no hook errors in admin/api/celery/cms logs)
- [~] `make build-prod` — not required (no app/frontend change) unless compose files change
### Semantics (as built)
- `valid` = full conformance (all required fields as standard-named columns, no row errors) → `status: valid`; `warnings` = publishable but not fully conformant; `invalid` = blocking.
- Row errors: coordinates missing / outside Poland, empty required value in a standard column (except `miejscowosc` → warning), type / allowed value / pattern / range / length, duplicate `id_aed`.
- Warnings: required fields derivable from metadata (`id_aed`, `zrodlo`, `data_aktualizacji`, `dostep`), missing town, columns recognised under non-standard names, unknown columns, missing recommended columns.
- Blocking: unreadable, no rows, no usable coordinates, invalid rows > `max_invalid_ratio` (0.2), and in `?strict=true` any missing required column.
- Normaliser now also takes standard-named columns as-is (typed) — used by T13 aggregation too.
- Known limitation: `url` pointing at the fork's own API (`api.mcod.local`) times out — the fork's dev API server is single-threaded; any other host works.

### Manual Verification
1. Help: open https://api.mcod.local/1.4/aed/validate
2. `curl -sk --resolve api.mcod.local:443:127.0.0.1 -F file=@docs/demo/samples/aed-bydgoszcz-demo.csv https://api.mcod.local/1.4/aed/validate | python3 -m json.tool | head -40` → `"valid": true`
3. Same with `aed-invalid-demo.csv` → `"blocking": true` + 5 errors (row, field, code, message)
4. `curl -sk --resolve api.mcod.local:443:127.0.0.1 -H 'Content-Type: application/json' -d '{"url": "https://api.dane.gov.pl/resources/54632,defibrylatory-zlokalizowane-w-miescie-krosno/file"}' https://api.mcod.local/1.4/aed/validate` → `warnings`, column mapping (real Krosno file)
5. Admin → Zasoby → Dodaj: dataset "Defibrylatory AED – Bydgoszcz (demo)", file `aed-invalid-demo.csv`, status Opublikowany → save refused with errors at the file field; with `aed-bydgoszcz-demo.csv` → saved; reopen → green "zgodny ze standardem" message
6. Admin → resource "AED – import z błędami (test automatycznej blokady)" (40219) → red "ZASÓB ZABLOKOWANY (szkic)"; https://api.mcod.local/1.4/resources/40219/standard-validation → report; try setting status Opublikowany → refused

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-22 01:36
- **Notes / Follow-Ups:** —
