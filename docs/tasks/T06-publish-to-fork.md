# `T06` — Publish the national AED dataset in the dane.gov.pl fork

- **Status:** `VERIFIED`
- **Layer:** `Infra`
- **UI Design Required:** `No`
- **Depends On:** `T04`, `T05`
- **Traces To:** `REQ-09`, `REQ-07`, `DEC-004`

## Goal & User Outcome

In the running fork, the organization *Misja AED* publishes dataset *Defibrylatory AED – zbiór ogólnopolski* with resources linking to our exports; the portal downloads and indexes them and shows the table preview, map preview and `/1.4` API for it.

## Scope & Non-Goals

- **In Scope:**
  - `fork-config/publish_aed.py` (run via `manage.py shell`, wrapper `fork-config/publish.sh`): idempotently create organization, dataset (category Zdrowie/HEAL, licence conditions with the ODbL 1.0 note — DEC-012/DEC-013, tags `AED`, `defibrylatory`, `zdrowie`, `ratownictwo`, update frequency `daily`), resources: CSV (primary, preview + map), XLSX, GeoJSON, Schemat (xlsx) uploaded as files downloaded from `https://aed.mcod.local/api/...`, and JSON as an API link to `/api/1.4/resources/1/data` (DEC-013)
  - Trigger resource validation (Celery), type the CSV columns and set map columns (`label`=`nazwa`, `b`=`szerokosc_geograficzna`, `l`=`dlugosc_geograficzna`) in `tabular_data_schema`
  - Fallback documented: same steps by hand in admin
  - Screenshots for the presentation
- **Out of Scope:**
  - Writing to production dane.gov.pl

## UI Design (Per-Task)

N/A — backend/infra only.

## Technical Implementation Plan

- `fork-config/publish_aed.py` + `fork-config/publish.sh`, README section *Publish the national AED dataset (T06)* (incl. manual admin fallback).
- Check: `/1.4/resources/{id}/data` and `/1.4/resources/{id}/geo` on `api.mcod.local` return our rows.
- Deviations found while implementing (DEC-013): link resources pointing outside the fork never get previews upstream (`Resource.is_linked`) → files are uploaded; CSV column types forced to `string` (coordinates `number`); JSON as API link (22 MB JSON file = minutes of rdflib parsing in Celery); `ng serve --prebundle=false` in `fork-config/compose.override.yml` (Leaflet `require` broke the map tab); XLSX has no table preview.

## Acceptance Criteria

- [x] Dataset visible on `https://mcod.local` search and dataset page with 5 resources
- [x] CSV resource has table preview and map preview with AED markers
- [x] `https://api.mcod.local/1.4/datasets?q=defibrylatory` returns the dataset
- [x] Re-running the script does not duplicate objects

## Verification Checklist

### Automated Checks
- [x] `make test` passes — 83 passed (no app code changed in T06; the fork script runs in the fork's Django and has no unit tests — verified end-to-end instead)
- [x] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [x] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [x] `make migrations-check` passes — no changes detected
- [~] `make build-prod` not run — no app code, Dockerfile or our Compose files changed (only `fork-config/`); `docker compose config --quiet`, prod config and `fork-compose.sh config --quiet` OK

### Observed Results (2026-11-21 22:31, local fork)
- `fork-config/publish.sh` → `DATASET 4211`, resources CSV 40212 (table+map), XLSX 40213, GeoJSON 40214, JSON API 40217, Schemat 40216 (table). First run ~35 s, re-run ~6 s (`file unchanged`, no duplicates), `AED_REVALIDATE=1` ~55 s.
- `api.mcod.local/1.4/datasets?q=defibrylatory` → count 1 (id 4211); `/1.4/resources/40212/data` → 18,769 rows (= our `aed_count`); `/1.4/resources/40212/geo` → 18,769 points; dataset: category HEAL, tags, frequency daily.
- Screenshots (headless Chrome): `docs/demo/screenshots/T06-fork-{search,dataset,table,map}.png`.

### Manual Verification
1. `fork-config/publish.sh` → prints `DATASET <id>` and 5 `RESOURCE` lines (CSV `table=True map=True`); run it again → `exists` / `file unchanged`, nothing new created
2. Open `https://mcod.local/pl/dataset?q=defibrylatory` → dataset *Defibrylatory AED – zbiór ogólnopolski* (Dostawca: Misja AED, Kategoria: Zdrowie) with 5 resources
3. Open the CSV resource → *Tabela* shows rows (18,769), *Mapa* shows clustered AED markers over Poland (hard-reload once if the tab was open before the `mcod-frontend` restart)
4. `https://api.mcod.local/1.4/datasets?q=defibrylatory` returns the dataset; `https://api.mcod.local/1.4/resources/<csv id>/geo?per_page=1` returns points
5. Re-harvest in our app (or just `AED_REVALIDATE=1 fork-config/publish.sh`) → script re-uploads changed files, counts follow our `/api/sources/` `aed_count`

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-21 23:05
- **Notes / Follow-Ups:** Data-quality findings visible on the fork map (source data, not T06 bugs): a few points just east of the PL border (Grodno/Lutsk area) pass the PL bbox check; OSM node "AED – Blok mieszkalny JANÓW … Konin 52.33, 18.24" is placed at 51.20, 20.42 — candidates for an extra coordinate/name check in T03 normalize. XLSX table preview would need the export to write empty strings and untyped cells.
