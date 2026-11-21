# 01 — Distilled Hackathon Brief

> Distilled from `docs/inputs/organizer-brief/brief.md` (transcription of `brief.pdf`, "Misja AED – Dane na ratunek") and user decisions in chat (2026-11-21) via `hackathon-kickoff`. Keep concise so agents can read the whole brief quickly without re-reading raw PDFs.

## Timeline

- **Submission Deadline:** `2026-11-22 11:00`
- **Demo Slot & Length:** `[OPEN]` not given in organizer brief; validation = "run the prototype and verify technical requirements & functionality" (brief §6)
- **Code Freeze:** `2026-11-22 09:00` — only fixes, screenshots, slides, and submission packaging after this

## Problem & Demo Goal

- **Problem Statement:** Poland has no complete map of AED defibrillators. AED data is scattered across several incomplete, unverified databases, published by different owners (*dysponenci*) in different formats. dane.gov.pl should host one national, open, up-to-date AED dataset (brief §1–2).
- **Demo Goal (DEC-014, 2026-11-22):** Inside the **dane.gov.pl portal itself** (local fork, new module `mcod.aed`): the portal holds many separate AED datasets from different institutions (uploaded files and connected APIs); one action aggregates them into **one common standard structure** — each source converted to the standard schema with a coverage report, all merged/deduplicated into the national dataset published natively in the portal (table + map preview, `/1.4` API) — and a **validation API** (`POST /1.4/aed/validate`) checks any imported data against the structure. A simple Next.js map shows the data coming from the portal.
- **Original Demo Goal (pre-pivot, kept for history):** Show that we (1) designed a **standard AED data schema** (*wzorcowy zakres danych*), (2) automatically **harvested every AED dataset from dane.gov.pl** (plus OpenStreetMap), showed which schema fields each source covers, and **merged them into one national dataset**, (3) expose it via an **API compatible with the dane.gov.pl API** and open machine-readable exports, and (4) show that dataset **published inside a running local fork of the dane.gov.pl portal** (its own dataset page, resource preview, and API).
- **Target Users:** Data owners publishing AED data (municipalities, institutions); dane.gov.pl operators; emergency services and app developers consuming the dataset; the general public (brief §2).

## Judging Criteria

| Criterion | Weight / Priority | How Our Demo Addresses It |
| --- | --- | --- |
| Compliance with how dane.gov.pl works | 30% | Dataset runs inside the real dane.gov.pl codebase (local fork); our API follows the dane.gov.pl API (`/1.4`, JSON:API style); open formats + portal metadata (licence, owner, update frequency) |
| Logo and slogan | 25% | Campaign name + slogan + logo + brand book (non-code deliverable, owner `[OPEN]`) |
| Creativity and innovation | 15% | Automatic harvesting + per-source coverage report against the standard schema; re-runnable refresh |
| Fit with the challenge | 15% | Real AED data from dane.gov.pl + OSM merged into one national set |
| Standard AED data schema | 10% | Schema defined once in code; `.xlsx` / CSV template / JSON Schema generated from it |
| Presentation | 5% | ≥5 slides with screenshots, user steps, limitations |

## Requirements

| ID | Requirement | Priority | Source (PDF / Notes) | Target Task(s) |
| --- | --- | --- | --- | --- |
| `REQ-01` | Design a standard AED schema (fields, types, required/optional, allowed values, examples) so that all data owners publish AED data the same way on dane.gov.pl | Must | Brief §2; user: "schema is very important" | T01, T08 |
| `REQ-02` | Deliver the standard schema as an `.xlsx` table | Must | Brief §4 | T01, T08 |
| `REQ-03` | Find and download all AED datasets/resources published on dane.gov.pl (via the public API `api.dane.gov.pl/1.4`), in whatever formats they use (CSV/XLSX/JSON/GeoJSON/XML) | Must | Brief §2 ("collect data from many scattered sources"); user | T02 |
| `REQ-04` | Also harvest OpenStreetMap AED data (`emergency=defibrillator`, Poland) as an extra source | Must | User | T02 |
| `REQ-05` | Map each source to the standard schema and show each source's reference scope (which standard fields it covers, how complete it is) | Must | Brief §2 ("ze wskazaniem ich referencyjnego zakresu") | T03, T08 |
| `REQ-06` | Merge all sources into one national dataset with deduplication, keeping the source of every record | Must | Brief §2–3 ("integrate information from all data owners in one dataset") | T03 |
| `REQ-07` | Expose the merged dataset via REST API endpoints compatible with the dane.gov.pl API (`/1.4` paths, JSON:API `data`/`attributes`/`links`/`meta` structure) | Must | User; brief §5 (compliance with dane.gov.pl) | T04, T06 → T11, T13, T14 (fork-native, DEC-014) |
| `REQ-08` | Shared data must be machine-readable (CSV/JSON/GeoJSON/XLSX), never PDF/DOC | Must | Brief §5 | T01, T04 |
| `REQ-09` | Configure and run a local fork of dane.gov.pl (`dane-gov-pl/`: mcod backend + Angular frontend) and publish the merged dataset in it so it is visible on the portal's dataset page | Must | User | T05, T06, T13 |
| `REQ-10` | Any UI we build: current WCAG, responsive (desktop + mobile), good UX | Must | Brief §5 | T07, T08 |
| `REQ-11` | Campaign name, slogan, logo (.jpg/.png/.pdf + open format such as SVG) and brand book PDF (colors, clear space, minimum size, forbidden uses, 3–5 sentence concept) | Must (deliverable) | Brief §2, §4, §8 (25%) | — (non-code, another team member) |
| `REQ-12` | Submission package: title + detailed description, presentation (≥5 slides with screenshots, user steps, limitations), prototype, source code | Must (deliverable) | Brief §4 | T09 (+ slides, non-code) |
| `REQ-13` | Interactive map of all merged AEDs in our Next.js app (markers with key schema fields + source), built last after the data pipeline and fork | Must | User (DEC-003); data from the portal API (DEC-014) | T07, T15 |
| `REQ-14` | dane.gov.pl fork with the published AED dataset reachable publicly on the Hetzner server (single port in 3000–3100) | Dropped (DEC-014) | User (DEC-005) | T10 (cancelled) |
| `REQ-15` | Aggregation **inside the dane.gov.pl portal**: AED datasets in the portal (uploaded files + connected API resources) are converted to the standard structure and merged into one common dataset available in the portal | Must | User pivot 2026-11-22 (DEC-014) | T11, T12, T13 |
| `REQ-16` | Portal API to validate imported AED data (file / URL / portal resource) against the standard structure, with per-row/per-field errors and coverage | Must | User pivot 2026-11-22 (DEC-014) | T14 |

