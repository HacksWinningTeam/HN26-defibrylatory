# `T16` — Standards defined as data (fields, synonyms, merge rule) + JSON loader

- **Status:** `VERIFIED`
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

- [x] `aed_load_standard` creates/updates "Żłobki i kluby dziecięce" (22 fields, 7 required, merge by key) and refreshes `aed-pl` (42 fields mirrored from `schema.py`); admin lists both standards with field counts and merge rules
- [x] The "Standard danych" dropdown on datasets offers both standards
- [x] Spec unit tests: definition checks, synonyms incl. real dane.gov.pl headers, JSON Schema accepts the example / rejects invalid rows, Table Schema / CSV template / XLSX, AED mirror = code schema

## Verification Checklist

### Automated Checks
- [x] `fork-config/test.sh` passes — 67 tests (incl. the aggregation-dispatch regression test); earlier 66 (9 new in `test_spec.py`, incl. replaying migration 0002 with the historical model so fresh installs still migrate); all AED tests unchanged and green
- [x] `make test` (83) / `make lint` still pass
- [x] Fork healthy (`manage.py check` OK, migration `0006_standard_definition` applied, `makemigrations --check` clean, no hook errors)

### Observed Results (2026-11-22 ~04:25)
- `fork-config/mcod_aed/standards/zlobki-pl.json`: 22 fields (required: id_placowki*, nazwa, podmiot_prowadzacy, miejscowosc, liczba_miejsc, data_aktualizacji*, zrodlo* — * filled by the portal when the column is missing), synonyms from real headers incl. broken-encoding ones (`miejscowo`, `dugo geograficzna podmiotu`, `max. liczba miejsc w obku`), merge `key` (REGON + name, else name + address), discovery terms, publish settings (category SOCI, map columns optional).
- `spec.py` (`StandardSpec`): validation of the definition, synonym map, JSON Schema / Table Schema / CSV template / XLSX from data. Admin: fields table, JSON editable for data-defined standards (checked + JSON Schema regenerated on save), AED read-only.
- Fixed before it bit: migration 0002 seeds AED with the historical model → `ensure_aed_standard` only sets fields the model has.
- Note: until T17/T18, validation and aggregation still use the AED engine — do not attach the nursery standard to datasets yet.
- Bug reported by the user during verification: "Uruchom agregację" on *Żłobki* ran the AED aggregation (button ignored the standard). Fixed: button/action pass the standard (`aggregate_task(standard_code=…)`), standards the engine cannot run yet show a warning and start nothing (`supports_aggregation`), `run_aggregation` refuses them; regression test added (67 tests).

### Manual Verification
1. `docker exec mcod-admin python manage.py aed_load_standard` → "aed-pl: 42 pól" + "zaktualizowano zlobki-pl … 22 pól"
2. Admin → sidebar *Standardy danych* → *Standardy danych (agregacja)* → two rows (AED: "odległość ≤ 25 m", Żłobki: "klucz: regon+nazwa | nazwa+miejscowosc+ulica+nr_budynku")
3. Open "Żłobki i kluby dziecięce" → *pola standardu* table (22 rows, other accepted column names) and editable JSON; open AED → table read-only
4. Datasets → any dataset → *Standard danych* dropdown lists both standards (don't save the nursery standard on a dataset yet)

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-22 04:03
- **Notes / Follow-Ups:** —
