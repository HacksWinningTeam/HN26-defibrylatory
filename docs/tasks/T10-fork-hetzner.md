# `T10` — Deploy the dane.gov.pl fork to Hetzner

- **Status:** `VERIFIED`
- **Layer:** `Infra`
- **UI Design Required:** `No`
- **Depends On:** `T06`
- **Traces To:** `REQ-14`, `REQ-09`, `DEC-005`

> **Cancelled by DEC-014, revived by DEC-018 (2026-11-22 ~02:50):** judges must see the app → deploy the fork *with* `mcod.aed` (standard field, validation, aggregation, `/1.4/aed/*`) on Hetzner port 3080, data created on the server by `aed-demo.sh`. Depends now on T09 instead of T06.

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

> As built (DEC-018 + user choice): port **443** with **Let's Encrypt** certificates (no warnings, no port in URLs) instead of 3080 + self-signed.

- [x] https://mcod.2.29.205.102.sslip.io shows the portal; *Defibrylatory AED – zbiór ogólnopolski* (4217) with table + map preview (18,776 rows/points), verified in Chrome **without** ignoring certificate errors
- [x] https://api.mcod.2.29.205.102.sslip.io/1.4/aed/sources, `/1.4/aed/devices`, `/1.4/aed/schema`, `/1.4/aed/validate` work; https://admin.mcod.2.29.205.102.sslip.io login page
- [x] Other apps on the server still answer (3000/3001/3002 → 200); the fork lives outside the CI dir, so a push to `main` does not touch it
- [x] Server memory OK (~7 GB used of 15 GB, ~8 GB available, swap unused)

## Verification Checklist

### Automated Checks
- [ ] `make test`, `make lint`, `make schema-check`, `make migrations-check` still pass (no app code change expected)
- [ ] `make build-prod` passes
- [ ] `DJANGO_SECRET_KEY=ci-check docker compose -f compose.prod.yaml config --quiet` passes

### Observed Results (2026-11-22 ~03:35)
- Images shipped (`docker save | zstd | ssh hack docker load`, ~2 min), `fork-config/hetzner/deploy.sh` (sync, `apply-hostnames.sh`, `certs.sh`, `FORK_SKIP_BUILD=1 setup.sh`), then `aed-demo.sh` on the server: 6 sources → 18,776 AEDs; first-time national CSV map/table configured automatically.
- Fixed during deploy: `setup.sh` re-copied un-rewritten config (deployed `fork-config` copies are rewritten too); Celery's `mcod.local.pem` mount (certificate now installed under that name); Angular/Vite host check (`allowedHosts: true` in the deployed `angular.json`).
- **Warsaw city API (dane.um.warszawa.pl) times out from the Hetzner server** (works from Poland): the connector falls back to the committed copy of the Warsaw API answer from 2026-11-21, **labelled** in the aggregation report and command output ("API m.st. Warszawy niedostępne z tego serwera – użyto oznaczonej kopii offline …").
- Screenshots: `docs/demo/screenshots/T10-pub-*.png`.

### Manual Verification
1. From any device (e.g. phone on mobile data): https://mcod.2.29.205.102.sslip.io → search "defibrylator" → 6 source datasets + "Defibrylatory AED – zbiór ogólnopolski" → CSV → Tabela / Mapa (no certificate warning)
2. https://admin.mcod.2.29.205.102.sslip.io → `admin@mcod.local` / `testadmin123!` → sidebar *Standardy danych* → Uruchom agregację → Agregacje AED
3. https://api.mcod.2.29.205.102.sslip.io/1.4/aed/sources and `/1.4/aed/schema`
4. `ssh hack 'free -h; docker ps | grep -c mcod'` → memory fine, 11 fork containers up

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-22 03:28
- **Notes / Follow-Ups:** Fallback if server memory is insufficient: demo local fork via screen share + screenshots in slides.
