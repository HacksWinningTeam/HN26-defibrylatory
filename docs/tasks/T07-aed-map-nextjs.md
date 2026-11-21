# `T07` — AED map in Next.js (/mapa)

- **Status:** `TODO`
- **Layer:** `Full-Stack`
- **UI Design Required:** `Yes`
- **Depends On:** `T04`
- **Traces To:** `REQ-13`, `REQ-10`, `DEC-003`, `DEC-004`

## Goal & User Outcome

Anyone opens `/mapa` in our Next.js app and sees all merged AEDs in Poland on a clustered, accessible, responsive map, with details (address, access hours, location description, source) in a popup and a keyboard/screen-reader-friendly list alternative.

## Scope & Non-Goals

- **In Scope:**
  - Leaflet map (`leaflet` + `react-leaflet` + marker clustering) loaded client-side only
  - Popup with key standard-schema fields + sources + link to dane.gov.pl fork dataset
  - Search by city/name, "near me" (geolocation, optional), list view alternative
  - Landing `/` updated with pitch + links (map, schema downloads, API docs)
- **Out of Scope:**
  - Routing/navigation to AED
  - Editing data

## UI Design (Per-Task)

- **Approved:** `—`
- **Route(s):** `/mapa`, `/`
- **Reference Sketch / Assets:** None
- **Layout & Information Hierarchy:** PENDING (`hackathon-ui-design`)
- **Components (Reused vs. New):** PENDING
- **Interactive States:** PENDING (loading / empty / error / success)
- **API Fields & Contracts Consumed:** `GET /api/aed/?bbox=&q=` (GeoJSON), `GET /api/sources/` (counts)
- **WCAG 2.2 AA Checks:** PENDING — contrast, `:focus-visible`, `>= 44px` targets, semantic headings, non-color cues.

## Technical Implementation Plan

- **Backend:** reuse `/api/aed/` from T04 (add fields only via DEC if UI design needs them).
- **Frontend (`frontend/`):** deps `leaflet`, `react-leaflet`, `react-leaflet-cluster` (or `leaflet.markercluster`), `@types/leaflet`; `src/app/mapa/page.tsx` (server, `force-dynamic`), `src/components/map/AedMap.tsx` (client, `dynamic(..., { ssr: false })`), `src/components/map/AedList.tsx`, `src/lib/api.ts` helper `getAeds()`; i18n strings in `src/i18n/messages.ts`.
- After `package.json` change: `docker compose up -V --build`.

## Acceptance Criteria

- [ ] `/mapa` shows clustered markers for all merged AEDs; clicking shows details + source
- [ ] List view + search work by keyboard; WCAG 2.2 AA checks pass
- [ ] Works on mobile width (375 px) and desktop
- [ ] `make build-prod` passes

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `T07`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes
  (required: frontend deps + code)

### Manual Verification
1. Open `http://localhost:3000/mapa` → markers over Poland; zoom into Krosno → individual AEDs
2. Tab through controls; open list view; search "Legionowo" → results
3. Resize to 375 px → usable layout

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** —
