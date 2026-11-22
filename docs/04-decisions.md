# 04 — Decision & Change Log

> Append-only log of architecture decisions, requirement clarifications, UI pivots, and mid-hackathon scope changes. Every agent must read this file before designing or implementing any task.

## When to Add a Decision (`DEC-XXX`)

- At kickoff when establishing initial MVP scope and constraints (`DEC-001`).
- Whenever new organizer info, mentor feedback, or extra user notes arrive.
- Whenever a task's UI design requires adding/changing API endpoints, models, or shared UI primitives.
- Whenever a planned task is split, modified, or `CANCELLED`.

## Decisions

### `DEC-000` — Template Baseline & Architecture Invariants
- **Date:** Initial template setup
- **Status:** Accepted
- **Context:** Full-stack hackathon template targeting fast vertical slices and automatic Hetzner deployment.
- **Decision:** Keep single-port Next.js 16 proxying (`frontend/src/proxy.ts` + `skipTrailingSlashRedirect`), PostgreSQL 18 (`/var/lib/postgresql`), `uv` (`/opt/venv`), WCAG 2.2 AA light UI baseline, mandatory unit tests + lint/typecheck/schema checks, and manual `git push`.
- **Affected Docs & Tasks:** `AGENTS.md`, `docs/02-ui-system.md`, `docs/03-architecture.md`.

### `DEC-001` — Appearance, i18n, and WCAG 2.2 AA Accessibility Configuration
- **Date:** 2026-11-21 14:36
- **Status:** Accepted
- **Context / New Info:** User requested an exact copy of the appearance, language (i18n), and WCAG accessibility configuration from `/Users/kubamilcarz/Developer/HackNation-2026/HN26-PCI`.
- **Decision:** Imported the full `appearance/` (`system`, `light`, `dark`, `hc-black-white`, `hc-black-yellow`, `grayscale`), `i18n/` (`pl-PL` default, `en-US`), and `components/accessibility/` + `/settings/accessibility` WCAG 2.2 AA system (pre-hydration script, CSS semantic tokens, `AccessibilityProvider`, `AccessibilityMenu`, `textScale` 25%–200%, `underlineLinks`, `Read aloud` via `speechSynthesis`, and `node --test` unit tests).
- **Affected Docs & Tasks:** `docs/02-ui-system.md`, `docs/accessibility-system.md`, `frontend/package.json`, `frontend/src/app/`, `frontend/src/appearance/`, `frontend/src/i18n/`, `frontend/src/components/`, `frontend/src/lib/`.

### `DEC-002` — Kickoff: "Misja AED" MVP Scope, Timeline, and dane.gov.pl Fork
- **Date:** 2026-11-21 18:00
- **Status:** Accepted (fork-hosting part superseded by DEC-005)
- **Context / New Info:** Organizer brief "Misja AED – Dane na ratunek" (`docs/inputs/organizer-brief/brief.pdf`, transcribed to `brief.md`). Deadline 2026-11-22 11:00. User: the common schema is the most important part; harvest all AED data from dane.gov.pl (+ OSM), merge into one file, expose dane.gov.pl-compatible API, and run a local fork of dane.gov.pl (upstream code copied into `dane-gov-pl/`) showing the data. A live API check on 2026-11-21 found ~5 real AED datasets on dane.gov.pl (Krosno, Marki, Przemyśl, Legionowo, generic "Lokalizacja defibrylatorów (AED)") with heterogeneous formats.
- **Decision:** MVP = standard schema (+ `.xlsx`/CSV/JSON Schema), harvester (dane.gov.pl API + OSM Overpass), per-source mapping + coverage report, merge/dedupe with provenance, `/1.4`-style JSON:API endpoints + open exports, and the merged dataset published in the local fork (resources pointing to our exports). Fork runs locally only, without Discourse; setup timeboxed ~2 h with a Next.js dataset-page fallback. `dane-gov-pl/` is git-ignored; fork config/overrides tracked separately. Code freeze 2026-11-22 09:00. Branding (logo/slogan/brand book, 25%) is a required deliverable with owner still open.
- **Affected Docs & Tasks:** `docs/01-brief.md`, `AGENTS.md`, `docs/inputs/my-notes.md`, `docs/02-ui-system.md`, `.gitignore`.

### `DEC-003` — Brief Approved + AED Map in Next.js
- **Date:** 2026-11-21 18:03
- **Status:** Accepted
- **Context / New Info:** User approved `docs/01-brief.md` and asked for a map visualisation of AEDs in our Next.js app at the end.
- **Decision:** Added `REQ-13` (Must): interactive map of merged AEDs in Next.js, scheduled last after the data pipeline and fork tasks. Removed it from Nice-to-Have. Map library chosen in `docs/03-architecture.md`.
- **Affected Docs & Tasks:** `docs/01-brief.md`, `docs/02-ui-system.md`; tasks created by `hackathon-plan`.

