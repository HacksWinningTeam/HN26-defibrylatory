# `T11` — `mcod.aed` app inside the fork: install mechanism, schema + parsers port, `GET /1.4/aed/schema`

- **Status:** `VERIFIED`
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

- [x] `curl -k https://api.mcod.local/1.4/aed/schema` → 42 fields, 6 groups, version 1.0.0, JSON:API envelope keys like other `/1.4` endpoints
- [x] `/1.4/aed/schema.xlsx` / `.csv` / `.json` (+ `/1.4/aed/table-schema.json`) download
- [x] Install is idempotent (bind mount + `INSTALLED_APPS`; `setup.sh` already runs `migrate`), fork boots, all services healthy
- [x] Dataset admin shows "Standard danych"; setting it to `aed-pl` appears as `data_standard` in `/1.4/datasets/{id}` and in the `/1.4/datasets` list

## Verification Checklist

### Automated Checks
- [x] `fork-config/test.sh` passes — 27 tests (unittest; pytest is not in the mcod image): schema/JSON Schema/XLSX/CSV, parsers + normalisation (ported), `/1.4/aed/schema` envelope + downloads via Falcon TestClient, seeded `aed-pl`, `data_standard` attribute, admin form/fieldsets hook
- [x] `make test` (83 passed) / `make lint` still pass for the repo
- [x] Fork boots cleanly (admin, api, cms, celery up; `manage.py check` no issues; `aed` 0001 + 0002 applied; `makemigrations aed --check` no changes; no hook errors in logs)
- [~] `make build-prod` — not required (no app/frontend change) unless compose files change
### Observed Results (2026-11-22 01:10)
- `GET /1.4/aed/schema` → 200 `application/vnd.api+json`, keys `jsonapi/links/meta/data`, `meta` keys identical to `/1.4/datasets/{id}`, `data.type=aed_schema`, 42 fields, 6 groups; downloads 200 (xlsx 16 KB, csv template, JSON Schema, Table Schema).
- Headless-Chrome admin flow: login `admin@mcod.local` → dataset 4210 → "Standard danych" = "Dane AED – wzorcowy zakres danych (aed-pl v1.0.0)" → save OK → `DatasetStandard` row → `/1.4/datasets/4210` and the `/1.4/datasets` list show `data_standard: {code: aed-pl, ...}` (test link removed afterwards). Saving dataset 4211 (T06) is blocked by an upstream form rule (licence text without a chosen licence) — unrelated to the plugin, fixed when T13 republishes that dataset.
- Implementation notes: bind mount instead of copying; no patch of `mcod/routes.py` (routes appended from `ready()`); responders accept `**kwargs` (`api_version` path param); Falcon router serves both `/aed/...` and `/1.4/aed/...` like upstream.

### Manual Verification
1. `curl -sk --resolve api.mcod.local:443:127.0.0.1 https://api.mcod.local/1.4/aed/schema | python3 -m json.tool | head -40` → envelope + `aed_schema` with 42 fields (or open https://api.mcod.local/1.4/aed/schema in the browser)
2. Download https://api.mcod.local/1.4/aed/schema.xlsx, `/1.4/aed/schema.csv`, `/1.4/aed/schema.json`
3. https://admin.mcod.local → *Standardy danych (AED) → Standardy danych* → "Dane AED – wzorcowy zakres danych" (code `aed-pl`, v1.0.0, JSON Schema)
4. https://admin.mcod.local → Zbiory danych → any dataset → tab *Ogólne*: field **Standard danych** under the categories; choose "Dane AED", save → https://api.mcod.local/1.4/datasets/{id} shows `"data_standard": {"code": "aed-pl", ...}`; set it back to "— brak —" afterwards
5. `fork-config/test.sh -v` → 27 OK

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-22 01:20
- **Notes / Follow-Ups:** User decision (2026-11-22 01:20): one data standard per dataset (`DatasetStandard` stays one-to-one); standards stay code-defined (no admin-defined structures). Demo sample files in `docs/demo/samples/`.
