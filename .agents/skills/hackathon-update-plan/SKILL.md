---
name: hackathon-update-plan
description: >-
  Incorporate new requirements, mentor feedback, extra user notes, or scope/design pivots mid-hackathon.
  Logs a numbered DEC-XXX in docs/04-decisions.md and propagates updates across docs/01-brief.md,
  docs/02-ui-system.md, docs/03-architecture.md, docs/05-plan.md, and docs/tasks/TXX-*.md.
---

# Update Plan Mid-Hackathon

Safely absorb new information or requirement changes during development without losing track of past decisions or breaking completed tasks.

## Steps

1. **Gather New Information & Current State**
   - Read the user's new request plus `docs/inputs/my-notes.md`, `docs/04-decisions.md`, `docs/05-plan.md`, `docs/03-architecture.md`, and `docs/01-brief.md`.
   - Identify every affected requirement (`REQ-XX`), architectural component, and task (`TXX`).
   - Re-check the remaining time against the code freeze in `docs/01-brief.md`; if the change does not fit, propose what to cut.

2. **Record the Decision (`docs/04-decisions.md`)**
   - Append the next numbered entry `DEC-XXX` with Date/Time (from `date '+%Y-%m-%d %H:%M'`, never guessed), `Status: Accepted`, `Context / New Info`, `Decision`, and `Affected Docs & Tasks`.
   - If this reverses an earlier decision, update the older decision's `Status` to `Superseded by DEC-XXX` (never delete history).

3. **Propagate Updates Consistently**
   - Update `docs/01-brief.md` (and `AGENTS.md` brief if the core demo goal, user flow, or deadline changed).
   - Update `docs/02-ui-system.md` if global UI shell, tokens, or shared primitives changed.
   - Update `docs/03-architecture.md` if models, API endpoints, routes, or env vars changed.
   - Update `docs/05-plan.md` and `docs/tasks/TXX-*.md`, always keeping both in sync, by task `Status`:
     - `TODO`: update the spec in place.
     - `DESIGN_REVIEW` / `DESIGN_READY`: update the spec; if the UI requirements changed significantly, set `Status` back to `TODO`, reset `## UI Design (Per-Task)` to `PENDING`, and clear **Approved** (the design must be re-approved).
     - `IN_PROGRESS`: stop and tell the user what the change means for the work in progress; with their OK, update the spec (and reset the design approval as above if the UI changed significantly), then resume or set `Status` back to `TODO`.
     - `VERIFIED`: never rewrite silently — add a new follow-up task from `docs/tasks/_template.md` instead.
     - Dropped tasks: set `Status` to `CANCELLED` and note `DEC-XXX` inside their task file.
     - New features: add new tasks (`TXX`) from `docs/tasks/_template.md` with `Status: TODO` and a real spec link in `docs/05-plan.md`; update `Target Task(s)` in `docs/01-brief.md`.

4. **Confirm With User**
   - Present a concise diff summary (`DEC-XXX`, updated docs, added/modified/cancelled tasks, reset design approvals, and any updated verification steps) and wait for confirmation before implementing affected tasks.
   - Explicitly name the next task and skill (`hackathon-ui-design` or `hackathon-run-task`) to resume with once confirmed.
