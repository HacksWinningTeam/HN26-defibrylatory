---
name: hackathon-ui-design
description: >-
  Design the screen layout, component hierarchy, interactive states, API fields, and WCAG 2.2 AA
  accessibility checks for a single UI-facing task TXX right before implementing it. Updates
  docs/tasks/TXX-*.md, sets status to DESIGN_REVIEW, and moves it to DESIGN_READY only after
  explicit user approval.
---

# Per-Task UI Design

Create a concrete, build-ready UI specification for one task `TXX` right before coding it, using the latest codebase and any mid-hackathon updates.

**Status flow:** `TODO` -> `DESIGN_REVIEW` (design written, awaiting user) -> `DESIGN_READY` (user approved). Only the user's explicit approval moves a task to `DESIGN_READY`.

## Steps

1. **Load Context**
   - Read `frontend/AGENTS.md`, `docs/02-ui-system.md`, `docs/03-architecture.md`, `docs/04-decisions.md`, and the target `docs/tasks/TXX-*.md`.
   - Check `docs/inputs/ui/` for any user-provided screenshots, wireframes, or brand assets relevant to `TXX`, plus existing components in `frontend/src/components/`.
   - If the task is already `DESIGN_REVIEW`, skip to step 5 and re-present the existing design.

2. **Verify Prerequisites**
   - Ensure the task needs UI design (`UI Design Required: Yes`) and its `Status` is `TODO` or `DESIGN_REVIEW`.
   - Confirm exact API endpoints and payload fields available (or needed) in `docs/03-architecture.md` and `backend/apps/`.

3. **Fill `## UI Design (Per-Task)` in `docs/tasks/TXX-*.md`**
   - **Route(s)** and **Reference Sketch / Assets**.
   - **Layout & Information Hierarchy:** Clear ASCII wireframe or section-by-section breakdown matching the app shell in `docs/02-ui-system.md`.
   - **Components (Reused vs. New):** List reused components from `docs/02-ui-system.md` and any new Server/Client components to create.
   - **Interactive States:** Concrete specs for **Loading**, **Empty**, **Error** (with recovery action), and **Success** (`aria-live="polite"` where dynamic).
   - **API Fields & Contracts Consumed:** Exact request/response fields and same-origin proxy path (`/api/...`).
   - **WCAG 2.2 AA Checks:** Light baseline (no unrequested dark mode), `>= 4.5:1` text contrast, `>= 3:1` UI borders/controls, `:focus-visible`, `>= 44px` (`min-h-11`) targets, semantic landmarks/labels, and non-color status indicators.
   - Leave **Approved** as `—`.

4. **Sync Impacted Docs (If UI Design Reveals Gaps)**
   - If UI design introduces a reusable primitive, add it to `docs/02-ui-system.md`.
   - If UI design requires new/changed backend fields or endpoints, update `docs/03-architecture.md`, note the backend changes in `docs/tasks/TXX-*.md` (or add a prerequisite task), and append a `DEC-XXX` in `docs/04-decisions.md` (timestamp from `date '+%Y-%m-%d %H:%M'`).

5. **Request Approval (`DESIGN_REVIEW`)**
   - Set `Status` to `DESIGN_REVIEW` in `docs/tasks/TXX-*.md` and `docs/05-plan.md`.
   - Present the UI design summary (wireframe, states, API fields, any doc/backend changes) and ask the user to approve or request changes. **Do not write UI code in this skill.**

6. **Record the Outcome**
   - **Approved** (explicit user confirmation only): set `Status` to `DESIGN_READY` in both files and fill **Approved** with `YYYY-MM-DD HH:MM` from `date`. Then offer to start `hackathon-run-task`.
   - **Changes requested:** revise the section, keep `DESIGN_REVIEW`, and ask again.
   - **No answer yet / session ends:** leave it as `DESIGN_REVIEW`; the next session re-presents it instead of implementing.
