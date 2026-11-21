# 05 — Master Implementation Plan

> Vertical-slice development roadmap. Each task links to a dedicated verifiable spec in `docs/tasks/TXX-*.md`. `hackathon-plan` replaces the `<Example: ...>` rows below with real tasks and links.

## Task Status Legend

Status lives in each task file's `Status` field; this table mirrors it.

- `TODO` — Planned; ready for design (if UI-facing) or implementation (if backend/infra only, once dependencies are `VERIFIED`).
- `DESIGN_REVIEW` — `## UI Design (Per-Task)` written (`hackathon-ui-design`) and **awaiting user approval**. Not ready for implementation.
- `DESIGN_READY` — UI design explicitly approved by the user (approval date recorded in the task); ready for implementation.
- `IN_PROGRESS` — Currently being implemented, or implemented and awaiting the user's manual verification.
- `VERIFIED` — Automated checks passed AND the user confirmed the manual verification steps.
- `CANCELLED` — Dropped via a `DEC-XXX` entry in `docs/04-decisions.md`.

## Milestone 1 — Core Vertical Slice (MVP Skeleton)

| ID | Task | Layer | UI Design? | Depends On | Status | Spec |
| --- | --- | --- | --- | --- | --- | --- |
| `T01` | `<Example: Core domain model + CRUD API>` | Backend | No | — | `TODO` | [T01](tasks/_template.md) |
| `T02` | `<Example: Primary user workflow screen>` | Full-Stack | Yes | `T01` | `TODO` | [T02](tasks/_template.md) |

## Milestone 2 — Core Features

| ID | Task | Layer | UI Design? | Depends On | Status | Spec |
| --- | --- | --- | --- | --- | --- | --- |

## Milestone 3 — Demo Polish & End-to-End Readiness

| ID | Task | Layer | UI Design? | Depends On | Status | Spec |
| --- | --- | --- | --- | --- | --- | --- |
