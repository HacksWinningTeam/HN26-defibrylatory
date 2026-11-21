# `T10` — Deploy the dane.gov.pl fork to Hetzner

- **Status:** `TODO`
- **Layer:** `Infra`
- **UI Design Required:** `No`
- **Depends On:** `T06`
- **Traces To:** `REQ-14`, `REQ-09`, `DEC-005`

## Goal & User Outcome

Judges can open the dane.gov.pl fork with our published AED dataset on the Hetzner server (`ubuntu-4gb-hel1-2`) via `https://mcod.<ip>.sslip.io:3080` without editing `/etc/hosts`, next to our own app on port `3002` (3000/3001 are used by other apps on the shared server).

## Scope & Non-Goals

- **In Scope:**
  - `fork-config/hetzner/`: `compose.hetzner.yml` (only needed services, nginx published on `3080` only, ES default heap (server has 15 GB), `extra_hosts: host-gateway`), nginx templates with `server_name` for `mcod.` / `api.` / `admin.` / `aed.<ip>.sslip.io` (self-signed cert), `aed.` → `http://host-gateway:3002` (our app's same-origin `/api/exports/...`), env file with server hostnames (`API_URL`, `BASE_URL`, `ADMIN_URL`, allowed hosts, CSRF origins)
  - Angular prod build with API base pointing to `https://api.<ip>.sslip.io:3080` (or relative `/api` proxied by nginx), served statically by fork nginx
  - `fork-config/hetzner/deploy.sh`: build images locally → `docker save | ssh <server> docker load`; rsync `dane-gov-pl/` + `fork-config/` to `/home/github/apps/danegov-fork/` (never inside the CI-synced app dir); remote `up -d`; `init_mcod_db`; ES index; run `publish_aed.py` with server URLs
  - Server prep: already done (15 GB RAM, swap, `vm.max_map_count`, ufw inactive, `/home/github/apps/danegov-fork/` exists); deploy via `ssh hack`
- **Out of Scope:**
  - Real domain / Let's Encrypt certificates
  - CI automation for the fork (manual deploy only)

## UI Design (Per-Task)

N/A — backend/infra only.

## Technical Implementation Plan

- **Config only:** `fork-config/hetzner/*`, `fork-config/README.md` section *Hetzner*.
- Risks: memory (OOM → check `dmesg`, lower limits, drop `mcod-smtp`), secure-cookie/https settings on a non-standard port, ALLOWED_HOSTS with port, Angular absolute API URLs in `environment.prod.ts`.
- Our app's CI deploy must keep working: nothing added to `compose.prod.yaml` or the CI dir.

## Acceptance Criteria

- [ ] `https://mcod.<ip>.sslip.io:3080` shows the portal with dataset *Defibrylatory AED – zbiór ogólnopolski*, table + map preview
- [ ] `https://api.<ip>.sslip.io:3080/1.4/datasets?q=defibrylatory` returns it
- [ ] Our app at `http://<ip>:3002/mapa` still works; a push to `main` does not touch the fork
- [ ] Server stays responsive (free memory / no OOM kills during a 10-minute demo run)

## Verification Checklist

### Automated Checks
- [ ] `make test`, `make lint`, `make schema-check`, `make migrations-check` still pass (no app code change expected)
- [ ] `make build-prod` passes
- [ ] `DJANGO_SECRET_KEY=ci-check docker compose -f compose.prod.yaml config --quiet` passes

### Manual Verification
1. Open the three fork URLs from a phone on mobile data (no hosts edits) → accept cert → dataset visible
2. `ssh <server> free -h && docker stats --no-stream` → no container restarting, swap in use acceptable
3. Push a trivial commit to `main` (user) → fork still running afterwards

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** Fallback if server memory is insufficient: demo local fork via screen share + screenshots in slides.