### `DEC-004` — Architecture: Schema-First Pipeline, dane.gov.pl-Compatible API, Fork Integration
- **Date:** 2026-11-21 18:10
- **Status:** Accepted — superseded in part by DEC-014 (pipeline/API move into the fork as `mcod.aed`)
- **Context / New Info:** Plan created. Fork investigation: resource links must be `https://` (fork `forms.py:683`, `link_validation.py:92`, cert not verified); JSON links are classified as "api" (no preview); map preview needs a tabular resource with numeric lat/lon + label columns; fork publishes host ports 5432/6379/9200/80/443 etc.; app image is Python 3.8 (20–40 min build). Real sources inspected: Krosno CSV (lon,lat), Marki CSV (row-wrapped quoting, lat/lon swapped), Przemyśl (`;` CSV/GeoJSON/JSON/GML), Legionowo CSV with TERYT address columns, Warszawa (link to city catalogue).
- **Decision:** One new Django app `apps.aed`; standard schema defined once in `schema.py` (Polish ASCII snake_case, TERYT-style address, WGS84) and all artefacts generated from it; harvest → per-source parse/mapping → normalize → merge (distance + similarity, dane.gov.pl over OSM) with provenance; dane.gov.pl-compatible JSON:API under `/api/1.4/...` + exports under `/api/exports/`; fork config tracked in `fork-config/` with an nginx `aed.mcod.local` https proxy to our backend and reset host ports; publishing via Django-shell script; CSV is the primary previewed resource in the fork; Next.js map with Leaflet + clustering and OSM tiles; committed raw snapshot as offline demo fallback.
- **Affected Docs & Tasks:** `docs/03-architecture.md`, `docs/05-plan.md`, `docs/01-brief.md`, T01–T09.

### `DEC-005` — dane.gov.pl Fork Also on Hetzner (ubuntu-4gb-hel1-2)
- **Date:** 2026-11-21 18:18
- **Status:** Accepted (supersedes the "fork local only" part of `DEC-002`) — superseded by DEC-014 (T10 cancelled, demo on the local fork)
- **Context / New Info:** User wants the fork reachable on the Hetzner server `ubuntu-4gb-hel1-2` (4 GB RAM) too. Constraints: only ports 3000–3100 are open; `deploy.yml` does `rsync --delete` into `/home/github/apps/<repo>/`, so untracked files there are wiped; `dane-gov-pl/` is git-ignored (222 MB); fork stack (ES 1 GB heap, RabbitMQ, Redis, Postgres, 3 Python 3.8 app containers, Angular) plus our stack is very tight in 4 GB.
- **Decision:** Fork stays a separate app with exactly one public port (fork nginx on `3080`, our app keeps `3000`), living outside the CI-synced dir (`/home/github/apps/danegov-fork/`), deployed manually from `fork-config/` (rsync code + config; images built locally and transferred with `docker save | ssh docker load` to avoid a 30+ min build on the server). Hostnames via wildcard DNS (`mcod.<ip>.sslip.io`, `api.…`, `admin.…`, `aed.…`) so judges need no `/etc/hosts`. Server check (2026-11-21 18:36): 15 GB RAM, 8 vCPU, 4 GB swap, `vm.max_map_count` OK, ufw inactive, access via `ssh hack` (root), GitHub self-hosted runner on the same host → no rescale; ES keeps default 1 GB heap. Server is shared: 3000 = `django-nextjs-template`, 3001 = `HN26-PCI`, so our app moves to `FRONTEND_PORT=3002` (server `.env`) and the fork uses `3080`. Local fork (T05/T06) first; server deploy is new task T10 in M3; fallback = local fork + screenshots.
- **Affected Docs & Tasks:** `docs/01-brief.md`, `docs/03-architecture.md`, `docs/05-plan.md`, T05, new T10.

### `DEC-006` — T05 Go: Local dane.gov.pl Fork Runs
- **Date:** 2026-11-21 19:12
- **Status:** Accepted
- **Context / New Info:** Fork booted in ~75 min wall-clock (app image build 23.5 min). Verified: 11 containers up (compose project `danegov-fork`, network 172.28.18.0/24), `https://api.mcod.local/1.4/datasets` count=1, portal 200, admin login OK, `aed.mcod.local` proxy reaches our backend from `mcod-celery`. Deviations from plan: Angular runs as container `mcod-frontend` on the fork network (not on host); `mcod-cms` also runs (Angular calls `/cms`); `local.py` drops ES `"timeout": 1` (rejected by ES 6.8); base images pulled via `mirror.gcr.io` (Docker Hub 429).
- **Decision:** GO — keep the real fork as the portal demo; the Next.js dataset-page fallback is not needed. Continue with T06 after T04.
- **Affected Docs & Tasks:** `docs/03-architecture.md` (fork services), T05, T06, T10.

