# `T07` — AED map in Next.js (/mapa)

- **Status:** `VERIFIED`
- **Layer:** `Full-Stack`
- **UI Design Required:** `Yes`
- **Depends On:** `T04`
- **Traces To:** `REQ-13`, `REQ-10`, `DEC-003`, `DEC-004`, `DEC-008`, `DEC-010`

## Goal & User Outcome

Anyone opens `/mapa` in our Next.js app and sees all merged AEDs in Poland on a clustered, accessible, responsive map, with details (address, access hours, location description, source) in a popup and a keyboard/screen-reader-friendly list alternative.

## Scope & Non-Goals

- **In Scope:**
  - Leaflet map (`leaflet` + `react-leaflet` + marker clustering) loaded client-side only
  - Popup with key standard-schema fields + sources + link to dane.gov.pl fork dataset
  - Search by city/name, "near me" (geolocation, optional), list view alternative
  - Landing `/` updated with pitch + links (map, schema downloads, API docs)
- **Out of Scope:**
  - In-app routing/navigation to AED (only an external OSM directions / `geo:` link)
  - Editing data

## UI Design (Per-Task)

- **Approved:** 2026-11-21 21:09 (user, design v2)
- **Revision:** v2 (DEC-010, 2026-11-21 20:41) — user asked for a **very simple, highly visible UI** with the **current location hardcoded to Bydgoskie Centrum Targowo-Wystawiennicze** (hackathon venue). Supersedes v1 (search, filters, geolocation, map/list toggle removed).
- **Route(s):** `/` — single page "Najbliższy AED" (map + nearest AEDs + data info). `/mapa` redirects to `/` (kept for links in docs/slides).
- **Reference Sketch / Assets:** None in `docs/inputs/ui/` (branding by another team member, REQ-11). Marker uses the ILCOR/ISO 7010 AED convention (white heart + lightning on green) as inline SVG.
- **Demo location (clearly labelled, never silent):** `DEMO_LOCATION = { lat: 53.170719, lon: 18.047651, label: "Bydgoskie Centrum Targowo-Wystawiennicze, Bydgoszcz" }` (OSM/Nominatim), shown as "📍 Jesteś tutaj: … (lokalizacja demonstracyjna)". Optional URL override `/?lat=..&lon=..&miejsce=..` for demos elsewhere (invalid values → fall back to the demo location).
- **Design principles:** one job — *where is the nearest AED and how do I get there*; huge readable numbers and buttons; max 3 badges per AED; everything visible without scrolling on a phone for the #1 AED; honest data (distance labelled "w linii prostej", missing values hidden, unknown shown as "brak informacji"); reuse DEC-001 tokens/i18n/AccessibilityMenu.

### Layout & Information Hierarchy

**Mobile (375 px) — single column, top to bottom:**
```text
+-----------------------------------+
| Misja AED          [PL▾] [Wygląd▾]|  header (simplified, no nav)
+-----------------------------------+
| ☎ NAGŁE ZATRZYMANIE KRĄŻENIA?     |  EmergencyBanner: red, bold, 1.25rem
|   [  ZADZWOŃ 112  ] (full width)  |  tel:112, min-h 56px
+-----------------------------------+
| 📍 Jesteś tutaj: Bydgoskie Centrum |
|  Targowo-Wystawiennicze, Bydgoszcz|
|  (lokalizacja demonstracyjna)     |
+-----------------------------------+
| h1 NAJBLIŻSZY AED                 |
| ┌───────────────────────────────┐ |
| │ 180 m                         │ |  distance: 3rem bold
| │ ok. 2 min pieszo · w linii prostej│  1rem muted
| │ h2 Hala A – przy recepcji     │ |  nazwa / opis_lokalizacji 1.25rem
| │ ul. Gdańska 187, Bydgoszcz    │ |
| │ [✔ Publiczny][🕑 24/7]         │ |  ≤ 3 badges, icon + text
| │ [🔒 Zamknięty na klucz]        │ |
| │ [   ➜  PROWADŹ DO AED   ]     │ |  primary, full width, min-h 56px
| │ Więcej informacji ▾            │ |  <details>: hours, floor, operator,
| └───────────────────────────────┘ |   phone, sources, update date
| h2 Inne w pobliżu                 |
|  2  420 m · Urząd …  [Prowadź]    |  compact rows (numbers = map labels)
|  3  610 m · Szkoła … [Prowadź]    |
|  4  …   5  …                      |
+-----------------------------------+
| Map h-[60dvh]: "Ty" marker +      |
| numbered markers 1–5 (big),       |
| other AEDs clustered              |
+-----------------------------------+
| h2 Skąd są te dane?               |  DataInfo: counts, sources table,
|  19 006 AED · 6 źródeł · 2026-11-21|  links: schema xlsx/csv/JSON Schema,
|  [Schemat danych] [Pobierz zbiór] |  exports csv/geojson/xlsx, API docs,
|  [API] [Zbiór w dane.gov.pl]      |  fork dataset (DANEGOV_FORK_URL)
+-----------------------------------+
```

