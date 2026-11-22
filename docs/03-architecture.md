# 03 — System Architecture

> Living technical architecture for backend, API contract, frontend routes, and integrations. Updated by `hackathon-plan`, `hackathon-ui-design` (when UI requires new fields/endpoints), and `hackathon-update-plan`. Key choices logged in `DEC-004`.

## Pivot (DEC-014, 2026-11-22): Everything Inside the dane.gov.pl Fork — `mcod.aed`

> This section is authoritative. Sections below describe the pre-pivot architecture (our separate `backend/`), now retired from the demo but kept in the repo.

```text
 api.dane.gov.pl/1.4 + dane.um.warszawa.pl API + OpenAEDMap (OSM)
        |  manage.py aed_import_sources (T12): mirror institutions + AED datasets
        v
 [dane.gov.pl fork: Django 2.2 admin / Falcon API / Celery / ES]   app mcod.aed (fork-config/mcod_aed -> backend_latest/mcod/aed)
   AED source datasets (tag AED): file resources (ResourceFile) | API/link resources ("connected APIs")
        |  aed_aggregate (T13): command | Celery task | admin "Agregacja AED"
        v
   parsers + mapping + normalize (T11, ported)  ->  AedSourceRecord (standard fields, flags, coverage)
        |  -> converted CSV resource "… – wersja zgodna ze wzorcem AED" on each source dataset
        v
   merge/dedupe (DEC-011 rules)  ->  AedDevice  ->  common dataset "Defibrylatory AED – zbiór ogólnopolski"
        (org Misja AED; CSV table+map, XLSX, GeoJSON, schema XLSX as native ResourceFiles; /1.4/datasets, /resources/{id}/data|geo)
   Falcon /1.4/aed/schema | POST /1.4/aed/validate (T14) | /1.4/aed/sources | /1.4/aed/devices
        |
 Next.js map (T07 UI) -> same-origin route -> fork API (T15, DANEGOV_API_URL)
```

- **Code location & install (as built in T11):** `fork-config/mcod_aed/` (tracked) is **bind-mounted** at `/usr/src/mcod_backend/mcod/aed` in all app containers (`fork-config/compose.override.yml`); `INSTALLED_APPS += ["mcod.aed.apps.AedConfig"]` in `fork-config/local.py`; migrations via the normal `migrate` in `setup.sh`. **No upstream file is edited**: `AedConfig.ready()` → `integration.py` appends routes to `mcod.routes.routes` (+ `/{api_version}` variants) in the api container, adds `data_standard` to `DatasetApiAttrs`, and wraps `DatasetAdminMixin.form/get_fieldsets/save_model` in the admin container. Tests: `fork-config/test.sh` (unittest, no pytest in the image).
- **Runtime:** Python 3.8, Django 2.2, Falcon 4 (`mcod-app:local` image); no new pip dependencies unless already in the image.
- **Models:** `AedImportRun(started_at, finished_at, status, report JSON)`, `AedSourceRecord(resource FK, row_no, raw JSON, data JSON keyed by schema fields, lat, lon, valid, quality_flags JSON, device FK)`, `AedDevice(id_aed unique, data JSON, lat, lon, sources_count)`.
- **API (dane.gov.pl 1.4 JSON:API envelope `data/links/meta`, `jsonapi`):**

| Method & Path | Purpose | Task |
| --- | --- | --- |
| `GET /1.4/aed/schema` (+ `.xlsx`, `.csv` template, `.json` JSON Schema) | Standard structure | T11 |
| `POST /1.4/aed/validate` (multipart `file` / JSON `url` / JSON `resource_id`), `GET` = help | Validate data against the structure: errors/warnings per row+field, column mapping, coverage | T14 |
| `GET /1.4/aed/sources` | Per-source status, records, coverage per field, quality flags, last run | T13 |
| `GET /1.4/aed/devices?bbox=&q=` | GeoJSON FeatureCollection, DEC-008 property contract (map) | T13 |
| `GET /1.4/resources/{id}/standard-validation` | Stored automatic validation result of a resource in a standard dataset | T14 |
| `data_standard` attribute in `GET /1.4/datasets[/{id}]` | Which standard (bigger dataset) a dataset belongs to | T11 |

