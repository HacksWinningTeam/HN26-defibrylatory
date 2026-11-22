# `T21` — Map-first public page

- **Status:** `VERIFIED`
- **Layer:** `Frontend`
- **UI Design Required:** `Yes`
- **Depends On:** `T15`
- **Traces To:** `REQ-13`, `DEC-021`

## Goal & User Outcome

Opening http://2.29.205.102:3002/ shows almost only a big map: the nearest AED is highlighted with a compact card on top of the map, and every other AED pin can be clicked to see its details and navigate to it.

## Scope & Non-Goals

- **In Scope:** layout of "/" and the app shell (header slimmed, footer removed), reuse of the existing map/popup/nearest logic
- **Out of Scope:** API/data changes, geolocation changes, new filters/search, dark mode

## UI Design (Per-Task)

- **Approved:** 2026-11-22 06:45 (user: "approve")
- **Route(s):** `/` (`/mapa` keeps redirecting to `/`)
- **Reference Sketch / Assets:** current page (`docs/demo/screenshots/T15-map-from-portal.png`); AEDane banner colours (`docs/inputs/ui/baner.png`) only as inspiration, existing tokens stay
- **Layout & Information Hierarchy:**
  ```text
  Desktop (≥ 1024 px)
  +----------------------------------------------------------------------+
  | [♥] Misja AED                                   [Zadzwoń 112] [PL ▾] |  slim header ~56 px
  +----------------------------------------------------------------------+
  |                                                                      |
  |  +-------------------------------+        MAP: full width,           |
  |  | NAJBLIŻSZY AED                |        height = 100dvh − header   |
  |  | 3,0 km · ok. 38 min pieszo    |                                  |
  |  | AED – na korytarzu …          |   (●) Jesteś tutaj               |
  |  | [⚠ Dostęp ograniczony]        |        ①  nearest AED (big red)  |
  |  | [➜ PROWADŹ DO AED]  [📞 112]  |        clustered pins = all AEDs |
  |  | z: BCTW Bydgoszcz (demo)      |        click pin → popup:        |
  |  +-------------------------------+        name, address, hours,     |
  |   floating card, top-left, 24rem          access, source, Prowadź   |
  |                                      [+/−]              © OSM · dane.gov.pl |
  +----------------------------------------------------------------------+

  Mobile (< 640 px)
  +------------------------------+
  | [♥] Misja AED   [112] [PL]   |
  +------------------------------+
  |            MAP               |
  |    (●)      ①                |
  +------------------------------+
  | NAJBLIŻSZY AED · 3,0 km      |  bottom sheet (card), map stays ≥ 55dvh
  | AED – na korytarzu …         |
  | [➜ PROWADŹ]      [📞 112]    |
  +------------------------------+
  ```
- **Removed:** emergency banner block (its 112 call becomes a header button + card button), "Jesteś tutaj" box (shown as the map marker + one muted line in the card), list of AEDs 2–5 and ranked pins 2–5 (all non-nearest AEDs are regular clickable pins), "Dane"/API section, footer links, appearance (theme) selector in the header. Kept: language selector, floating accessibility button, skip link, map attribution (+ "Dane: dane.gov.pl" link to the common dataset in the attribution).
- **Components (Reused vs. New):**
  - Reused: `AedMap` (pins, clustering, popups, keyboard support), `NearestCard` content (distance, walking time, access badge, "Prowadź do AED"), `EmergencyBanner` 112 link styling, `LanguageSelector`, `AccessibilityMenu`
  - New: `MapFirstView` (`components/aed/MapFirstView.tsx`, replaces `AedFinder` on "/": map container + overlay card); `NearestCard` gets a `compact` variant (no "Pokaż na mapie"/"Więcej informacji"; card click centres the map on the nearest AED)
- **Interactive States:**
  - **Loading:** map tiles + "you are here" visible; card shows skeleton lines + "Szukam najbliższych defibrylatorów…" (`role="status"`, `aria-busy`)
  - **Empty:** card: "Zbiór AED nie został jeszcze wczytany." + 112 button stays
  - **Error:** card: "Nie udało się wczytać defibrylatorów." + "Spróbuj ponownie" button (`role="alert"`); 112 button stays
  - **Success:** card filled; `aria-live="polite"` announcement "Najbliższy AED: 3,0 km, …"; clicking any pin opens its popup with focus on the popup heading (existing behaviour)
- **API Fields & Contracts Consumed:** unchanged — `fetchAeds()` (portal `/1.4/aed/devices` GeoJSON via the same-origin proxy): `id`, `geometry.coordinates`, `properties.nazwa/opis_lokalizacji/miejscowosc/nazwa_ulicy/nr_budynku/dostep/godziny_dostepnosci/zrodlo…`
- **WCAG 2.2 AA Checks:** card on solid surface over the map (text ≥ 4.5:1, border ≥ 3:1), buttons `min-h-11`, `:focus-visible` rings kept, skip link "Pomiń mapę" → card, card is an `<aside aria-labelledby>` with an `h1` "Najbliższy AED", 112 is a real `tel:` link, access shown as text badge (not colour only), card never covers the zoom control or attribution, `prefers-reduced-motion` respected for pan/zoom.

## Technical Implementation Plan

- **Frontend (`frontend/`):** `src/app/page.tsx` (render `MapFirstView`, drop `DataInfo`), `src/components/aed/MapFirstView.tsx`, `NearestCard.tsx` (`compact`), `AedMap.tsx` (only the nearest gets a ranked pin), `AppShell.tsx` (slim header with 112, no footer on "/"), i18n strings PL/EN
- **Config / Env:** none

## Acceptance Criteria

- [x] "/" shows a full-height map with the nearest AED highlighted and the floating/bottom card (`docs/demo/screenshots/T21-map-first-{desktop,mobile}.png`)
- [x] Every AED pin is clickable (popup with details + navigation) (`T21-map-first-popup.png`)
- [x] Removed elements are gone; 112 always reachable in one tap (header + card)
- [x] `npm run typecheck`, `npm run lint`, `make build-prod` pass

## Verification Checklist

### Automated Checks
- [x] `npm run typecheck` / `npm run lint` / frontend unit tests (20 pass) — in the `frontend` container
- [x] `make build-prod`

### Manual Verification
1. http://localhost:3000/ — desktop and 390 px wide: map, card, 112, click 3 different pins
2. Keyboard only: skip link, card buttons, pins, popup

### Sign-Off
- **Verified By:** user (manual check approved) — 2026-11-22 06:55
- **Notes / Follow-Ups:** Removed dead components `AedFinder`, `NearbyList`, `DataInfo`, `EmergencyBanner`; theme selector left the header (display modes remain in the accessibility menu). On phones the header wraps to two rows. The public map on :3002 changes only after you push `main` (CI deploy).