### `DEC-007` — Schema v1.0.0 Extended for London-Schema Compatibility
- **Date:** 2026-11-21 19:31
- **Status:** Accepted
- **Context / New Info:** User provided an AED JSON Schema based on the London dataset ("The Circuit", mentioned by a mentor) and asked whether `aed-pl` covers it. User wants to keep the Polish public-sector style (Polish ASCII snake_case names, flat table).
- **Decision:** Added optional fields `numer_seryjny`, `data_instalacji`, `data_ostatniego_uzycia`, `data_waznosci_elektrod_pediatrycznych` and recommended `data_nastepnego_przegladu`; added `status` values `do_weryfikacji`, `skradziony`, `wycofany` (42 fields, 8 required). Not adopted: `what3words` (user decision), `accessCode` (security — open data; publish only `zabezpieczenie = szafka_na_kod`), `contactPerson` / `inspectorName` (personal data, RODO), nested `consumables[]` / `maintenanceLogs[]` (flattened to dates for tabular dane.gov.pl previews); serial number/manufacturer/model stay optional (no current dane.gov.pl source publishes them).
- **Affected Docs & Tasks:** `backend/apps/aed/schema.py`, `docs/schema-aed.md`, `docs/deliverables/*`, T01.

### `DEC-008` — T07 UI Design: `/api/aed/` Map Contract, Client-Side Filtering, Shared Primitives
- **Date:** 2026-11-21 19:38
- **Status:** Accepted (UI parts refined by DEC-010; API contract unchanged)
- **Context / New Info:** T07 per-task UI design needs exact properties for the map popup/list and landing counters; T04 only said "lightweight GeoJSON". Users are the public in an emergency (mobile, fast) and judges.
- **Decision:** `/api/aed/` returns a FeatureCollection with `meta {count, generated_at, license}` and properties `id_aed, nazwa, adres (display string), miejscowosc, opis_lokalizacji, w_budynku, pietro, dostep, godziny_dostepnosci, zabezpieczenie, status, dysponent, telefon_kontaktowy, data_aktualizacji, zrodla[{nazwa, typ, url}]` (schema names/codes, empty = `null`). The UI loads the full set once and searches/filters (24/7, public) and sorts by distance (browser geolocation, optional) client-side; `q`/`bbox` stay for API users. Django `GZipMiddleware` enabled. `/api/sources/` exposes `aed_count`, `updated_at`, `sources[].{id,title,kind,url,record_count}`. New shared UI primitives: `EmergencyBanner` (112), `Badge`, warning colour tokens; AppShell rebranded to "Misja AED" with nav and full-bleed `/mapa`. Optional server env `DANEGOV_FORK_URL` for the landing link to the fork. Navigation = external OSM directions / `geo:` link only (no in-app routing).
- **Affected Docs & Tasks:** `docs/03-architecture.md`, `docs/02-ui-system.md`, `docs/tasks/T07-aed-map-nextjs.md`, T03 (`/api/sources/` fields), T04 (`/api/aed/` properties + gzip).

### `DEC-009` — Warsaw AED Data via Token-Protected City API (`WARSAW_API_TOKEN`)
- **Date:** 2026-11-21 20:11
- **Status:** Accepted
- **Context / New Info:** User wants Warsaw AED data from dane.gov.pl. dane.gov.pl dataset 39512 only links to `dane.um.warszawa.pl/pl/catalogue/7bc32ffc-…` (HTML). The catalogue metadata API (`/api/datasets/{uuid}`) points to call examples: `POST https://dane.um.warszawa.pl/api/action/get_scb_lokalizacja_defibrylatorow` with header `Authorization: <token>` (free token from `dane.um.warszawa.pl/key-api`); without it HTTP 403. Data (Stołeczne Centrum Bezpieczeństwa, CC BY, daily) has rich fields: access description, 24/7 availability, public access, manufacturer, location description, address.
- **Decision:** Harvester recognises Warsaw catalogue links, resolves the API action from the published call examples (fallback: known AED action) and POSTs with `WARSAW_API_TOKEN`. New env var mirrored in `.env.example`, `compose.yaml`, `compose.prod.yaml`, `settings.py` (secret: only in `.env`, never committed, never stored in DB). Without/with a rejected token the resource gets new status `requires_api_key` with an explanatory message (also a finding for the pitch: the dataset is listed on dane.gov.pl but not machine-readable without registration). Fetched Warsaw data is saved in the offline snapshot (CC BY).
- **Affected Docs & Tasks:** `backend/apps/aed/harvest.py`, `models.py` (+ migration 0002), `.env.example`, `compose*.yaml`, `docs/03-architecture.md`, T02, T03 (Warsaw parser).

