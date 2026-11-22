# `T16` — Standards defined as data (fields, synonyms, merge rule) + JSON loader

- **Status:** `TODO`
- **Layer:** `Backend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T13`
- **Traces To:** `REQ-15`, `REQ-16`, `DEC-019`
- **Estimate:** 1 h

## Goal & User Outcome

A data standard is described by data — fields with types/obligation/allowed values/patterns/synonyms, a merge rule, discovery terms and publish settings — loaded from a JSON file and visible in the admin; AED is mirrored into the same format.

## Scope & Non-Goals

- **In Scope:**
  - `DataStandard`: `fields` JSON, `merge` JSON, `discovery` JSON, `publish` JSON (+ migration); `spec.py`: `StandardSpec` built from a `DataStandard` (field lookup, required/derivable fields, synonyms, JSON Schema + Table Schema + CSV template + XLSX generated from the spec)
  - `fork-config/mcod_aed/standards/zlobki-pl.json` (~15 fields) and command `aed_load_standard <file>` (idempotent, by `code`); `aed-pl` definition generated from `schema.py` into the same format (display only)
  - Admin: standard page shows the fields table (read-only) + JSON editable
- **Out of Scope:**
  - Changing the verified AED code path; full admin field editor (DEC-019)

## UI Design (Per-Task)

N/A — backend/infra only (portal admin/portal pages are existing UI).

## Acceptance Criteria

- [ ] `aed_load_standard standards/zlobki-pl.json` creates/updates "Żłobki i kluby dziecięce"; admin lists both standards with field counts
- [ ] The "Standard danych" dropdown on datasets offers both standards
- [ ] Spec unit tests: field lookup, synonyms, JSON Schema accepts valid / rejects invalid rows

## Verification Checklist

### Automated Checks
- [ ] `fork-config/test.sh` passes (incl. new tests for `T16`; all AED tests unchanged and green)
- [ ] `make test` / `make lint` still pass for the repo
- [ ] Fork healthy (`manage.py check`, migrations applied, no hook errors)

### Manual Verification
1. `docker exec mcod-admin python manage.py aed_load_standard mcod/aed/standards/zlobki-pl.json`
2. Admin → Standardy danych → both standards; open "Żłobki…" → fields

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
