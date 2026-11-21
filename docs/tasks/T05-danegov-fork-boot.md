# `T05` — Run the dane.gov.pl fork locally (fork-config)

- **Status:** `TODO`
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

- [ ] `https://admin.mcod.local` login works with fixture admin
- [ ] `https://api.mcod.local/1.4/datasets` returns the fixture dataset
- [ ] `https://mcod.local` shows the portal; dataset page opens
- [ ] `https://aed.mcod.local/api/health/` (from fork network) reaches our backend
- [ ] Our stack (`make up-d`) runs at the same time without port conflicts

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `T05`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes

### Manual Verification
1. Follow `fork-config/README.md` from scratch; time it
2. Open the three URLs above in the browser (accept self-signed cert)
3. `docker compose -f ... exec mcod-local-celery curl -k https://aed.mcod.local/api/health/` → `{"status": "ok"...}`

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** Go/no-go decision at ~2 h logged as DEC-XXX.
