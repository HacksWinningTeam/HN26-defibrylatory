# Misja AED — demo script (in-portal flow, DEC-014…017)

> Audience: hackathon judges. Length: ~6–7 min + Q&A. Everything runs **inside a local fork of dane.gov.pl**
> (module `mcod.aed`, code in `fork-config/mcod_aed/`). Screenshots: `docs/demo/screenshots/T09-*.png` (+ T07/T15 map).

## Before the demo (T-15 min)

1. Fork running: `fork-config/start.sh` (or check `fork-config/fork-compose.sh ps`); map: `docker compose up -d --no-deps frontend`.
2. Data fresh: `fork-config/aed-demo.sh` (~1 min; import → automatic validation → aggregation).
   No internet? `fork-config/aed-demo.sh --offline` (committed snapshot; Warsaw API then reported as unavailable, OSM uses the portal's cached copy).
3. Browser tabs (accept the self-signed certificate once per host):
   - A https://admin.mcod.local (`admin@mcod.local` / `testadmin123!`) → *Standardy danych*
   - B https://mcod.local/pl/dataset?q=defibrylator
   - C https://api.mcod.local/1.4/aed/schema
   - D http://localhost:3000/
4. File ready: `docs/demo/samples/aed-invalid-demo.csv` (uploaded to a **published** dataset with the AED standard, e.g. Krosno — it is refused, nothing changes).

## Script

Images are the real screens (headless Chrome, 2026-11-22) — use them as slides or as a fallback if something is down.

### 1. Many separate AED datasets (0:00) — *Fit 15%*
**Show:** tab B — portal search "defibrylator".
**Say:** AED data on dane.gov.pl is scattered: each city publishes its own file in its own columns and format (Krosno CSV, Przemyśl GeoJSON, Warszawa only via a city API, Legionowo hidden in a dataset called "Zdrowie").

![Portal search: separate AED datasets of different institutions](demo/screenshots/T09-s01-portal-search.png)

### 2. One standard structure (0:45) — *Schema 10%*
**Show:** tab C `https://api.mcod.local/1.4/aed/schema`, then download `/1.4/aed/schema.xlsx`.
**Say:** we designed one structure "Dane AED": 42 fields, 8 required, dictionaries, examples; JSON Schema, Table Schema and a CSV template — all served by the portal's own `/1.4` API.

![GET /1.4/aed/schema in the portal API](demo/screenshots/T09-s14-api-schema.png)

### 3. "Standard danych" field on a dataset (1:30) — *dane.gov.pl compliance 30%*
**Show:** tab A — sidebar *Dane → Datasets* → "Defibrylatory zlokalizowane w Mieście Krosno" → tab *General* → field **Standard danych = Dane AED** (note the new sidebar section *Standardy danych*).
**Say:** a dataset declares that it is part of a bigger dataset; the API shows it as `data_standard`. It is a plug-in Django app in the real dane.gov.pl — no upstream file edited.

![Dataset admin: Standard danych field and the Standardy danych sidebar section](demo/screenshots/T09-s08-admin-dataset-standard.png)

### 4. Validation blocks publishing (2:15) — *Innovation 15%*
**Show:** tab A — *Dane → Resources → Dodaj*: dataset "Defibrylatory zlokalizowane w Mieście Krosno", file `docs/demo/samples/aed-invalid-demo.csv`, status *Opublikowany* → *Zapisz*.
**Say:** the portal refuses to publish — errors per row and field, in Polish (missing coordinates, a point in Germany, a value outside the dictionary, a wrong date, an empty name). Nothing is saved, so the real dataset stays intact.

![Admin upload refused with validation errors at the file field](demo/screenshots/T09-s13-admin-upload-refused.png)

### 5. Real data: blocked original, corrected copy published (3:00) — *Compliance / Innovation*
**Show:** tab A — resource "Wykaz defibrylatorów AED … w Legionowie" (draft, red banner); tab B — public dataset "Zdrowie" (Legionowo) shows only the corrected copy.
**Say:** Legionowo's real file uses "ulica" instead of "ul." and a 6-digit TERC → automatically set to draft; the corrected copy passes. The same check is an API: `POST /1.4/aed/validate` (file, URL or resource id), and every result is stored at `/1.4/resources/{id}/standard-validation`.

![Blocked Legionowo resource with the validation report](demo/screenshots/T09-s09-admin-blocked-resource.png)

![Public Legionowo dataset: only the corrected file is visible](demo/screenshots/T09-s05-legionowo-public.png)

![Stored validation report of the blocked resource in the API](demo/screenshots/T09-s12-api-validation.png)

### 6. One-click aggregation (3:45) — *Fit / Innovation*
**Show:** tab A — sidebar *Standardy danych → Standardy danych (agregacja)* → **Uruchom agregację** → *Agregacje AED* (refresh after ~30 s).
**Say:** every dataset in the standard — uploaded files and connected APIs (Warsaw city API, OpenStreetMap) — is converted to the standard, validated and deduplicated: **6 sources → 18,776 AEDs, 315 confirmed by several sources**.

![Standardy danych list with the Uruchom agregację button](demo/screenshots/T09-s06-admin-standards.png)

![Agregacje AED: finished runs with counts and link to the common dataset](demo/screenshots/T09-s07-admin-runs.png)

![Merged AEDs confirmed by two sources](demo/screenshots/T09-s10-admin-devices.png)

### 7. The common dataset in the portal (4:30) — *Compliance 30%*
**Show:** tab B — "Defibrylatory AED – zbiór ogólnopolski" → CSV → **Tabela** (search "Krosno") and **Mapa**.
**Say:** the common dataset is published natively by the portal — its own table and map previews and `/1.4` API; every row points to its source (`zrodlo`).

![Common dataset page with its resources](demo/screenshots/T09-s02-national-dataset.png)

![Tabela preview of the common CSV](demo/screenshots/T09-s03-national-table.png)

![Mapa preview of the common CSV](demo/screenshots/T09-s04-national-map.png)

### 8. Coverage per source (5:15) — *Schema / Fit*
**Show:** `https://api.mcod.local/1.4/aed/sources`.
**Say:** a per-source report — how much of the standard each publisher fills, rows accepted and excluded: a to-do list for data owners.

![GET /1.4/aed/sources: per-source coverage report](demo/screenshots/T09-s11-api-sources.png)

### 9. Public map reading the portal (5:45) — *Fit / Presentation*
**Show:** tab D `http://localhost:3000/` (desktop, then phone width).
**Say:** a simple public front-end that reads only the portal API: nearest AED from the venue, 112 banner, walking route, WCAG 2.2 AA.

![Najbliższy AED page with data from the portal](demo/screenshots/T15-map-from-portal.png)

![Mobile view (375 px)](demo/screenshots/T07-mobile-375.png)

### 10. Limitations + next steps (6:30) — *Presentation 5%*
See "Limitations" below.

## Talking points per criterion

- **Compliance with dane.gov.pl (30%)**: runs on the real dane.gov.pl code (Django 2.2 / Falcon / Celery / Elasticsearch / Angular); plug-in app installed by config only; uses the portal's own models (datasets, resources, institutions), admin, resource pipeline, previews and `/1.4` JSON:API conventions; new endpoints follow the same envelope.
- **Schema (10%)**: one definition in code → XLSX, CSV template, JSON Schema, Table Schema, validator, admin field — cannot drift apart.
- **Innovation (15%)**: data standard as a first-class portal concept (any future "category with a structure" works the same), validation that blocks publishing, connected APIs aggregated live.
- **Fit (15%)**: real data from 5 institutions on dane.gov.pl + OSM; honest reports (blocked Legionowo file, excluded rows, missing towns in OSM).

## Fallbacks

| Problem | Fallback |
|---|---|
| No internet | `fork-config/aed-demo.sh --offline`; screenshots `docs/demo/screenshots/T09-*.png` |
| Celery stuck (aggregation "w toku") | `docker restart mcod-celery`; or run `docker exec mcod-admin python manage.py aed_aggregate` live in a terminal |
| Admin upload slow | show the API instead: `curl -sk -F file=@docs/demo/samples/aed-invalid-demo.csv https://api.mcod.local/1.4/aed/validate` |
| Portal frontend (Angular) not loading | `docker logs -f mcod-frontend` (compiles ~1 min after restart); show the API + admin |
| Map page empty | `curl -sI localhost:3000/portal-api/aed/devices` → must say `x-aed-data-source: dane.gov.pl fork`; restart `frontend` |

## Limitations (say them)

- Demo runs on a local fork; the live Hetzner app (push to `main`) shows the map from the earlier stand-alone backend (no fork there).
- One standard per dataset; new standards are defined in code (admin edits name/limit/target only).
- Blocking threshold 20 % invalid rows (configurable per standard); required fields the portal can fill from metadata (id, source, date, access) are warnings.
- The nearest AED to the venue in the merged data is 3 km away — real data gap, shown honestly ("Daleko – dzwoń 112").
- OSM points have no town for most records (`miejscowosc` warning); a few OSM points are misplaced (data quality issue reported, not fixed).

## Screenshot list for the slides (≥ 5)

All images above live in `docs/demo/screenshots/`. Suggested 7 slides: 1 (`T09-s01`), 3 (`T09-s08`), 4 (`T09-s13`), 5 (`T09-s09`), 6 (`T09-s07`), 7 (`T09-s04`), 9 (`T15-map-from-portal`).
