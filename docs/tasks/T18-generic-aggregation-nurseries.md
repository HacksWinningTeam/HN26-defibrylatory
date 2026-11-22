# `T18` — Generic aggregation + nursery datasets imported from dane.gov.pl

- **Status:** `VERIFIED`
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

- [x] `aed_import_sources --standard zlobki-pl` mirrors 8 nursery datasets of 8 institutions (Gdynia, Krosno, Inowrocław, Zabrze, Wyry, Tychy, Wojkowice, Tarnowskie Góry) — discovery from the standard's `discovery` settings, real file format from the URL extension
- [x] Aggregation (command or admin button) → "Żłobki i kluby dziecięce – zbiór zbiorczy" (4306) with CSV (Tabela 85 rows + Mapa), XLSX, schema XLSX, API link; report per source (rows, accepted, coverage, column mapping); `/1.4/standards/zlobki-pl/sources`
- [x] AED aggregation unchanged (6 sources → 18,776 AEDs)

## Verification Checklist

### Automated Checks
- [x] `fork-config/test.sh` passes — 78 tests (new: format from URL, address split / derived fields / town suffix, merge by key incl. "same resource never merged", full generic run on the three nursery samples, per-standard admin dispatch); AED tests green
- [~] `make test` / `make lint` — not affected (no repo code changed)
- [x] Fork healthy (migration `0007_device_optional_coordinates`, no hook errors, no missing migrations)

### Observed Results (2026-11-22 ~05:25)
- Real-data findings handled by data, not code: GZM-metropolis files (Zabrze, Tychy, …) are an English export of the national nursery register (`businessPlaceName`, `operatorRegon`, `businessPlaceInstitutionType = NURSERY`) → synonyms + value aliases added to `zlobki-pl.json` (v1.0.2); their "xlsx" resources are really RDF/CSV → format from the file extension. Until the synonyms existed the 5 files were correctly blocked ("no column matches the standard"); after the standard update they passed and were **re-published automatically** (new: automatic un-blocking when a blocked resource later passes).
- Generic engine: conversion by the standard (synonyms, coercion), derived fields (id, source, date, address parts from a full address, "Tychy, miasto" → "Tychy"), invalid rows excluded, merge by key (REGON + name, else name + address; never within one resource) — 85 records → 85 nurseries (cities do not overlap).
- Common CSV preview: coordinate columns stay text for generic standards (many nurseries have no coordinates; the portal map parses text) → Tabela 85 rows, Mapa for the ones with coordinates.

### Manual Verification
1. Admin → *Standardy danych (agregacja)* → "Żłobki i kluby dziecięce" → **Uruchom agregację** → *Agregacje AED*: new run (zlobki-pl) "zakończona", 8 sources, 85 objects
2. Portal https://mcod.local/pl/dataset?q=żłobki → 8 source datasets + "Żłobki i kluby dziecięce – zbiór zbiorczy" → CSV → **Tabela** (85) / **Mapa**
3. https://api.mcod.local/1.4/standards/zlobki-pl/sources → 8 sources with coverage and column mapping
4. Admin → *Zbiory danych* → "Tychy: Rejestr żłobków…" → *Standard danych* = Żłobki; its resource page shows the validation message; *Zasoby → Dodaj* to that dataset with `docs/demo/samples/zlobki-invalid-demo.csv` → refused
5. AED still: Uruchom agregację on "Dane AED" → 6 sources, 18,776

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-22 04:28
- **Notes / Follow-Ups:** —
