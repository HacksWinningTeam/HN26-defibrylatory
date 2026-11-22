# 05 — Master Implementation Plan

> Vertical-slice development roadmap. Each task links to a dedicated verifiable spec in `docs/tasks/TXX-*.md`.

## Task Status Legend

Status lives in each task file's `Status` field; this table mirrors it.

- `TODO` — Planned; ready for design (if UI-facing) or implementation (if backend/infra only, once dependencies are `VERIFIED`).
- `DESIGN_REVIEW` — `## UI Design (Per-Task)` written (`hackathon-ui-design`) and **awaiting user approval**. Not ready for implementation.
- `DESIGN_READY` — UI design explicitly approved by the user (approval date recorded in the task); ready for implementation.
- `IN_PROGRESS` — Currently being implemented, or implemented and awaiting the user's manual verification.
- `VERIFIED` — Automated checks passed AND the user confirmed the manual verification steps.
- `CANCELLED` — Dropped via a `DEC-XXX` entry in `docs/04-decisions.md`.

> **DEC-014 pivot (2026-11-22 00:00):** ~9 h to code freeze; new work T11–T15 + T09 ≈ 9 h. Cut order if late (DEC-015): converted per-source resources in T13 → T15 (map keeps the old backend as data source) → admin page in T13 (keep the command) → XLSX/GeoJSON outputs (keep CSV). T08/T10 cancelled.
>
> Previous budget (from 2026-11-21 18:10 to code freeze 2026-11-22 09:00 ≈ 14.5 h): estimates total ≈ 17 h (incl. T10 2.5 h, DEC-005) — over budget, with the T05 image build running in the background in parallel. Cut order if late: T08 → map extras in T07 → T10 falls back to local fork + screenshots → OSM (keep dane.gov.pl sources). Branding (logo, slogan, brand book, 25%) and slides are **not** code tasks and run in parallel (another team member).

## Milestone 1 — Core Vertical Slice (Schema → Data → API) + Fork Boot in Parallel

| ID | Task | Layer | UI Design? | Depends On | Est. | Status | Spec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `T01` | Standard AED schema + downloads (xlsx / CSV / JSON Schema) | Backend | No | — | 1.5 h | `VERIFIED` | [T01](tasks/T01-standard-aed-schema.md) |
| `T02` | Harvester: dane.gov.pl API + OSM raw download | Backend | No | `T01` | 1.5 h | `VERIFIED` | [T02](tasks/T02-harvest-sources.md) |
| `T03` | Parse, normalize, coverage report, merge & dedupe | Backend | No | `T02` | 2.5 h | `VERIFIED` | [T03](tasks/T03-normalize-merge.md) |
| `T04` | dane.gov.pl-compatible API (/api/1.4) + exports | Backend | No | `T03` | 1.5 h | `VERIFIED` | [T04](tasks/T04-danegov-compatible-api-exports.md) |
| `T05` | Run dane.gov.pl fork locally (fork-config) — start now, parallel | Infra | No | — | 2 h | `VERIFIED` | [T05](tasks/T05-danegov-fork-boot.md) |

## Milestone 2 — Core Features (Portal + Map)

| ID | Task | Layer | UI Design? | Depends On | Est. | Status | Spec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `T06` | Publish national AED dataset in the fork | Infra | No | `T04`, `T05` | 1.5 h | `VERIFIED` | [T06](tasks/T06-publish-to-fork.md) |
| `T07` | AED map in Next.js — "Najbliższy AED" from BCTW Bydgoszcz (/) | Full-Stack | Yes | `T04` | 2 h | `VERIFIED` | [T07](tasks/T07-aed-map-nextjs.md) |

## Milestone 3 — Pivot (DEC-014): AED Aggregation + Validation Inside the dane.gov.pl Fork

Order: T11 → T14 (validation needs only the ported schema/parsers — the explicitly requested API lands early) → T12 → T13 → T15 → T09.

| ID | Task | Layer | UI Design? | Depends On | Est. | Status | Spec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `T11` | `mcod.aed` app in the fork: install mechanism, schema + parsers port, `GET /1.4/aed/schema`, data standard + "Standard danych" dataset field (DEC-015) | Backend (fork) | No | `T05` | 2 h | `VERIFIED` | [T11](tasks/T11-mcod-aed-scaffold-schema.md) |
| `T14` | Validation API `POST /1.4/aed/validate` + automatic validation on upload that blocks publishing (DEC-015) | Backend (fork) | No | `T11` | 2 h | `TODO` | [T14](tasks/T14-validation-api.md) |
| `T12` | Mirror AED source datasets from dane.gov.pl into the fork (files + connected APIs) | Backend (fork) | No | `T11` | 1.5 h | `TODO` | [T12](tasks/T12-import-aed-sources-into-fork.md) |
| `T13` | In-portal aggregation → converted sources + common dataset published natively; `/1.4/aed/sources`, `/1.4/aed/devices` | Backend (fork) | No | `T12` | 2.5 h | `TODO` | [T13](tasks/T13-in-portal-aggregation.md) |
| `T15` | Next.js map reads data from the fork API | Frontend | No | `T13` | 1 h | `TODO` | [T15](tasks/T15-map-reads-fork-api.md) |

## Milestone 4 — Demo Polish & End-to-End Readiness

| ID | Task | Layer | UI Design? | Depends On | Est. | Status | Spec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `T08` | Schema & source coverage page (/schemat) — cancelled (DEC-014) | Frontend | Yes | `T04` | 1 h | `CANCELLED` | [T08](tasks/T08-schema-coverage-page.md) |
| `T10` | Deploy dane.gov.pl fork to Hetzner — cancelled (DEC-014) | Infra | No | `T06` | 2.5 h | `CANCELLED` | [T10](tasks/T10-fork-hetzner.md) |
| `T09` | Demo readiness (in-portal flow), offline snapshot, demo script, retire `backend/` decision | Infra | No | `T13`, `T14`, `T15` | 1 h | `TODO` | [T09](tasks/T09-demo-readiness.md) |