### `DEC-010` — T07 Design v2: Very Simple UI, Location Fixed to BCTW Bydgoszcz
- **Date:** 2026-11-21 20:41
- **Status:** Accepted (refines DEC-008 UI parts; `/api/aed/` contract unchanged)
- **Context / New Info:** User asked to hardcode the current location to Bydgoszcz exhibition centre and to make the UI very simple and highly visible.
- **Decision:** Single page `/` "Najbliższy AED": big 112 banner, "Jesteś tutaj: Bydgoskie Centrum Targowo-Wystawiennicze, Bydgoszcz (lokalizacja demonstracyjna)" at 53.170719, 18.047651 (OSM Nominatim), one big card for the nearest AED (distance, walking time "w linii prostej", ≤ 3 badges, "PROWADŹ DO AED" OSM walking route), rows #2–#5, map with numbered pins 1–5 + clustered rest, "Skąd są te dane?" section (counts, sources, schema/exports/API/fork links). Removed: search, filters, browser geolocation (also avoids the https requirement on the plain-http Hetzner deploy), map/list toggle. `/mapa` redirects to `/`. Optional `?lat=&lon=&miejsce=` override. Answers to v1 open questions: load all AEDs once (yes), fork link via `DANEGOV_FORK_URL` (yes), drop health card (yes), single "Prowadź" link (no `geo:`).
- **Affected Docs & Tasks:** `docs/tasks/T07-aed-map-nextjs.md`, `docs/03-architecture.md` (frontend routes), `docs/02-ui-system.md`.

### `DEC-011` — T03: Schema-Keyed JSON Records, Merge Rules, Coordinate Quality Checks
- **Date:** 2026-11-21 21:21
- **Status:** Accepted
- **Context / New Info:** Implementing T03 on real data (19,084 records). Plain transitive clustering chained distinct devices (two Warsaw AEDs in one building merged through an OSM point between them); Marki publishes one record with Krosno's coordinates (250 km away) and repeats coordinates for different schools; loading records with `select_related` pulled the 7 MB OSM payload per row (container OOM-killed).
- **Decision:** `SourceRecord.data` / `AED.data` are `JSONField`s keyed by standard schema field names (+ `lat`/`lon` columns), so the schema stays the single source of truth (instead of one DB column per field). Merge = greedy agglomeration by distance (≤ 25 m, or ≤ 75 m with name/address similarity ≥ 0.6) where a cluster never contains two records from the same resource; field precedence dane.gov.pl > OSM, first non-empty wins; `id_aed` = `PL-AED-` + hash of the top record key. Municipal sources get coordinate checks: point > 30 km from the source's median → `valid=False` + flag `wspolrzedne_daleko_od_pozostalych`; repeated coordinates → `wspolrzedne_powtorzone`; swapped lat/lon fixed + flagged. Coverage counts `nieznany` as empty. Raw payloads always deferred in record queries.
- **Affected Docs & Tasks:** `docs/03-architecture.md`, T03, T04 (exports read `AED.data`).

