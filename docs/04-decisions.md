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
- **Status:** Accepted
- **Context / New Info:** Plan created. Fork investigation: resource links must be `https://` (fork `forms.py:683`, `link_validation.py:92`, cert not verified); JSON links are classified as "api" (no preview); map preview needs a tabular resource with numeric lat/lon + label columns; fork publishes host ports 5432/6379/9200/80/443 etc.; app image is Python 3.8 (20–40 min build). Real sources inspected: Krosno CSV (lon,lat), Marki CSV (row-wrapped quoting, lat/lon swapped), Przemyśl (`;` CSV/GeoJSON/JSON/GML), Legionowo CSV with TERYT address columns, Warszawa (link to city catalogue).
- **Decision:** One new Django app `apps.aed`; standard schema defined once in `schema.py` (Polish ASCII snake_case, TERYT-style address, WGS84) and all artefacts generated from it; harvest → per-source parse/mapping → normalize → merge (distance + similarity, dane.gov.pl over OSM) with provenance; dane.gov.pl-compatible JSON:API under `/api/1.4/...` + exports under `/api/exports/`; fork config tracked in `fork-config/` with an nginx `aed.mcod.local` https proxy to our backend and reset host ports; publishing via Django-shell script; CSV is the primary previewed resource in the fork; Next.js map with Leaflet + clustering and OSM tiles; committed raw snapshot as offline demo fallback.
- **Affected Docs & Tasks:** `docs/03-architecture.md`, `docs/05-plan.md`, `docs/01-brief.md`, T01–T09.

### `DEC-005` — dane.gov.pl Fork Also on Hetzner (ubuntu-4gb-hel1-2)
- **Date:** 2026-11-21 18:18
- **Status:** Accepted (supersedes the "fork local only" part of `DEC-002`)
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

<!-- Template for new entries:
### `DEC-XXX` — `<Short Title>`
- **Date:** `<YYYY-MM-DD HH:MM from date '+%Y-%m-%d %H:%M'>`
- **Status:** Accepted | Superseded by DEC-YYY
- **Context / New Info:** `<What changed or what was decided>`
- **Decision:** `<Exact choice made>`
- **Affected Docs & Tasks:** `<e.g., docs/01-brief.md, docs/03-architecture.md, T03, T04>`
-->
