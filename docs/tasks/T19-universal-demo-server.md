# `T19` — Universal standards on the server + demo script

- **Status:** `TODO`
- **Layer:** `Backend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T18`
- **Traces To:** `REQ-15`, `REQ-16`, `DEC-019`
- **Estimate:** 0.5 h + video ~45 min

## Goal & User Outcome

The public portal shows both standards; the demo script has a "same engine, different data" step with screenshots.

## Scope & Non-Goals

- **In Scope:**
  - Sync `mcod_aed` to Hetzner, migrate, load the nursery standard, import + aggregate there
  - `docs/demo-script.md`: new step + screenshots; README section
  - **Demo video** (user request 2026-11-22 ~05:30): recorded on the public server after the deploy — one MP4 of max **3 min** with **Polish captions** + one clip per step (≈ 9 steps), headless Chrome screencast → `ffmpeg` (from `imageio-ffmpeg` in a scratch virtualenv); files in `docs/demo/video/`
- **Out of Scope:**
  - Changing the verified AED code path; full admin field editor (DEC-019)

## UI Design (Per-Task)

N/A — backend/infra only (portal admin/portal pages are existing UI).

## Acceptance Criteria

- [ ] https://mcod.2.29.205.102.sslip.io shows the nursery common dataset; admin shows both standards
- [ ] Demo script step + screenshots added
- [ ] `docs/demo/video/misja-aed-demo.mp4` (≤ 3:00, Polish captions) + per-step clips

## Verification Checklist

### Automated Checks
- [ ] `fork-config/test.sh` passes (incl. new tests for `T19`; all AED tests unchanged and green)
- [ ] `make test` / `make lint` still pass for the repo
- [ ] Fork healthy (`manage.py check`, migrations applied, no hook errors)

### Manual Verification
1. Public portal search "żłobki" → common dataset → Tabela
2. Public admin → Standardy danych → both standards

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
