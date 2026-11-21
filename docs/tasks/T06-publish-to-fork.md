# `T06` — Publish the national AED dataset in the dane.gov.pl fork

- **Status:** `TODO`
- **Layer:** `Infra`
- **UI Design Required:** `No`
- **Depends On:** `T04`, `T05`
- **Traces To:** `REQ-09`, `REQ-07`, `DEC-004`

## Goal & User Outcome

In the running fork, the organization *Misja AED* publishes dataset *Defibrylatory AED – zbiór ogólnopolski* with resources linking to our exports; the portal downloads and indexes them and shows the table preview, map preview and `/1.4` API for it.

## Scope & Non-Goals

- **In Scope:**
  - `fork-config/publish_aed.py` (run via `manage.py shell`): idempotently create organization, dataset (category Zdrowie/HEAL if present else create, licence CC BY 4.0, tags `AED`, `defibrylatory`, `zdrowie`, update frequency `daily`), resources: CSV (primary, preview + map), XLSX, GeoJSON, JSON, Schemat (xlsx) — links `https://aed.mcod.local/api/exports/...`
  - Trigger resource validation (Celery) and set map columns (`label`=`nazwa`, `b`=`szerokosc_geograficzna`, `l`=`dlugosc_geograficzna`) in `tabular_data_schema`
  - Fallback documented: same steps by hand in admin
  - Screenshots for the presentation
- **Out of Scope:**
  - Writing to production dane.gov.pl

## UI Design (Per-Task)

N/A — backend/infra only.

## Technical Implementation Plan

- `fork-config/publish_aed.py`, README section *Publish*.
- Check: `/1.4/resources/{id}/data` and `/1.4/resources/{id}/geo` on `api.mcod.local` return our rows.

## Acceptance Criteria

- [ ] Dataset visible on `https://mcod.local` search and dataset page with 5 resources
- [ ] CSV resource has table preview and map preview with AED markers
- [ ] `https://api.mcod.local/1.4/datasets?q=defibrylatory` returns the dataset
- [ ] Re-running the script does not duplicate objects

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `T06`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes

### Manual Verification
1. `docker compose ... exec mcod-local-admin python manage.py shell < /fork-config/publish_aed.py` → prints dataset id + resource ids
2. Open dataset page → *Tabela* and *Mapa* tabs show data
3. Re-harvest in our app → re-validate resource in fork admin → updated counts

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