- **Data standards & dataset field (DEC-015):** `DataStandard(code "aed-pl", name, version, json_schema, target_dataset, max_invalid_ratio=0.2, is_active)`; `DatasetStandard(dataset OneToOne, standard FK)` = "Standard danych" dropdown in dataset admin + `data_standard` attribute in `/1.4/datasets`; `ResourceStandardValidation(resource OneToOne, status, blocking, rows_total, rows_invalid, errors, coverage, validated_at, standard_version)` → `GET /1.4/resources/{id}/standard-validation`. Blocking (unreadable / required columns missing / invalid rows > ratio): admin upload rejected synchronously in the resource form; other paths validated after the fork's file/data Celery tasks → resource set to `draft`. Aggregation = datasets with standard `aed-pl`, non-blocked resources only.
- **Connectors (source resources):** file → main `ResourceFile`; link/API → generic CSV/JSON/GeoJSON URL, OpenAEDMap PL GeoJSON, Warsaw `POST .../api/action/<aed action>` with `WARSAW_API_TOKEN` (fork env; missing → `requires_api_key`, run continues).
- **Tests:** `fork-config/test.sh` → `pytest mcod/aed/tests` inside `mcod-admin` (pure logic: schema, parsers, mapping, validation, merge; API smoke via Falcon test client if the fork's test settings allow).
- **Frontend:** T07 UI unchanged; data from `/1.4/aed/devices` + `/1.4/aed/sources` (T15).

## High-Level Data Flow

```text
                 api.dane.gov.pl/1.4 (search + resources)      OSM Overpass (emergency=defibrillator, PL)
                                 \                               /
                                  v                             v
  [our Django: apps.aed]  harvest_aed command -> SourceDataset/SourceResource (raw file stored)
                                  -> per-source parser + FieldMapping -> SourceRecord (standard schema)
                                  -> merge/dedupe -> AED (national, with provenance) -> coverage report
                                  -> /api/1.4/... (dane.gov.pl-compatible JSON:API) + /api/exports/aed.{csv,json,geojson,xlsx}
                                  -> /api/schema-standard/... (xlsx / csv template / JSON Schema / Table Schema)
                                  |
          https://aed.mcod.local (fork nginx proxy -> host:8000) 
                                  v
  [local dane.gov.pl fork: dane-gov-pl/]  Organization "Misja AED" -> Dataset "Defibrylatory AED – zbiór ogólnopolski"
                                  -> Resources (links to our exports) -> Celery downloads + ES indexing
                                  -> portal dataset page, table preview, map preview, /1.4 API (https://mcod.local)

  Browser (same-origin) -> our Next.js 16 (/ "Najbliższy AED" map from demo location, /schemat) -> src/proxy.ts -> Django -> PostgreSQL 18
```

## Standard AED Schema ("wzorcowy zakres danych") — single source of truth

- Defined once in `backend/apps/aed/schema.py` as an ordered list of `FieldSpec(name, type, required, description_pl, description_en, example, allowed_values, format)`. Everything else is generated from it: the `AED` model columns mirror it, exports use its column order, and the `.xlsx` / CSV template / JSON Schema / Frictionless Table Schema are rendered from it.
- Column names are Polish `snake_case` in ASCII, matching dane.gov.pl conventions and the address/TERYT pattern already used by Legionowo (`cecha_ulicy`, `nazwa_ulicy`, `nr_budynku`, `kod_terc`, `kod_simc`, `szerokosc_geograficzna`, `dlugosc_geograficzna`).
- Draft field groups (finalized in T01):
  - **Identyfikacja:** `id_aed`, `nazwa`, `zrodlo_id`
  - **Lokalizacja:** `szerokosc_geograficzna`, `dlugosc_geograficzna` (WGS84, required), `wojewodztwo`, `powiat`, `gmina`, `miejscowosc`, `kod_terc`, `kod_simc`, `cecha_ulicy`, `nazwa_ulicy`, `nr_budynku`, `nr_lokalu`, `kod_pocztowy`, `opis_lokalizacji` (e.g. "hall, next to reception"), `w_budynku`, `pietro`
  - **Dostępność:** `dostep` (`publiczny` / `ograniczony` / `prywatny`), `godziny_dostepnosci` (OSM `opening_hours` syntax, e.g. `24/7`), `calodobowy`, `wymaga_klucza`
  - **Urządzenie:** `producent`, `model`, `status` (`sprawny` / `niesprawny` / `nieznany`), `data_ostatniego_przegladu`, `data_waznosci_elektrod`, `data_waznosci_baterii`
  - **Dysponent / kontakt:** `dysponent`, `telefon_kontaktowy`, `email_kontaktowy`
  - **Metadane:** `zrodlo` (source name), `zrodlo_url`, `data_aktualizacji`, `zweryfikowany`

## Backend Apps & Data Models (`backend/`)

- **`apps.core`**: Built-in `GET /api/health/` readiness check.
- **`apps.aed`** (new):
  - `SourceDataset`: `kind` (`dane_gov_pl` / `osm`), `external_id` (dane.gov.pl dataset id), `title`, `publisher`, `url`, `license_name`, `harvested_at`.
  - `SourceResource`: FK `SourceDataset`, `external_id`, `format`, `url`, `raw` (BinaryField, stored raw payload — no media files, safe for the non-root prod container), `selected` (bool, chosen best format per dataset: GeoJSON > CSV > XLSX > JSON > XML), `parse_status`, `parse_error`, `record_count`, `coverage` (JSON: field -> filled ratio).
  - `SourceRecord`: FK `SourceResource`, `source_row_id`, `raw` (JSON original row), `data` (JSON keyed by standard schema fields, normalized), `lat`/`lon`, `valid`, `quality_flags` (JSON list), FK `aed` (set by merge) — DEC-011.
  - `AED`: national merged record; `data` (JSON keyed by standard schema fields), `lat`/`lon`, `id_aed` (`PL-AED-` + hash of top source record key), `sources_count`; provenance via `SourceRecord.aed` — DEC-011.
  - Parsers: `apps/aed/parsers/` (`csv_generic.py` with delimiter/encoding sniffing, `xlsx.py`, `geojson.py`, `osm.py`) + `mappings.py` (header synonyms -> standard fields, plus per-source overrides, e.g. Marki: row-wrapped quoting and lat/lon swapped under lon/lat headers).
  - Services: `harvest.py` (dane.gov.pl API client + Overpass client, retries, timeouts), `normalize.py` (coordinates validation inside PL bbox, swap detection, address splitting, postcode regex), `merge.py` (greedy dedupe: ≤ 25 m, or ≤ 75 m + name/address similarity; never two records of one resource per cluster; precedence dane.gov.pl > OSM; first non-empty wins; municipal coordinate checks — DEC-011), `sources_report.py` (`/api/sources/`).
  - Management commands: `harvest_aed` (fetch + parse + merge; `--offline` uses committed snapshot), `load_aed_snapshot` (demo fallback, idempotent).

## API Endpoints Overview (`drf-spectacular`)

dane.gov.pl-compatible endpoints mimic the portal's JSON:API envelope (`data[]{id,type,attributes,relationships,links.self}`, top-level `links` (self/first/last/next/prev), `meta` (count, language, params, path, rel_uri)), and the `?page=&per_page=&q=&sort=` params.

| Method & Path | View / App | Purpose | Auth / Permissions | Task |
| --- | --- | --- | --- | --- |
| `GET /api/health/` | `HealthCheckView` (`apps.core`) | DB + service readiness | Public | Starter |
| `GET /api/schema/`, `/api/docs/`, `/api/redoc/` | `drf-spectacular` | OpenAPI 3 spec & docs UI | Public | Starter |
| `GET /api/schema-standard/` | `apps.aed` | Standard AED schema as JSON (field list) | Public | T01 |
| `GET /api/schema-standard/aed-schema.xlsx`, `.csv`, `.json` (JSON Schema), `table-schema.json` | `apps.aed` | Schema downloads | Public | T01 |
| `GET /api/sources/` | `apps.aed` | Harvested sources + coverage per standard field + record counts | Public | T02/T03 |
| `GET /api/1.4/datasets` , `/api/1.4/datasets/{id}` | `apps.aed` | Our national dataset (+ source datasets) in dane.gov.pl dataset shape | Public | T04 |
| `GET /api/1.4/datasets/{id}/resources`, `/api/1.4/resources/{id}` | `apps.aed` | Export resources (csv/json/geojson/xlsx) in dane.gov.pl resource shape | Public | T04 |
| `GET /api/1.4/resources/{id}/data` | `apps.aed` | Rows as `type: "row"`, `attributes.col1..colN`, `meta.headers_map`, `meta.data_schema` | Public | T04 |
| `GET /api/exports/aed.csv`, `.json`, `.geojson`, `.xlsx` | `apps.aed` | Machine-readable exports of merged dataset (CSV is UTF-8, `,`, numeric lat/lon for the fork map) | Public | T04 |
| `GET /api/aed/?bbox=&q=` | `apps.aed` | Lightweight GeoJSON for our Next.js map (property contract below, DEC-008) | Public | T04/T07 |

### `/api/aed/` map contract (DEC-008, consumed by T07)

- `FeatureCollection` + `meta {count, generated_at, license}`; each feature `id` = `id_aed`, `geometry` Point `[lon, lat]`.
- `properties`: `id_aed`, `nazwa`, `adres` (server-built display string or `null`), `miejscowosc`, `opis_lokalizacji`, `w_budynku` (bool/`null`), `pietro`, `dostep`, `godziny_dostepnosci`, `zabezpieczenie`, `status`, `dysponent`, `telefon_kontaktowy`, `data_aktualizacji`, `zrodla[] {nazwa, typ (dane_gov_pl|osm), url}`. Schema names + enum codes from `schema.py`; empty values are `null`.
- The UI loads the full set once (no params) and filters client-side; `q` / `bbox` remain for API users. `GZipMiddleware` enabled so ~20k features stay ≈ 1 MB on the wire.
- `/api/sources/` additionally exposes top-level `aed_count`, `updated_at` and `sources[].{id, title, kind, url, record_count}` for the landing counters.

## Frontend Routes & Modules (`frontend/`)

| Route | Component / Type | Purpose | API Endpoints Used | Task |
| --- | --- | --- | --- | --- |
| `/` | `src/app/page.tsx` + client `AedFinder` (Leaflet, clustered) | Single page "Najbliższy AED" from the demo location (BCTW Bydgoszcz, DEC-010): nearest card, nearby list, map, data info | `GET /api/aed/`, `GET /api/sources/` | T07 |
| `/mapa` | `src/app/mapa/page.tsx` | Redirect to `/` (DEC-010) | — | T07 |
| `/schemat` | `src/app/schemat/page.tsx` | Standard schema table + downloads + per-source coverage | `GET /api/schema-standard/`, `GET /api/sources/` | T08 |

## dane.gov.pl Fork — `fork-config/` (tracked) + `dane-gov-pl/` (git-ignored); local first, then Hetzner (DEC-005)

- `fork-config/` holds everything we change: `backend.env` (copied to `dane-gov-pl/backend_latest/.env`, `DISCOURSE_FORUM_ENABLED=false`), `local.py`, `compose.override.yml` (drops discourse/flower/rdfdb deps, resets conflicting host ports, adds `aed.mcod.local` alias), `nginx/07-aed.conf.template` (https `aed.mcod.local` -> `http://host.docker.internal:8000`), `setup.sh` (build, init_mcod_db, ES index, start), `publish_aed.py` + `publish.sh` (Django-shell script: create organization "Misja AED", dataset with category HEAL/tags/licence conditions, resources = CSV/XLSX/GeoJSON/schema files downloaded from `https://aed.mcod.local` and uploaded, plus an API-type JSON link to `/api/1.4/resources/1/data`; CSV columns typed + map columns in `tabular_data_schema`; idempotent, re-uploads on change — DEC-013), `README.md`.
- Local hosts (one-time, sudo): `127.0.0.1 mcod.local api.mcod.local admin.mcod.local cms.mcod.local aed.mcod.local` (fork subnet moved off `172.18.0.0/16`, which collides with an existing local docker network); `vm.max_map_count` already OK locally.
- **Hetzner (T10):** fork in `/home/github/apps/danegov-fork/` (outside CI rsync dir), single public port `3080` (fork nginx, https self-signed), hostnames `mcod.<ip>.sslip.io` / `api.` / `admin.` / `aed.` (wildcard DNS, no hosts edits for judges), `aed.` proxies to our app on the host (`host-gateway:3002`, our server `FRONTEND_PORT`); server has 15 GB RAM + swap so ES keeps 1 GB heap; images built locally and shipped with `docker save | ssh docker load`; Angular built once (`ng build`) and served statically by the fork nginx.
- Services used (DEC-006): `mcod-db`, `mcod-redis`, `mcod-rabbitmq`, `mcod-elasticsearch`, `mcod-nginx`, `mcod-smtp`, `mcod-admin`, `mcod-api`, `mcod-celery`, `mcod-cms`, `mcod-frontend` (Angular `ng serve -c local` in a container on the fork network 172.28.18.0/24). Scripts: `fork-config/setup.sh` (first run, idempotent), `start.sh`, `stop.sh` (never `-v`), `fork-compose.sh <args>`.
- Constraints: links must be https (forms.py:683, link_validation.py:92 — `verify=False`, self-signed OK); JSON links classify as "api" (no preview) → CSV is the primary previewed resource; map preview requires numeric lat/lon + label columns.

## Environment Variables & External Integrations

- Only optional new env var: `DANEGOV_FORK_URL` (server-side, landing link to the fork dataset; hidden when empty; T07 mirrors it in `.env.example`, `compose.yaml`, `compose.prod.yaml`). Public APIs, no keys. Constants in `apps/aed/harvest.py`: `DANE_API_URL=https://api.dane.gov.pl/1.4`, `OSM_PRIMARY_URL=https://openaedmap.org/api/v1/countries/PL.geojson` (daily OSM AED export; Overpass is the fallback — unreachable from the dev network on 2026-11-21), timeout 60 s, 3 retries. If made configurable later, mirror in `.env.example`, `compose.yaml`, `compose.prod.yaml`.
- Local port conflicts with the fork: fork host ports for postgres/redis/rabbit/ES are reset in `fork-config/compose.override.yml`; our stack keeps `8000` (backend) and `3000` (frontend).
- Map tiles: OpenStreetMap standard tiles with attribution (demo traffic only). OSM data: ODbL, attribution in exports metadata and map.

## Hackathon Simplifications & Tradeoffs

- Harvest is a management command (run manually / on deploy), not a scheduled job.
- Dedupe uses simple distance + string similarity (stdlib `difflib`), no PostGIS; bbox filtering in Python/SQL floats is enough for ~10–20k points.
- dane.gov.pl compatibility = same envelope/attribute names for the subset we serve, not the full portal API.
- Publishing into the fork via Django shell script instead of a write API (the portal has no public write API).
- A committed raw snapshot (`backend/apps/aed/fixtures/snapshot/`, labelled demo/offline) protects the demo if an external source is down.
