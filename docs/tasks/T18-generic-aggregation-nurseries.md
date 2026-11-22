# `T18` — Generic aggregation + nursery datasets imported from dane.gov.pl

- **Status:** `TODO`
- **Layer:** `Backend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T17`
- **Traces To:** `REQ-15`, `REQ-16`, `DEC-019`
- **Estimate:** 1 h

## Goal & User Outcome

Nursery datasets of several municipalities (CSV + XLSX, different columns) are imported into the portal with standard "Żłobki…", validated, merged and published as "Żłobki i kluby dziecięce – zbiór zbiorczy" by the same engine and the same admin button.

## Scope & Non-Goals

- **In Scope:**
  - Generic conversion (spec mapping + type coercion + address split), merge strategy `key` (REGON, else normalised name + address), records stored per standard
  - Publish: common dataset per standard from `publish` settings — CSV (table preview; map only if coordinates), XLSX, schema XLSX
  - Importer driven by `discovery` (search terms, title pattern, max datasets) → 6–8 nursery datasets mirrored with "Standard danych" = zlobki-pl
  - `aed_aggregate --standard <code>` and the admin "Uruchom agregację" button per standard; `/1.4/standards/{code}/sources`
- **Out of Scope:**
  - Changing the verified AED code path; full admin field editor (DEC-019)

## UI Design (Per-Task)

N/A — backend/infra only (portal admin/portal pages are existing UI).

## Acceptance Criteria

- [ ] `aed_import_sources --standard zlobki-pl` mirrors ≥ 6 nursery datasets of different institutions
- [ ] Aggregation → common nursery dataset with table preview; report per source (rows, accepted, coverage)
- [ ] AED aggregation unchanged (6 sources → 18,776 AEDs)

## Verification Checklist

### Automated Checks
- [ ] `fork-config/test.sh` passes (incl. new tests for `T18`; all AED tests unchanged and green)
- [ ] `make test` / `make lint` still pass for the repo
- [ ] Fork healthy (`manage.py check`, migrations applied, no hook errors)

### Manual Verification
1. Admin → Standardy danych → "Żłobki…" → Uruchom agregację → Agregacje AED shows the nursery run
2. Portal → "Żłobki i kluby dziecięce – zbiór zbiorczy" → CSV → Tabela

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
