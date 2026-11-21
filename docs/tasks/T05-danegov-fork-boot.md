# `T05` — Run the dane.gov.pl fork locally (fork-config)

- **Status:** `VERIFIED`
- **Layer:** `Infra`
- **UI Design Required:** `No`
- **Depends On:** None (start in parallel with T01 — slow image build)
- **Traces To:** `REQ-09`, `DEC-002`, `DEC-004`

## Goal & User Outcome

The upstream dane.gov.pl portal (backend + Angular frontend) runs locally from `dane-gov-pl/` using our tracked `fork-config/`, with admin login, API and frontend reachable at `https://admin.mcod.local`, `https://api.mcod.local/1.4/`, `https://mcod.local`.

## Scope & Non-Goals

- **In Scope:**
  - `fork-config/backend.env` (from `env.sample`, `DISCOURSE_FORUM_ENABLED=false`), `local.py` (from sample), `compose.override.yml` (no discourse/flower/rdfdb deps, conflicting host ports reset, `aed.mcod.local` alias on nginx), `nginx/07-aed.conf.template` (https `aed.mcod.local` → `http://host.docker.internal:8000`, `extra_hosts: host-gateway`)
  - `fork-config/setup.sh`: copy config into `dane-gov-pl/backend_latest`, build only needed services, `init_mcod_db`, `search_index --rebuild -f`, start services; `fork-config/README.md` with one-time sudo steps (`/etc/hosts`, `vm.max_map_count`)
  - Angular frontend on host: `npm ci && npx ng serve -c local --proxy-config proxy.local.conf.json --port 4200`
  - Timebox 2 h → go/no-go recorded as DEC; fallback = dataset page in our Next.js
- **Out of Scope:**
  - Discourse, CMS (unless home page needs it), Jupyter/lab add-ons
  - Deploying fork to Hetzner

## UI Design (Per-Task)

N/A — backend/infra only.

## Technical Implementation Plan

- **Config only (`fork-config/`)**, no changes inside `dane-gov-pl/` beyond copied config files.
- Known gotchas: Python 3.8 app image build 20–40 min (start first, in background); ES needs `vm.max_map_count=262144`; never run bare `docker compose up` in the fork (pulls private discourse image); `mcod-local-run` uses `--profile manual`; fixture admin `admin@mcod.local` / `testadmin123!`.
- No unit tests (infra); our own stack checks must still pass and our ports (8000/3000) must not conflict.

## Acceptance Criteria

- [x] `https://admin.mcod.local` login works with fixture admin
- [x] `https://api.mcod.local/1.4/datasets` returns the fixture dataset
- [x] `https://mcod.local` shows the portal; dataset page opens
- [x] `https://aed.mcod.local/api/health/` (from fork network) reaches our backend
- [x] Our stack (`make up-d`) runs at the same time without port conflicts

## Verification Checklist

### Automated Checks
- [x] `make test` passes (including new/updated unit & API tests for `T05`)
- [x] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [x] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [x] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [~] `make build-prod` not run — no app code/compose changes in T05

### Manual Verification
1. Follow `fork-config/README.md` from scratch; time it
2. Open the three URLs above in the browser (accept self-signed cert)
3. `docker compose -f ... exec mcod-local-celery curl -k https://aed.mcod.local/api/health/` → `{"status": "ok"...}`

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-21 19:24
- **Notes / Follow-Ups:** GO logged as DEC-006 (2026-11-21 19:12). Verified via `curl --resolve` + headless Chrome (hosts line not yet added). Known harmless issues: Celery RDF task errors (no rdfdb), empty CMS (blank footer/news), cert name mismatch for `aed.mcod.local` in browsers, admin media downloads may 502. Remaining manual step: user adds hosts line and opens URLs in browser.
