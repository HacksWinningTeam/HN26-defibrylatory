# `T15` — Next.js map reads data from the dane.gov.pl fork API

- **Status:** `TODO`
- **Layer:** `Frontend`
- **UI Design Required:** `No`
- **Depends On:** `T13`
- **Traces To:** `REQ-13, DEC-014, DEC-010`
- **Estimate:** 1 h

## Goal & User Outcome

The "Najbliższy AED" page (T07) shows AEDs and source statistics coming from the portal (`/1.4/aed/devices`, `/1.4/aed/sources`) instead of our own backend; UI unchanged.

## Scope & Non-Goals

- **In Scope:**
  - Server-side env `DANEGOV_API_URL` (e.g. `https://api.mcod.local` via the fork network, TLS self-signed handled server-side) mirrored in `.env.example`, `compose.yaml`, `compose.prod.yaml`
  - Same-origin route for the browser (`/portal-api/aed/devices` proxied by `src/proxy.ts` or a Next.js route handler) — no backend origin in browser code
  - `DataInfo` links point to portal resources (schema, common dataset, `/1.4/aed/validate` docs) instead of `/api/...` of our backend
  - Frontend container joins the fork network (or uses host-gateway) to reach the fork API
- **Out of Scope:**
  - UI redesign (design v2 stays as approved)

## UI Design (Per-Task)

N/A — frontend data-source switch only; the approved T07 design v2 is unchanged.

## Technical Implementation Plan

- `src/lib/api.ts`: `fetchAeds()` / `fetchSources()` switch to the fork endpoints; adapt `/1.4/aed/sources` shape in a small mapper; keep unit tests green.

## Acceptance Criteria

- [ ] `/` shows nearest AEDs with data from the fork (stop our `backend` container → page still works)
- [ ] "Skąd są te dane?" shows the portal's source counts and links to the portal dataset
- [ ] `make build-prod` passes

## Verification Checklist

### Automated Checks
- [ ] `fork-config/test.sh` passes (pytest for `mcod.aed` inside the fork's `mcod-admin` container, incl. new tests for `T15`)
- [ ] `make test` / `make lint` still pass for the repo (no regressions; `backend/` frozen)
- [ ] Fork boots cleanly after `fork-config/setup.sh` (admin, api, celery healthy; `manage.py check` OK; `mcod.aed` migrations applied)
- [ ] `make build-prod` passes (frontend changed)
### Manual Verification
1. `docker compose stop backend` → open `http://localhost:3000/` → map + nearest AED still load
2. Links in "Skąd są te dane?" open the portal dataset / schema / validation API

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