## Core User Flows

0. **Primary flow after the pivot (DEC-014):** Portal operator imports/keeps AED datasets in dane.gov.pl (files + connected APIs, e.g. Warsaw city API, OSM) → admin runs "Agregacja AED" → the portal converts every source to the standard structure (coverage + quality flags, converted resource per source dataset) → merges/deduplicates into "Defibrylatory AED – zbiór ogólnopolski" with native CSV/XLSX/GeoJSON resources (table + map preview, `/1.4` API) → data owners validate their files against the structure via `POST /1.4/aed/validate` → the public sees the nearest AED on the simple map that reads the portal API. Flows 1–2 below describe the pre-pivot architecture (our separate backend), kept for history.

1. **Primary Happy Path (data pipeline → portal):** Operator runs the harvest → system queries `api.dane.gov.pl` for AED datasets and downloads their resources + fetches OSM AEDs → each source is mapped to the standard schema and gets a coverage report → records are merged and deduplicated into one national dataset → dataset is exposed via our dane.gov.pl-compatible API and CSV/JSON/GeoJSON/XLSX exports → in the local dane.gov.pl fork, the dataset "Defibrylatory AED – zbiór ogólnopolski" appears with resources pointing to our exports, and the portal shows its own dataset page, preview, and API → finally, the merged AEDs are visualised on a map in our Next.js app.
2. **Secondary Flow (data owner):** A data owner downloads the standard schema (`.xlsx` / CSV template / JSON Schema) to publish their AED data in the uniform format.

## MVP Scope (Must-Have)

- Standard AED schema in code + generated `.xlsx` / CSV template / JSON Schema
- Harvester: dane.gov.pl API search → download all AED resources; OSM Overpass for Poland
- Per-source column mapping, normalization, coverage report
- Merge + deduplication with provenance
- dane.gov.pl-compatible API (`/1.4`-style) + open exports with metadata
- Local dane.gov.pl fork running (without Discourse) with the merged dataset published in it, then deployed to Hetzner on its own port (DEC-005)
- Map of merged AEDs in our Next.js app (last MVP item, DEC-003)

## Nice-to-Have (Only After MVP Is Verified)

- Per-source coverage dashboard page in our Next.js app
- Scheduled/re-runnable refresh from the portal (harvest on demand)
- Data quality flags (missing coordinates, out-of-Poland points, stale inspection date)

## Explicit Out of Scope

- User accounts / auth in our app
- Writing to the real production dane.gov.pl (only the local fork)
- Crowdsourced reports, native mobile apps, Discourse forum in the fork

## Open Questions / Assumptions

- `[RESOLVED 2026-11-21]` Campaign name, slogan, logo, and brand book (25%) are produced by another team member, outside the code plan.
- `[OPEN]` Demo slot / format not specified by organizers.
- `[RESOLVED 2026-11-21]` Hetzner server already has 15 GB RAM / 8 vCPU / 4 GB swap / `vm.max_map_count=262144`; no rescale needed. Shared with other apps: port 3000 = `django-nextjs-template`, 3001 = `HN26-PCI` → our app uses `FRONTEND_PORT=3002`, fork `3080` (DEC-005).
- `[ASSUMPTION]` `dane-gov-pl/` (222 MB copy of upstream code) is git-ignored; our config/overrides for the fork live in a separate tracked folder (e.g. `fork-config/`) so changes are reviewable and the fork is deployed to Hetzner manually (DEC-005), never via the CI rsync.
- `[ASSUMPTION]` Fork setup is timeboxed (~2 h); fallback if it cannot run in time = dane.gov.pl-style dataset page in our Next.js app embedding the data.
- `[ASSUMPTION]` Source datasets found on 2026-11-21: Krosno, Marki, Przemyśl (CSV/GeoJSON/JSON/XML), Legionowo, "Lokalizacja defibrylatorów (AED)" — harvester discovers them dynamically, not hardcoded.
- `[ASSUMPTION]` OSM data is used under ODbL with attribution; merged dataset licence follows the sources (to be stated in metadata).
