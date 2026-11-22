# `T19` — Universal standards on the server + demo script

- **Status:** `VERIFIED`
- **Layer:** `Backend (fork)`
- **UI Design Required:** `No`
- **Depends On:** `T18`
- **Traces To:** `REQ-15`, `REQ-16`, `DEC-019`, `DEC-020`
- **Estimate:** 0.5 h + video ~45 min

## Goal & User Outcome

The public portal shows both standards; the demo script has a "same engine, different data" step with screenshots.

## Scope & Non-Goals

- **In Scope:**
  - Sync `mcod_aed` to Hetzner, migrate, load the nursery standard, import + aggregate there
  - `docs/demo-script.md`: new step + screenshots; README section
  - **Automatic aggregation (DEC-020):** a source file that passes its standard refreshes the common dataset (debounced Celery run); admin message on the resource page; before/after demo files for Krosno (AED + nurseries)
  - **Demo video** (user request 2026-11-22 ~05:30): recorded on the public server after the deploy — one MP4 of max **3 min** with **Polish captions** + one clip per step, following the DEC-020 flow (two standards → broken file rejected → corrected file accepted → common dataset refreshed automatically, for nurseries and AED), headless Chrome screencast → `ffmpeg` (from `imageio-ffmpeg` in a scratch virtualenv); files in `docs/demo/video/`
- **Out of Scope:**
  - Changing the verified AED code path; full admin field editor (DEC-019)

## UI Design (Per-Task)

N/A — backend/infra only (portal admin/portal pages are existing UI).

## Acceptance Criteria

- [x] https://mcod.2.29.205.102.sslip.io shows the nursery common dataset; admin shows both standards
- [x] Demo script step + screenshots added (step 8b + main flow DEC-020)
- [x] A corrected file accepted into a standard dataset refreshes its common dataset without clicking (both standards; server: nurseries 85 → 88 run #4, AED 18 776 → 18 779 run #5)
- [x] `docs/demo/video/misja-aed-demo.mp4` (1:57, Polish captions, 1440×900, 4.1 MB) + 9 clips in `docs/demo/video/kroki/`

## Verification Checklist

### Automated Checks
- [x] `fork-config/test.sh` passes — 79 tests OK (new: automatic aggregation queue/debounce/guards + admin note)
- [ ] `make test` / `make lint` — not run: the retired `backend` container is down and no repo code outside `fork-config/` changed
- [x] Fork healthy locally and on the server (admin/celery/api restarted; `AED_AUTO_AGGREGATION=True`)

### Manual Verification
1. Public portal search "żłobki" → common dataset → Tabela
2. Public admin → Standardy danych → both standards
3. Watch `docs/demo/video/misja-aed-demo.mp4` (1:57) and the clips in `docs/demo/video/kroki/`
4. Live flow (DEC-020) on https://admin.mcod.2.29.205.102.sslip.io → Resources → Dodaj: dataset "Żłobki publiczne" (4219), file `docs/demo/samples/zlobki-krosno-nowe-bledny.csv`, Opublikowany → refused with per-row errors; then `zlobki-krosno-nowe-poprawiony.csv` → saved; refresh the resource page after ~20 s → "Zbiór zbiorczy … odświeżony automatycznie … 88 obiektów"; Agregacje shows "auto: zasób N …"
5. Same with dataset 4211 (Krosno AED) and `aed-krosno-nowe-{bledny,poprawiony}.csv` → 18 779 (~1 min)
6. Reset afterwards (demo-script "Reset after a rehearsal"): delete the "(demo)" resources + "Uruchom agregację" for both standards (server currently reset to 85 / 18 776)

### Sign-Off
- **Verified By:** user (manual check approved) — 2026-11-22 06:37
- **Notes / Follow-Ups:** Video caption in step 4 says "8 innych instytucji" — strictly 7 others (Krosno is one of the 8). Right after an automatic AED refresh the portal's Mapa tab is briefly unavailable (~1–2 min) while the new CSV is re-indexed — show the map a bit later.
