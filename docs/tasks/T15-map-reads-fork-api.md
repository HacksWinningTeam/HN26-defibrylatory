# `T15` — Next.js map reads data from the dane.gov.pl fork API

- **Status:** `VERIFIED`
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

- [x] `/` shows nearest AEDs with data from the fork, with our `backend` and `db` **stopped** (`x-aed-data-source: dane.gov.pl fork`, 18,776 AEDs, ~1.4 MB gzip)
- [x] "Skąd są te dane?" shows the portal's counts/sources ("18 776 AED z 6 źródeł") and links to the portal: schema XLSX/CSV/JSON (`/1.4/aed/schema*`), common dataset page, `/1.4/aed/devices`, `/1.4/aed/sources`, `/1.4/aed/validate`
- [x] `make build-prod` passes (new route `/portal-api/aed/devices` in the standalone build)

## Verification Checklist

### Automated Checks
- [~] `fork-config/test.sh` — not affected (no fork code changed in T15)
- [x] `make test` / `make lint` still pass
- [x] Compose validated: `docker compose config --quiet`, prod config with `DJANGO_SECRET_KEY=ci-check`
- [x] `make build-prod` passes; frontend `npm test` 20 passed (2 new: portal sources mapper, `DANEGOV_API_URL` parsing); `make test` 83 / `make lint` / `make schema-check` / `make migrations-check` pass (backend started only for the checks)
### Observed Results (2026-11-22 ~02:35)
- Implementation: server-only `src/lib/portal.ts` (`DANEGOV_API_URL`, `mapPortalSources`), same-origin route handler `src/app/portal-api/aed/devices/route.ts` (fork `/1.4/aed/devices`, fallback to old backend `/api/aed/` when `DANEGOV_API_URL` is empty — keeps the Hetzner deploy working without the fork), `DataInfo` portal links (fixes the old `aed-schema.csv` 404 too).
- Local TLS: the frontend container resolves `api.mcod.local` to the host nginx (`extra_hosts: host-gateway`) and trusts the fork's dev certificate via `NODE_EXTRA_CA_CERTS` (certificate file only, mounted read-only) — no TLS checks disabled.
- Env: `DANEGOV_API_URL` mirrored in `.env.example`, `compose.yaml` (default `https://api.mcod.local`), `compose.prod.yaml` (default empty).
- Screenshot: `docs/demo/screenshots/T15-map-from-portal.png`.

### Manual Verification
1. With only the frontend running (`docker compose up -d --no-deps frontend`; backend/db stopped) open http://localhost:3000/ → 112 banner, nearest AED card, map with clusters load
2. `curl -sI localhost:3000/portal-api/aed/devices` → `x-aed-data-source: dane.gov.pl fork`
3. "Skąd są te dane?" → "18 776 AED z 6 źródeł", source list with institutions; links open https://api.mcod.local/1.4/aed/... and the portal dataset (accept the self-signed certificate once)
4. Optional: re-run aggregation in the admin → reload `/` → the "aktualizacja" date/time changes

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-22 02:29
- **Notes / Follow-Ups:** —
