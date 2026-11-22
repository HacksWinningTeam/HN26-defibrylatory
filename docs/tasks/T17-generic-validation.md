# `T17` — Generic validation for any standard + `/1.4/standards/{code}/…` API

- **Status:** `TODO`
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

- [ ] A nursery CSV with the standard's columns → `valid`; a broken one (missing `nazwa`, `liczba_miejsc` = "dużo") → errors per row/field, blocking
- [ ] Uploading the broken file to a dataset with standard "Żłobki…" in the admin is refused
- [ ] All AED validation tests unchanged and green

## Verification Checklist

### Automated Checks
- [ ] `fork-config/test.sh` passes (incl. new tests for `T17`; all AED tests unchanged and green)
- [ ] `make test` / `make lint` still pass for the repo
- [ ] Fork healthy (`manage.py check`, migrations applied, no hook errors)

### Manual Verification
1. `curl -sk -F file=@… https://api.mcod.local/1.4/standards/zlobki-pl/validate`
2. Admin upload of the invalid nursery sample → refused

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