**Desktop (≥ 1024 px):** emergency banner full width on top; below, two columns — left `w-[28rem]` scrollable: "Jesteś tutaj", NAJBLIŻSZY AED card, "Inne w pobliżu"; right: map filling the viewport height (min 520 px). "Skąd są te dane?" section below both columns.

**Map behaviour:** initial view fits the demo location + 5 nearest AEDs (max zoom 17); "Ty" marker (blue dot + label "Jesteś tutaj"); markers 1–5 are 48 px numbered AED pins; all other AEDs (~19k) in clusters. Clicking any marker opens a popup with the same compact details + "Prowadź" button; clicking a row "N" in the list highlights pin N and opens its popup.

**AED details content (card "Więcej informacji" and popups):** Gdzie dokładnie (`opis_lokalizacji`, `pietro`, w budynku/na zewnątrz) · Godziny (`godziny_dostepnosci`) · Zabezpieczenie · Status · Dysponent + tel (tel: link) · Źródła (links) · Aktualizacja. Rows with null hidden.

**"Prowadź" link:** `https://www.openstreetmap.org/directions?engine=fossgis_osrm_foot&route={from_lat}%2C{from_lon}%3B{lat}%2C{lon}` (walking route from the demo location), new tab.

### Components (Reused vs. New)

- **Reused:** `AppShell` (simplified: brand "Misja AED · Dane na ratunek", no primary nav, full-bleed `main` on `/`, footer OSM attribution + accessibility settings link), `AccessibilityMenu`, `LanguageSelector`, `AppearanceSelector`, `useTranslations()` + `messages.ts`, DEC-001 tokens, `getApiBaseUrl()`. `HomeView`/`HealthStatusCard` no longer rendered (files kept).
- **New shared primitives (in `docs/02-ui-system.md`):** `EmergencyBanner.tsx` (`<aside aria-label="Numer alarmowy">`, `tel:112` big button), `ui/Badge.tsx` (`neutral | success | warning | error`, icon + text required), warning tokens `--color-warning-*` in `globals.css`.
- **New feature components (`frontend/src/components/aed/`):** `AedFinder.tsx` (client; fetches `/api/aed/` once, computes 5 nearest to the location, owns `selectedId`), `NearestCard.tsx` (#1 big card), `NearbyList.tsx` (#2–#5 rows), `AedDetails.tsx` (presentational), `AedMap.tsx` (client-only via `dynamic(..., { ssr: false })`, Leaflet + `leaflet.markercluster`), `DataInfo.tsx` (server; counts + links from `/api/sources/`).
- **Pure logic `frontend/src/lib/aed.ts` + `aed.test.mjs`:** `DEMO_LOCATION`, `parseLocationParams()`, `haversineMeters()`, `nearestAeds(features, from, n)`, `formatDistance()` (`180 m` / `1,2 km`), `walkingMinutes()` (80 m/min, min 1), `is247()`, `topBadges(props)` (max 3, priority: lock/code → access → 24/7 → status niesprawny), `osmDirectionsUrl(from, to)`.
- **Pages:** `frontend/src/app/page.tsx` (server, `force-dynamic`: EmergencyBanner + AedFinder + DataInfo), `frontend/src/app/mapa/page.tsx` (`redirect("/")`).

### Interactive States

- **Loading:** NAJBLIŻSZY AED card shows skeleton + `role="status"` "Szukam najbliższych defibrylatorów…"; map shows tiles + "Ty" marker immediately.
- **Success:** card filled; live region (`aria-live="polite"`) announces "Najbliższy AED: {distance}, {nazwa}". Focus is not moved automatically.
- **Empty (no data in DB):** card replaced by "Zbiór AED nie został jeszcze załadowany." (no fake data); map still shows the location.
- **Far away:** if the nearest AED is > 2 km, the card adds a warning badge "Daleko – dzwoń 112, dyspozytor wskaże najbliższy AED".
- **Error:** `role="alert"` "Nie udało się wczytać defibrylatorów." + [Spróbuj ponownie]; emergency banner always visible.
- **Hover/focus:** 3 px `--color-focus` outline; selected row/pin shows "Wybrany" text + thicker border (non-colour cue).

### API Fields & Contracts Consumed (same-origin `/api/...` via `src/proxy.ts`)

- **`GET /api/aed/`** (T04, contract fixed by this design → DEC-008). Called once from the browser without params; the client computes the 5 nearest AEDs to the (demo) location in memory (no refetch on pan/zoom). `?q=` and `?bbox=minLon,minLat,maxLon,maxLat` stay supported server-side for API users/tests but are unused by the MVP UI. Response `200 application/geo+json` (Django `GZipMiddleware` enabled; ~20k features ≈ 6–8 MB raw, ≈ 1 MB gzipped):
  ```json
  {
    "type": "FeatureCollection",
    "meta": { "count": 12345, "generated_at": "2026-11-21T20:00:00Z", "license": "CC BY 4.0 / ODbL (OSM)" },
    "features": [{
      "type": "Feature",
      "id": "PL-AED-000123",
      "geometry": { "type": "Point", "coordinates": [21.7657, 49.6887] },
      "properties": {
        "id_aed": "PL-AED-000123",
        "nazwa": "Urząd Miasta Krosno",
        "adres": "ul. Lwowska 28, 38-400 Krosno",
        "miejscowosc": "Krosno",
        "opis_lokalizacji": "hol główny, przy portierni",
        "w_budynku": true,
        "pietro": 0,
        "dostep": "publiczny",
        "godziny_dostepnosci": "24/7",
        "zabezpieczenie": "zamkniety_na_klucz",
        "status": "nieznany",
        "dysponent": "Urząd Miasta Krosna",
        "telefon_kontaktowy": "+48 13 474 33 00",
        "data_aktualizacji": "2025-03-01",
        "zrodla": [
          { "nazwa": "Krosno – lokalizacje AED", "typ": "dane_gov_pl", "url": "https://dane.gov.pl/pl/dataset/3624" },
          { "nazwa": "OpenStreetMap", "typ": "osm", "url": "https://www.openstreetmap.org/node/123" }
        ]
      }
    }]
  }
  ```
  Rules: all standard-schema fields use their `schema.py` names and enum codes (`dostep`, `zabezpieczenie`, `status` codes translated client-side via `messages.ts`); empty values are `null` (never `""`); `adres` is a server-built display string (`cecha_ulicy nazwa_ulicy nr_budynku[/nr_lokalu], kod_pocztowy miejscowosc`, `null` if no street data); `zrodla` comes from the AED's `SourceRecord` provenance (`typ` = `SourceDataset.kind`, `url` = dataset page on dane.gov.pl or OSM element URL); `w_budynku` boolean or `null`.
- **`GET /api/sources/`** (T03, server-side from `/` `DataInfo` only). Fields consumed: top-level `aed_count` (merged AEDs), `updated_at` (last harvest/merge, ISO), and `sources[]` items `{ id, title, kind ("dane_gov_pl" | "osm"), url, record_count }`. Extra fields (coverage) are ignored here and used by T08.
- **Static links in `DataInfo`:** `/api/schema-standard/aed-schema.xlsx`, `.csv`, `.json`; `/api/exports/aed.csv`, `.geojson`, `.xlsx`; `/api/docs/`; optional fork dataset URL from server env `DANEGOV_FORK_URL` (link hidden when empty; mirror in `.env.example`, `compose.yaml`, `compose.prod.yaml`).
- **External:** OSM tiles `https://tile.openstreetmap.org/{z}/{x}/{y}.png` with attribution "© OpenStreetMap contributors"; OSM walking-directions link (from demo location).

### Backend Changes Required by This Design (implemented in T04/T03, verified in T07)

- `/api/aed/` property list above (incl. `adres`, `zrodla`, `meta`) + tests asserting the exact property keys and `null` for empty values; add `django.middleware.gzip.GZipMiddleware` (after `SecurityMiddleware`) to `backend/config/settings.py`.
- `/api/sources/` exposes `aed_count`, `updated_at`, `sources[].{id,title,kind,url,record_count}`.
- If T04 is already `VERIFIED` when T07 starts, these are added in T07 with tests.

### WCAG 2.2 AA Checks

- **Appearance:** only DEC-001 semantic tokens (works in light, dark, system, hc-black-white, hc-black-yellow, grayscale); no new theme switch. New warning tokens meet ≥ 4.5:1 text / ≥ 3:1 border in each mode. OSM tiles are not recoloured; overlays sit on solid `--color-surface`.
- **Contrast:** text ≥ 4.5:1 (badges use `*-badge`/`*-on-badge` pairs); marker (green `#00703c` + 2 px white outline) and cluster icons ≥ 3:1 against tiles; Leaflet zoom/attribution controls restyled with `--color-surface`/`--color-text`/`--color-border`.
- **Targets (2.5.8):** primary buttons (112, Prowadź) ≥ 56 px high; all other links/buttons, Leaflet zoom buttons (overridden from 30 px), markers and cluster icons ≥ 44×44 px (`min-h-11`).
- **Focus:** visible `:focus-visible` 2 px `--color-focus` outline on everything incl. Leaflet controls/popup close; focus moved to popup heading on "Pokaż na mapie" and restored on close; focus not obscured by the fixed AccessibilityMenu (list panel gets bottom padding ≥ 5rem) (2.4.11).
- **Keyboard:** full task completable without the map — nearest card, nearby list, details, Prowadź links. Map: Leaflet keyboard pan/zoom (`keyboard: true`), markers/clusters focusable and Enter-activated, `Esc` closes popup. "Pomiń mapę / przejdź do listy" skip link before the map; no keyboard trap.
- **Semantics:** landmarks (`header`, `nav aria-label`, `main`, `aside` emergency, `footer`); headings h1 page → h2 "Lista AED"/"Mapa" (visually hidden for map) → h3 per AED; map wrapper `role="region" aria-label="Mapa defibrylatorów"`; search in `<form role="search">` with visible `<label>`; checkboxes with visible labels; toggle buttons with `aria-pressed`; results `<ol>`; details via `<details>/<summary>`; key/values via `<dl>`; external links announce "(otwiera się w nowej karcie)" (sr-only) + ↗ icon.
- **Live regions:** nearest-AED announcement `aria-live="polite"`; fetch error `role="alert"`; loading `role="status"` + `aria-busy`.
- **Non-colour cues:** access, 24/7, lock/code, status, selected card all icon + text; distance as text.
- **Reflow / text scale:** usable at 320 px and at 200% text scale (list panel width in `rem`, toolbar wraps, no horizontal scroll); `prefers-reduced-motion` → `setView` instead of `flyTo`.
- **Language:** `lang` follows locale; all UI strings (incl. enum labels, aria-labels, Leaflet control titles) translated pl-PL/en-US.

## Technical Implementation Plan

- **Backend:** reuse `/api/aed/` from T04 with the property contract from the UI design (DEC-008); `/api/sources/` counts (T03); `GZipMiddleware`. Add any missing fields + tests here if T04/T03 are already `VERIFIED`.
- **Frontend (`frontend/`):** deps `leaflet`, `react-leaflet`, `react-leaflet-cluster` (or `leaflet.markercluster`), `@types/leaflet`; `src/app/page.tsx` (server, `force-dynamic`), `src/app/mapa/page.tsx` (redirect), `src/components/aed/{AedFinder,NearestCard,NearbyList,AedDetails,AedMap,DataInfo}.tsx` (map client-only via `dynamic(..., { ssr: false })`), `src/components/EmergencyBanner.tsx`, `src/components/ui/Badge.tsx`, `src/lib/aed.ts` (+ `aed.test.mjs`, added to `npm test`), `src/lib/api.ts` helpers `fetchAeds()` / `fetchSources()`; i18n strings in `src/i18n/messages.ts`; warning tokens + Leaflet overrides in `globals.css`; optional server env `DANEGOV_FORK_URL` (mirror in `.env.example`, `compose.yaml`, `compose.prod.yaml`).
- After `package.json` change: `docker compose up -V --build`.

## Acceptance Criteria

> Criteria below were written for design v1; design v2 (DEC-010) replaced search/list view with the nearest card + "Inne w pobliżu" list, and `/mapa` redirects to `/`.

- [x] `/` shows clustered markers for all merged AEDs (18,769); clicking a marker shows details + source
- [x] Nearest card + nearby list fully usable by keyboard (Prowadź, Pokaż na mapie → popup heading focused, Esc closes, focus restored); automated WCAG spot checks pass (targets ≥ 44 px, no horizontal scroll at 375 px, live region, labelled controls)
- [x] Works on mobile width (375 px) and desktop (1440 px) — screenshots in `docs/demo/screenshots/T07-*.png`
- [x] `make build-prod` passes

## Verification Checklist

### Automated Checks
- [x] `make test` passes — 83 backend tests (API contract of `/api/aed/` + `/api/sources/` already covered in T03/T04); frontend `npm test` 18 passed incl. 9 new `src/lib/aed.test.mjs` (location params, haversine, nearest, distance/walk format, 24/7, badges, OSM directions, title)
- [x] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [x] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [x] `make migrations-check` passes — no model changes
- [x] `make build-prod` passes (new deps `leaflet` 1.9.4, `leaflet.markercluster` 1.5.3, `@types/*`)

### Observed Results (2026-11-21 23:14, headless Chrome against `make up-d`)
- `/` → h1 "Najbliższy AED"; nearest AED **3,0 km** from BCTW ("AED – na korytarzu, blisko wyjścia", Dostęp ograniczony) so the "Daleko – dzwoń 112" warning shows (real data: no AED within 2 km of the venue in the merged set); #2–#5 at 3,5–4,2 km; live region "Najbliższy AED: 3,0 km, …"; map fits venue + 5 pins, ~29 clusters in view.
- "Pokaż na mapie" on #2 → `aria-pressed=true`, pin 2 highlighted, popup "2. AED – portiernia" opens and its heading gets focus; close button labelled "Zamknij".
- 375 px: no horizontal scroll; all interactive targets ≥ 44 px (Leaflet zoom 44 px). `/mapa` → 307 to `/`; `/?lat=52.2297&lon=21.0122&miejsce=Warszawa` → "Jesteś tutaj: Warszawa" (no demo label).
- Implementation notes: plain Leaflet + `leaflet.markercluster` in a client-only component (no `react-leaflet`); clusters are white discs with a green ring so they cannot be confused with the solid numbered pins 1–5; badge priority puts "Może być niesprawny" first (safety) before lock/code → access → 24/7; `DANEGOV_FORK_URL` mirrored in `.env.example`, `compose.yaml`, `compose.prod.yaml` (link hidden when empty).

### Manual Verification
1. Open `http://localhost:3000/` → red 112 banner, "Jesteś tutaj: Bydgoskie Centrum Targowo-Wystawiennicze … (lokalizacja demonstracyjna)", NAJBLIŻSZY AED card with distance, badges, **PROWADŹ DO AED** (opens OSM walking route in a new tab)
2. Map: "Jesteś tutaj" marker + numbered pins 1–5 + clusters; zoom out to see all of Poland, click a cluster → zooms in, click a single AED → popup with details + source link
3. Keyboard only: Tab through the card and "Inne w pobliżu" → "Pokaż na mapie" on #3 → popup opens with focus on its heading; `Esc` closes it and focus returns to the button
4. "Więcej informacji" expands details (hours, access, operator, sources, update date); switch language to English → all labels translated; try appearance "Wysoki kontrast"
5. Resize to 375 px → single column, no horizontal scroll; `http://localhost:3000/mapa` redirects to `/`
6. Optional: set `DANEGOV_FORK_URL=https://mcod.local/pl/dataset/4211,defibrylatory-aed-zbior-ogolnopolski` in `.env`, `docker compose up -d frontend` → "Zbiór w dane.gov.pl (fork)" link appears in "Skąd są te dane?"

### Sign-Off
- **Verified By:** User (marcin) on 2026-11-21 23:43
- **Notes / Follow-Ups:** —
