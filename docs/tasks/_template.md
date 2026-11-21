# `TXX` — `<Task Title>`

- **Status:** `TODO | DESIGN_REVIEW | DESIGN_READY | IN_PROGRESS | VERIFIED | CANCELLED`
- **Layer:** `Backend | Frontend | Full-Stack | Infra`
- **UI Design Required:** `Yes | No`
- **Depends On:** `<None or T01, T02>`
- **Traces To:** `<REQ-01, DEC-001>`

## Goal & User Outcome

`<1-2 sentences explaining what works end-to-end once this task is verified.>`

## Scope & Non-Goals

- **In Scope:** `<Bullet list>`
- **Out of Scope:** `<Bullet list>`

## UI Design (Per-Task)

> If `UI Design Required` is `No`, replace this section with `N/A — backend/infra only.`
> Otherwise leave as `PENDING` during `hackathon-plan` and fill via `hackathon-ui-design` **before** implementing UI code.
> Design progress is tracked only in the task `Status` above (`TODO` -> `DESIGN_REVIEW` -> `DESIGN_READY`).

- **Approved:** `— | YYYY-MM-DD HH:MM (filled only after explicit user approval)`
- **Route(s):** `<e.g., /items, /items/[id]>`
- **Reference Sketch / Assets:** `<None or docs/inputs/ui/TXX-screen.png>`
- **Layout & Information Hierarchy:**
  ```text
  +----------------------------------------------------------+
  | Header / Page Title + Primary Action                     |
  +----------------------------------------------------------+
  | Main Content / Form / List / Feedback Banner             |
  +----------------------------------------------------------+
  ```
- **Components (Reused vs. New):**
  - Reused from `docs/02-ui-system.md`: `<list>`
  - New components: `<name, path, responsibility>`
- **Interactive States:**
  - **Loading:** `<Skeleton / button disabled + aria-busy>`
  - **Empty:** `<Clear empty-state message + primary CTA>`
  - **Error:** `<Accessible inline/banner error with retry action>`
  - **Success:** `<Updated view + aria-live="polite" confirmation>`
- **API Fields & Contracts Consumed:** `<Exact endpoint(s), request fields, and response fields>`
- **WCAG 2.2 AA Checks:** Light palette contrast (`>= 4.5:1` text, `>= 3:1` borders), `:focus-visible`, `>= 44px` (`min-h-11`) controls, semantic labels/headings, non-color status indicators.

## Technical Implementation Plan

- **Backend (`backend/`):**
  - Models / Migrations: `<file paths + fields>`
  - Serializers / Views / URLs: `<file paths + OpenAPI schema updates>`
  - Unit Tests: `<test cases in apps/<feature>/tests.py>`
- **Frontend (`frontend/`):**
  - Server / Client Components & `src/lib/api.ts`: `<file paths>`
- **Config / Env:** `<None or .env.example / compose*.yaml updates>`

## Acceptance Criteria

- [ ] `<Observable behavior 1>`
- [ ] `<Observable behavior 2>`

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `TXX`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes (no missing migrations); migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes (required if frontend code, Dockerfiles, dependencies, or Compose files changed, or this is a milestone's last task)

### Manual Verification
1. `<Exact URL / curl / Swagger UI step and expected result>`
2. `<Exact browser UI click-through + database persistence check across refresh>`

### Sign-Off
- **Verified By:** `<User>` on `<YYYY-MM-DD HH:MM>` (only the user confirms manual verification)
- **Notes / Follow-Ups:** `<Any caveats or follow-up tasks>`
