# `T17` — Generic validation for any standard + `/1.4/standards/{code}/…` API

- **Status:** `VERIFIED`
- **Layer:** `Backend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T16`
- **Traces To:** `REQ-15`, `REQ-16`, `DEC-019`
- **Estimate:** 1 h

## Goal & User Outcome

Validation (upload blocking, background validation, stored results, API) works for any data-defined standard with the same rules as AED.

## Scope & Non-Goals

- **In Scope:**
  - `generic_validation.py`: column mapping by exact name + synonyms, type/required/allowed values/pattern/range/length checks, coordinates only if the spec has them, blocking threshold from the standard
  - `resource_validation.validate_resource` + admin form hook dispatch: `aed-pl` → existing code, other standards → generic
  - API: `GET /1.4/standards`, `GET /1.4/standards/{code}/schema` (+ `.xlsx`/`.csv`/`.json`), `GET|POST /1.4/standards/{code}/validate`
- **Out of Scope:**
  - Changing the verified AED code path; full admin field editor (DEC-019)

## UI Design (Per-Task)

N/A — backend/infra only (portal admin/portal pages are existing UI).

## Acceptance Criteria

- [x] `zlobki-valid-demo.csv` → `valid`; `zlobki-invalid-demo.csv` → 9 errors (type, pattern, allowed value, minimum, required, duplicate id), blocking; `zlobki-legacy-demo.csv` (real Inowrocław-style headers incl. broken encoding) → all columns mapped by synonyms, `warnings`, not blocking (`?strict=true` → blocking)
- [x] Admin upload rule + background validation dispatch per standard: a nursery resource with the invalid file → stored `invalid` for `zlobki-pl`, set to draft; the form refuses the invalid file and accepts the valid one (tested in a rolled-back transaction; live admin check with real nursery datasets in T18)
- [x] All AED validation tests unchanged and green; live re-validation of Krosno / Legionowo original / corrected copy gives the same results as before

## Verification Checklist

### Automated Checks
- [x] `fork-config/test.sh` passes — 75 tests (8 new in `test_generic.py`: coercion, valid/invalid/legacy files, strict, unmappable file, AED vs generic dispatch, nursery resource blocking + form rule, `/1.4/standards` API)
- [~] `make test` / `make lint` — not affected (no repo code changed in T17; last run green in T16)
- [x] Fork healthy (no migration changes, no hook errors)

### Observed Results (2026-11-22 ~04:40)
- `generic.py`: column mapping (exact name, then declared synonyms; geometry only if the spec has coordinates), lenient-but-reported coercion (e.g. "tak" → true, "22/11/2026" → 2026-11-22, "276-115-858" → REGON digits, "Klub dziecięcy" → `klub_dzieciecy` = warnings `value_converted`), same report shape and blocking rules as AED. `validation.validate_for_standard()` is the single entry point used by the admin form, the background validation and the API (`aed-pl` → verified AED rules).
- API: `GET /1.4/standards`, `GET /1.4/standards/{code}/schema` (+ `.xlsx`, `.csv` template, `.json` JSON Schema, `table-schema.json`), `GET|POST /1.4/standards/{code}/validate`; unknown standard → 404; `/1.4/aed/*` unchanged (incl. the help resource type).
- Samples: `docs/demo/samples/zlobki-{valid,invalid,legacy}-demo.csv` (invented demo data, labelled "(demo)").

### Manual Verification
1. https://api.mcod.local/1.4/standards → two standards; https://api.mcod.local/1.4/standards/zlobki-pl/schema and `/schema.xlsx`
2. `curl -sk --resolve api.mcod.local:443:127.0.0.1 -F file=@docs/demo/samples/zlobki-invalid-demo.csv https://api.mcod.local/1.4/standards/zlobki-pl/validate | python3 -m json.tool | less` → `"blocking": true`, 9 errors
3. Same with `zlobki-legacy-demo.csv` → `"status": "warnings"`, `column_mapping` shows "miejscowo" → `miejscowosc`, "max. liczba miejsc w obku" → `liczba_miejsc`
4. `curl … -F file=@docs/demo/samples/aed-invalid-demo.csv https://api.mcod.local/1.4/aed/validate` → AED result unchanged (3 invalid rows)

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-22 04:10
- **Notes / Follow-Ups:** —