### `DEC-012` — T04: dane.gov.pl 1.4 Envelope Parity, Resource Layout, ODbL Licence
- **Date:** 2026-11-21 21:53
- **Status:** Accepted — superseded in part by DEC-014 (our `/api/1.4` replaced by the fork's native API + `/1.4/aed/*`)
- **Context / New Info:** Real responses of `api.dane.gov.pl/1.4` (dataset 40593, resource 2625221 + `/data`) recorded as test fixtures. The merged database contains OpenStreetMap data (ODbL 1.0, share-alike).
- **Decision:** `/api/1.4/datasets[/{id}[/resources]]`, `/api/1.4/resources/{id}[/data[/{row_uuid}]]` reproduce the portal envelope 1:1 at key level (`jsonapi`, `links`, `data{id,type,attributes,relationships,links}`, `meta{server_time,path,language,relative_uri,params,count}`; rows `colN={repr,val}` + `headers_map`/`data_schema`; `id,slug` path form accepted) — enforced by a test comparing keys with the fixtures. One dataset (id `1`, "Defibrylatory AED – zbiór ogólnopolski") with resources 1 CSV, 2 XLSX, 3 GeoJSON, 4 JSON (all tabular via `/data`) and 5 schema xlsx. Exports `/api/exports/aed.{csv,json,geojson,xlsx}` (standard column order, metadata block, cached per data version). **Licence of the merged dataset: ODbL 1.0** (because of OSM content; municipal CC0/CC BY data is compatible) — stated in exports and the portal metadata. `/api/aed/` per DEC-008 (~1.4 MB gzipped for the whole country); `GZipMiddleware` enabled.
- **Affected Docs & Tasks:** `docs/03-architecture.md`, T04, T06 (fork dataset licence/links), T07.

### `DEC-013` — T06: Publish via File Uploads, JSON as API Resource, Licence Fields, Angular `--prebundle=false`
- **Date:** 2026-11-21 22:31
- **Status:** Accepted
- **Context / New Info:** Implementing T06 against the running fork. (1) Upstream `Resource.is_linked` is true for any link outside the fork's own API, and linked resources never get `visualization_types` → no *Tabela*/*Mapa* tabs. (2) The fork guesses CSV column types from the first rows (`boolean`/`integer`) and then rejects empty cells. (3) libmagic reports our 22 MB JSON export as `text/plain`, so the fork tries every rdflib parser on it (minutes of Celery CPU, blocking the 2 workers); our exports send `Content-Disposition: attachment`, which forces type `file`. (4) The fork's licence model only knows CC licences (`license_chosen`). (5) In `ng serve`, Vite prebundling breaks `LeafletService`'s `require('leaflet')` → empty map tab. (6) Our XLSX export has typed cells and a trailing all-empty column → goodtables `missing-value`.
- **Decision:** `fork-config/publish_aed.py` downloads CSV, XLSX, GeoJSON and the schema XLSX from our app and uploads them as resource main files (`ResourceFile`, the pattern of upstream `dga_utils.py`); re-runs re-upload only when the sha256 changes (XLSX: ignoring `docProps/core.xml`). Phase 2 sets every CSV column to `string` except `szerokosc_geograficzna`/`dlugosc_geograficzna` (`number`) and map columns `label=nazwa`, `b`, `l`, then re-indexes synchronously and refreshes the ES documents. The JSON resource is an API-type link (`forced_api_type`) to our `/api/1.4/resources/1/data` (application/json, no attachment); the full JSON export is linked in its description. Licence: fork fields stay CC-based (`license_condition_source` → shown as CC BY 4.0) and the ODbL 1.0 requirement (DEC-012) is stated in `license_condition_db_or_copyrighted` and the dataset description. `mcod-frontend` runs `ng serve ... --prebundle=false` (config-only change in `fork-config/compose.override.yml`). XLSX keeps no table preview (CSV is the previewed resource).
- **Affected Docs & Tasks:** `fork-config/publish_aed.py`, `fork-config/publish.sh`, `fork-config/compose.override.yml`, `fork-config/README.md`, `docs/03-architecture.md`, T06, T10 (same script with `AED_BASE_URL`).

### `DEC-014` — Pivot: AED Aggregation + Validation API Built Inside the dane.gov.pl Fork (`mcod.aed`)
- **Date:** 2026-11-22 00:07
- **Status:** Accepted
- **Context / New Info:** User (2026-11-22 ~00:00): the functionality must live **inside the dane.gov.pl portal**, not in a separate backend. The portal already holds many separate AED datasets; it needs one common structure in which they are aggregated and available inside the portal, plus an API to validate imported data against that structure. Answers: sources = datasets uploaded into the portal **and** connected APIs (link/API resources); build only in dane.gov.pl, "without my backend" — keep the data structure (standard schema), the source datasets converted into it, and a simple frontend that shows the data coming from dane.gov.pl; validation = portal API endpoint; keep the map (T07), cancel T08/T10. Time left at decision: ~9 h to code freeze (09:00).
- **Decision:**
  - New Django app **`mcod.aed`** inside the fork backend (Python 3.8 / Django 2.2 / Falcon 4), source tracked in our repo at `fork-config/mcod_aed/` and installed into `dane-gov-pl/backend_latest/mcod/aed/` by `fork-config/setup.sh` (enabled via `local.py` `INSTALLED_APPS`, routes registered in `mcod/routes.py` by a small idempotent patch). Schema, parsers, column mapping, normalisation and merge logic are **ported** from `backend/apps/aed` (py3.8-compatible).
  - **Sources inside the portal:** published datasets tagged `AED`/`defibrylatory` (except the common one). File resources are parsed from their uploaded files; link/API resources ("connected APIs") are fetched live through connectors (generic CSV/JSON/GeoJSON URL, OpenAEDMap/OSM GeoJSON, Warsaw city API with `WARSAW_API_TOKEN` in the fork's env). The real AED datasets from api.dane.gov.pl are mirrored into the fork (their institutions, datasets, files; Warsaw + OSM as API resources) by a management command.
  - **Aggregation** (`manage.py aed_aggregate`, Celery task, admin trigger): every source resource -> records in the standard structure (`AedSourceRecord`, with coverage + quality flags), each source dataset gets a converted resource "… – wersja zgodna ze wzorcem AED (CSV)", and all records are merged/deduplicated into `AedDevice` and published natively as the common dataset **"Defibrylatory AED – zbiór ogólnopolski"** (organization Misja AED) with CSV (table + map preview), XLSX, GeoJSON and the schema XLSX as fork-generated files (T06's external-link workaround becomes unnecessary).
  - **Portal API** (Falcon, dane.gov.pl 1.4 JSON:API envelope): `GET /1.4/aed/schema`, `POST /1.4/aed/validate` (multipart file or `{"url"}` or `resource_id`; returns per-row/per-field errors, warnings, coverage), `GET /1.4/aed/sources` (coverage report), `GET /1.4/aed/devices` (GeoJSON for the map).
  - **Our `backend/` is retired from the demo** (kept in the repo, not extended; removing it from compose/CI is decided in T09 so the live deploy does not break). The Next.js map (T07) switches its data source to the fork API (`/1.4/aed/devices`, `/1.4/aed/sources`).
  - **Cancelled:** T08 (/schemat page — the schema is served by the portal) and T10 (fork on Hetzner). Demo runs on the local fork.
- **Affected Docs & Tasks:** `AGENTS.md`, `docs/01-brief.md`, `docs/03-architecture.md`, `docs/05-plan.md`; new T11–T15; T08, T10 `CANCELLED`; T09 updated; T06 (superseded by native publishing in T13, stays VERIFIED); DEC-004, DEC-005, DEC-012 partially superseded.

### `DEC-015` — Data Standard Field on Datasets + Automatic Validation That Blocks Publishing
- **Date:** 2026-11-22 00:39
- **Status:** Accepted (refines DEC-014)
- **Context / New Info:** User: every dataset that is part of a bigger dataset should carry a field naming its category (e.g. "AED data"); that category has a structured JSON definition and data is validated against it automatically on upload and during aggregation. Answers: invalid data **blocks publishing**; the field is a **dedicated, typed field** (not `customfields`).
- **Decision:**
  - **`DataStandard`** model in `mcod.aed` (generic, AED is the first): `code` (`aed-pl`), `name` ("Dane AED – wzorcowy zakres danych"), `version`, `json_schema` (generated from `FieldSpec`), `target_dataset` (common dataset FK), `max_invalid_ratio` (default 0.2), `is_active`. Seeded by migration/command.
  - **"Standard danych" on datasets:** link model `DatasetStandard` (OneToOne `Dataset` → `DataStandard`, no change to the upstream `dataset` table); dropdown in the dataset admin form and attribute `data_standard {code, name, version}` in `/1.4/datasets[/{id}]` (small idempotent patches to the fork's dataset admin form + API serializer, installed by `setup.sh`).
  - **Automatic validation:** `ResourceStandardValidation` (OneToOne `Resource`: `status` valid/warnings/invalid/error, `blocking` bool, `rows_total`, `rows_invalid`, `errors` JSON (first 500), `coverage` JSON, `validated_at`, `standard_version`). Exposed at `GET /1.4/resources/{id}/standard-validation` and in admin (resource page panel + list column).
  - **Blocking rule:** blocking = unreadable file, required columns missing/unmappable, or `rows_invalid / rows_total > max_invalid_ratio`. (a) Admin upload: the resource form validates the uploaded file synchronously and rejects the save with the error list. (b) Other paths (link/API resources, link revalidation, imports): after the fork's file/data Celery tasks finish, validation runs; blocking → resource set to `draft` (hidden from portal/search) + report stored; non-blocking → published, invalid rows excluded from aggregation and listed in the report.
  - **Aggregation** selects sources by `DatasetStandard = aed-pl` (not tags) and uses only non-blocked resources.
  - Time: +~1 h; the per-source converted "wersja zgodna ze wzorcem" CSV moves to the top of the cut list.
- **Affected Docs & Tasks:** `docs/03-architecture.md`, T11 (models + field + API attribute), T12 (imported datasets marked `aed-pl`), T13 (select by standard), T14 (validator reused + on-upload hook + blocking), `docs/05-plan.md`.

### `DEC-016` — Strict Blocking Kept; Corrected Copy Published Next to a Blocked Real Source
- **Date:** 2026-11-22 01:58
- **Status:** Accepted (refines DEC-015)
- **Context / New Info:** T12 import: Legionowo's real file uses the standard's column names but writes `cecha_ulicy` as "ulica"/"aleja" and a 6-digit TERC in all 24 rows, so automatic validation blocks it (draft). User: show both the correct and the incorrect version with the validator, and upload a corrected version of the file.
- **Decision:** The blocking rule stays strict (any row error counts towards `max_invalid_ratio`). The importer keeps the original resource (blocked → draft, report in admin/API) and publishes a corrected copy next to it in the same dataset ("… – wersja poprawiona (zgodna ze standardem AED)", `fixtures/corrected/`, only the reported values fixed: "ul."/"al.", TERC 1408011). Re-imports never re-publish a blocked resource unless its file changed (then the portal re-validates).
- **Affected Docs & Tasks:** T12, T13 (aggregates the corrected copy, skips the blocked original), `fork-config/mcod_aed/importer.py`, `publishing.py`.

### `DEC-017` — Retired `backend/` Stays in Compose/CI as the Hetzner Fallback Data Source; Demo Datasets Stay Drafts
- **Date:** 2026-11-22 02:36
- **Status:** Accepted (completes DEC-014 for T09)
- **Context / New Info:** After the pivot the demo runs entirely on the local fork (`mcod.aed`) and the map reads the portal API (T15). The Hetzner deploy (push to `main`) has no fork (T10 cancelled); removing `backend` from `compose.prod.yaml` would leave the live map without data.
- **Decision:** Keep `backend` (+ `db`) in `compose.yaml` / `compose.prod.yaml` / CI unchanged and frozen (not extended): on Hetzner `DANEGOV_API_URL` is empty, so the map keeps using the old backend `/api/aed/` (same DEC-008 contract). Locally the demo needs only the fork + `frontend` (`docker compose up -d --no-deps frontend`). Datasets with invented demo data (e.g. "Bydgoszcz (demo)") stay `draft` so they are never aggregated into the national dataset or shown on the map. Admin sidebar gets a "Standardy danych" section (django-suit `MENU` entry in `fork-config/local.py`). One-command demo preparation: `fork-config/aed-demo.sh [--offline]`.
- **Affected Docs & Tasks:** T09, `docs/demo-script.md`, `fork-config/aed-demo.sh`, `fork-config/local.py`, `fork-config/README.md`.

### `DEC-018` — T10 Revived: dane.gov.pl Fork with `mcod.aed` on Hetzner for the Judges
- **Date:** 2026-11-22 02:48
- **Status:** Accepted (reverses the T10 cancellation of DEC-014; supersedes the Hetzner part of DEC-017)
- **Context / New Info:** User: the judges have to see the app. The in-portal module exists only on the local fork; Hetzner runs only the Next.js map with old-backend data. Server check: 15 GB RAM (13 GB free), 8 vCPU, 21 GB disk free, swap 4 GB, `vm.max_map_count` 262144, port 3080 free, IP 2.29.205.102. ~6 h to code freeze.
- **Decision:** Deploy the fork + `mcod.aed` to `ssh hack` in `/home/github/apps/danegov-fork/` (outside the CI-synced dir), only nginx published on **3080**, hostnames `mcod./api./admin./cms.2.29.205.102.sslip.io` (no hosts edits for judges). Reuse the proven local stack (same compose files + `fork-config/compose.override.yml`) plus a Hetzner override for hostnames/ports/certificate; images built locally and shipped (`docker save | ssh hack docker load`); data created on the server by `init_mcod_db` + `fork-config/aed-demo.sh`. Timebox 3 h; fallback = local demo + screenshots. Our app's CI deploy and `compose.prod.yaml` stay untouched. As built: port 443 + Let's Encrypt (user choice); the Hetzner map's `DANEGOV_API_URL` (server `.env`) points at the server fork, so the DEC-017 old-backend fallback is no longer used on Hetzner; Warsaw city API is unreachable from the server → labelled offline copy from 2026-11-21.
- **Affected Docs & Tasks:** T10 (`TODO` again, rescoped), `docs/05-plan.md`, `fork-config/hetzner/*`, `fork-config/README.md`.

### `DEC-019` — Universal Data Standards: Data-Defined Standards + Second Standard "Żłobki i kluby dziecięce"
- **Date:** 2026-11-22 03:49
- **Status:** Accepted (refines DEC-015: standards are no longer code-only; AED path unchanged)
- **Context / New Info:** User wants to show that the schema-based aggregation is universal, not built only for AED. Research on dane.gov.pl: 36 nursery datasets ("Rejestr żłobków i klubów dziecięcych" per municipality — Zabrze, Tychy, Sosnowiec, Tarnowskie Góry…, city lists e.g. Inowrocław), CSV + XLSX, different columns (`nazwa_zlobka`/`address`/`regon`/`liczba_miejsc`/`lat`,`lon` vs `nazwa`/`adres_ulica`/`adres_nr` vs `Nazwa podmiotu`/`ulica`/`nr telefonu`), only some with coordinates. User choices: nurseries; standards defined as a JSON file + admin view (no full admin editor). ~5 h to code freeze.
- **Decision:** `DataStandard` gains a data definition: `fields` (name, label, type, obligation, allowed values, pattern, min/max, max length, description, **synonyms**), `merge` (strategy `key` with key fields / `geo` with distance / `none`), `discovery` (dane.gov.pl search terms + title pattern) and `publish` (common dataset title/description, optional map columns). New standards are loaded from JSON files (`fork-config/mcod_aed/standards/*.json`, command `aed_load_standard`) and shown/edited as JSON in the admin. A generic engine (spec → validate / convert / merge / publish) serves every standard except `aed-pl`, whose verified code path (schema.py, OSM/Warsaw handling, geo merge, `/1.4/aed/*`) stays unchanged; AED's fields are mirrored into the same JSON format for display. Generic API `/1.4/standards`, `/1.4/standards/{code}/schema|validate|sources`. Second standard `zlobki-pl` (~15 fields; merge by REGON, else name + address); 6–8 municipal nursery datasets imported from dane.gov.pl; common dataset "Żłobki i kluby dziecięce – zbiór zbiorczy" published by the portal (CSV with table preview, XLSX, schema XLSX). Cut order: nursery map → admin JSON editing (command only) → generic `/1.4/standards/*` API.
- **Affected Docs & Tasks:** new T16–T19, `docs/03-architecture.md`, `docs/05-plan.md`, `docs/demo-script.md`, `fork-config/mcod_aed/*`.

### `DEC-020` — Demo Flow "Reject → Fix → Accept → Auto-Refresh" + Automatic Aggregation
- **Date:** 2026-11-22 06:08
- **Status:** Accepted (extends DEC-015/DEC-019; aggregation button/command unchanged)
- **Context / New Info:** User's demo workflow: show the new universal functionality — two standards; put a file into a dataset of either standard; the system validates it and rejects it; then the corrected version is accepted and the common dataset is updated with data from many sources automatically. Until now aggregation ran only from the admin button / command.
- **Decision:** When a source resource passes its standard and is published (Celery `validate_resource_standard_task`), the plugin queues the aggregation of that standard automatically (15 s delay, one queued run per standard per 45 s via the Redis cache; never from the common dataset's own files; switch `AED_AUTO_AGGREGATION`, default on). Runs show `triggered_by = "auto: zasób N zgodny ze standardem"`; the resource admin page shows "Zbiór zbiorczy … odświeżony automatycznie … (agregacja #N)". Demo files: before/after pairs for Krosno (`docs/demo/samples/{aed,zlobki}-krosno-nowe-{bledny,poprawiony}.csv`). The demo video (T19) follows this flow.
- **Affected Docs & Tasks:** T19, `docs/demo-script.md`, `fork-config/mcod_aed/{resource_validation,tasks,integration}.py`, `fork-config/local.py`.

### `DEC-021` — UI Polish: AEDane Banner on the Portal Home Page + Map-First Public Page
- **Date:** 2026-11-22 06:40
- **Status:** Accepted
- **Context / New Info:** User: add `docs/inputs/ui/baner.png` (AEDane – "Pomoc zaczyna się od informacji. Udostępnij zbiór danych na dane.gov.pl", 1860×240) to the main page of the dane.gov.pl fork; simplify the public Next.js page — remove most elements, keep a big map with the nearest AED and all other AEDs clickable. ~2 h 20 min to code freeze.
- **Decision:** (1) Portal: the banner is served by the plugin (`GET /1.4/aed/banner.png`, reached by the portal through its own `/api` proxy) and shown under the search box of the home page via a patched copy of `home.component.html` kept in `fork-config/frontend/` and bind-mounted over the upstream file (no edit in `dane-gov-pl/`); it links to the AED common dataset (`GET /1.4/standards/aed-pl/dataset` → 302 to the portal dataset page). (2) Next.js: "/" becomes map-first — full-height map, one floating "Najbliższy AED" card (distance, name, access, Prowadź, 112), every AED pin clickable with its details popup; removed: emergency banner block, location box, list of AEDs 2–5, data/API section and footer links (attribution stays on the map). No backend/API change.
- **Affected Docs & Tasks:** new T20 (portal banner), new T21 (map-first page, UI design gate), `docs/05-plan.md`, `fork-config/compose.override.yml`.

<!-- Template for new entries:
### `DEC-XXX` — `<Short Title>`
- **Date:** `<YYYY-MM-DD HH:MM from date '+%Y-%m-%d %H:%M'>`
- **Status:** Accepted | Superseded by DEC-YYY
- **Context / New Info:** `<What changed or what was decided>`
- **Decision:** `<Exact choice made>`
- **Affected Docs & Tasks:** `<e.g., docs/01-brief.md, docs/03-architecture.md, T03, T04>`
-->
