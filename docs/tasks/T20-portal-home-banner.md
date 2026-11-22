# `T20` — AEDane banner on the portal home page

- **Status:** `VERIFIED`
- **Layer:** `Frontend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T19`
- **Traces To:** `DEC-021`

## Goal & User Outcome

The dane.gov.pl fork's main page (https://mcod.2.29.205.102.sslip.io/pl) shows the AEDane banner under the search box; clicking it opens the AED common dataset.

## Scope & Non-Goals

- **In Scope:**
  - `fork-config/mcod_aed/static/baner.png` (copy of `docs/inputs/ui/baner.png`), route `GET /1.4/aed/banner.png` (long cache)
  - `GET /1.4/standards/{code}/dataset` → 302 to the common dataset page in the portal
  - `fork-config/frontend/home.component.html` = upstream template + banner section (responsive `<img>` with Polish alt text, full container width, link); bind-mounted over `frontend_latest/src/app/pages/home/home.component.html` in `fork-config/compose.override.yml`
  - Tests for both routes; deploy to the server
- **Out of Scope:** CMS (Wagtail) banner widgets, other portal pages

## UI Design (Per-Task)

N/A — one static image placed into the existing portal home page (portal styles; `img` with `alt`, link with focus ring from the portal CSS).

## Acceptance Criteria

- [x] Banner visible on the home page locally and on the server, scales down on mobile (`docs/demo/screenshots/T20-portal-home-banner.png`)
- [x] Banner link opens "Defibrylatory AED – zbiór ogólnopolski" (server: 302 → /pl/dataset/4217,…)
- [x] `fork-config/test.sh` green

## Verification Checklist

### Automated Checks
- [x] `fork-config/test.sh` — 80 tests OK (new: banner PNG + common dataset redirect + 404)

### Manual Verification
1. https://mcod.2.29.205.102.sslip.io/pl → banner under the search box → click → common AED dataset

### Sign-Off
- **Verified By:** user (manual check approved) — 2026-11-22 06:55
- **Notes / Follow-Ups:** Server deploy = rsync `fork-config/` + `fork-config/hetzner/apply-hostnames.sh 2.29.205.102` (re-run after every rsync: it rewrites `compose.override.yml`, `backend.env`, the nginx template) + `fork-config/fork-compose.sh up -d --no-deps mcod-frontend` + restart `mcod-api`.
