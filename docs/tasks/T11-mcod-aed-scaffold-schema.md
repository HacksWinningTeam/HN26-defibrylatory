# `T11` — `mcod.aed` app inside the fork: install mechanism, schema + parsers port, `GET /1.4/aed/schema`

- **Status:** `TODO`
- **Layer:** `Backend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T05`
- **Traces To:** `REQ-01, REQ-15, DEC-014`
- **Estimate:** 2 h (incl. DEC-015 models/field)

## Goal & User Outcome

The fork runs a new Django app `mcod.aed` (tracked in `fork-config/mcod_aed/`) containing the standard AED schema and the source parsers/column mapping ported from `backend/apps/aed`; `https://api.mcod.local/1.4/aed/schema` returns the schema in the dane.gov.pl JSON:API envelope.

## Scope & Non-Goals

- **In Scope:**
  - `fork-config/mcod_aed/` package: `apps.py`, `schema.py` (FieldSpec list, v1.0.0, py3.8), `parsers/` (CSV with delimiter/encoding sniffing, XLSX, JSON, GeoJSON, XML), `mappings.py` (header synonyms + per-source overrides), `normalize.py` (coordinates, swap detection, address split, postcode), `migrations/` (models land in T13)
  - Install: `setup.sh` copies (or bind-mounts) the package to `backend_latest/mcod/aed/`; `local.py` adds `mcod.aed` to `INSTALLED_APPS`; idempotent patch registers `mcod.aed.routes` in `mcod/routes.py`
  - Falcon resource `GET /1.4/aed/schema` (envelope: `data{id,type:"aed_schema",attributes{name,version,title,description,license,groups,fields[]}}`, `links`, `meta`) + schema file downloads `/1.4/aed/schema.xlsx`, `.csv` (template), `.json` (JSON Schema)
  - `fork-config/test.sh`: runs `pytest mcod/aed/tests` in `mcod-admin`
  - DEC-015: models `DataStandard` (seed `aed-pl` v1.0.0, `max_invalid_ratio` 0.2), `DatasetStandard`, `ResourceStandardValidation` + migrations; "Standard danych" dropdown in the dataset admin form; `data_standard {code,name,version}` attribute in `/1.4/datasets[/{id}]` (idempotent patches installed by `setup.sh`)
- **Out of Scope:**
  - Models / aggregation (T13), validation endpoint (T14)

## UI Design (Per-Task)

N/A — backend/infra only (portal pages are the fork's existing UI).

## Technical Implementation Plan

- Port from `backend/apps/aed/{schema,parsers,mappings,normalize}.py`; replace 3.10+ syntax (`X | Y`, `match`, `list[str]` at runtime) with py3.8-compatible code; no new pip deps beyond what `mcod-app:local` has (check `openpyxl`, `chardet` availability; fall back to stdlib).
- Routes: follow `mcod/datasets/depricated/...`/`mcod/routes.py` pattern of Falcon views (`mcod.core.api.views`).

## Acceptance Criteria

- [ ] `curl -k https://api.mcod.local/1.4/aed/schema` → 42 fields, 6 groups, version 1.0.0, JSON:API envelope keys like other `/1.4` endpoints
- [ ] `/1.4/aed/schema.xlsx` / `.csv` / `.json` download
- [ ] Re-running `setup.sh` keeps the app installed (idempotent), fork still boots
- [ ] Dataset admin shows "Standard danych"; setting it to `aed-pl` appears as `data_standard` in `/1.4/datasets/{id}`

## Verification Checklist

### Automated Checks
- [ ] `fork-config/test.sh` passes (pytest for `mcod.aed` inside the fork's `mcod-admin` container, incl. new tests for `T11`)
- [ ] `make test` / `make lint` still pass for the repo (no regressions; `backend/` frozen)
- [ ] Fork boots cleanly after `fork-config/setup.sh` (admin, api, celery healthy; `manage.py check` OK; `mcod.aed` migrations applied)
- [~] `make build-prod` — not required (no app/frontend change) unless compose files change
### Manual Verification
1. `fork-config/setup.sh` (or `fork-config/install_aed.sh`) → `docker exec mcod-admin python manage.py check` OK
2. `curl -k --resolve api.mcod.local:443:127.0.0.1 https://api.mcod.local/1.4/aed/schema | jq '.data.attributes.fields | length'` → 42
3. Download the XLSX/CSV/JSON Schema files

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
