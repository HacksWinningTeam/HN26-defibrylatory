# `T08` — Schema & source coverage page (/schemat)

- **Status:** `CANCELLED`
- **Layer:** `Frontend`
- **UI Design Required:** `Yes`
- **Depends On:** `T04`
- **Traces To:** `REQ-01`, `REQ-02`, `REQ-05`, `REQ-10`, `DEC-004`

> **Cancelled by DEC-014 (2026-11-22):** functionality moved into the dane.gov.pl fork; the schema and coverage are served by the portal (`/1.4/aed/schema`, `/1.4/aed/sources`, schema XLSX resource). The T07 link bug (`aed-schema.csv` → `aed-template.csv`) is handled in T15.

## Goal & User Outcome

Judges and data owners see the standard schema (field table, descriptions, examples) with download buttons, plus a coverage matrix showing which standard fields each harvested source fills.

## Scope & Non-Goals

- **In Scope:**
  - `/schemat`: field table grouped by section, download buttons (xlsx / csv / JSON Schema / Table Schema)
  - Coverage matrix: sources × field groups with % + text labels (non-color cues)
- **Out of Scope:**
  - Editing the schema in UI

## UI Design (Per-Task)

- **Approved:** `—`
- **Route(s):** `/schemat` (server page, `force-dynamic`; data rendered by client components so labels follow the saved locale). Reached from a new 2-item header nav and from "Skąd są te dane?" on `/`.
- **Reference Sketch / Assets:** None in `docs/inputs/ui/`. Reuses the T07 look (AED pin brand, tokens, Badge).
- **Audience & job:** judges (schema = 10 % of the score) and municipal data owners: *what fields, which are required, how do I publish, and how well do today's sources match?*

### Layout & Information Hierarchy

**Header (AppShell, all pages):** brand "Misja AED · Dane na ratunek" + `<nav aria-label="Główna">` with 2 links: **Najbliższy AED** (`/`) · **Schemat danych** (`/schemat`), `aria-current="page"` + underline/bold on the active one (non-colour cue); language + appearance selectors as today.

**Desktop (≥ 1024 px), single column `max-w-7xl`:**
```text
h1 Wzorcowy zakres danych o defibrylatorach AED
   [v1.0.0] [CC BY 4.0]  "Jednolity zakres danych ... Jeden wiersz = jedno urządzenie AED."
+-- Pobierz -----------------------------------------------------------------------+
| [⬇ Specyfikacja XLSX] [⬇ Szablon CSV do wypełnienia] [{ } JSON Schema] [Table Schema]|  min-h-11 buttons
+----------------------------------------------------------------------------------+
Summary line: 42 pola · ★ 8 wymaganych · ◆ 13 zalecanych · ○ 21 opcjonalnych · 6 grup
Na tej stronie: Identyfikacja · Lokalizacja · Dostępność · Urządzenie · Dysponent · Metadane · Pokrycie w źródłach · Jak opublikować
                                                                           (in-page anchor nav)
h2 Identyfikacja (2 pola)                                       <- one section per group
| Pole            | Nazwa i opis                                 | Typ      | Wymagalność  | Przykład          |
| `id_aed`        | Identyfikator AED                            | tekst    | ★ wymagane   | LEGIONOWO-AED-001 |
|                 | Unikalny i niezmienny identyfikator ...      | maks. 64 |              |                   |
|                 | OSM: ref                                     | wzorzec  |              |                   |
| `dostep`        | ... ▸ Dozwolone wartości (4)  (<details>: publiczny – ..., ograniczony – ...) |
h2 Lokalizacja (16 pól) ... (same table)
...
h2 Pokrycie wzorcowego zakresu w źródłach
   "Jaka część rekordów każdego źródła ma wypełnione pole (po mapowaniu na wzorzec)."
   Legend: ● wysokie ≥ 80 %  ◐ średnie 40–79 %  ○ niskie 1–39 %  – brak (0 %)
 a) Source summary table:
| Źródło (link ↗)                | Typ          | Rekordy (poprawne/wszystkie) | Wymagane | Zalecane | Ogółem | Potwierdzone w innych źródłach | Uwagi jakości |
| Lokalizacja defibrylatorów ... | dane.gov.pl  | 708 / 708                    | ● 100 %  | ◐ 51 %   | ○ 38 % | 267                            | godziny tekstem: 606; powtórzone współrzędne: 81 |
| OpenStreetMap – ...            | OpenStreetMap| 18 303 / 18 303              | ● 87 %   | ○ 21 %   | ○ 26 % | 315                            | brak miejscowości: 18 227 ... |
   each % cell = symbol + number + thin decorative bar (aria-hidden)
 b) Field × source matrix (<details open> "Pokrycie pole po polu"): rows = 42 fields grouped by
    <th scope="rowgroup"> group, first column field name + obligation symbol (sticky), columns = 6 sources
    (short names: Marki, Krosno, Warszawa, Przemyśl, Legionowo, OSM — full title in <abbr title> + sr-only);
    cells "● 100 %" / "◐ 55 %" / "○ 12 %" / "–".
h2 Jak opublikować dane AED zgodnie ze wzorcem
  <ol> 1. Pobierz szablon CSV (link)  2. Wypełnij co najmniej pola ★ wymagane (współrzędne WGS84, ...)
       3. Opublikuj na dane.gov.pl jako zasób CSV z tagiem „AED” – harvester Misji AED dołączy go do zbioru ogólnopolskiego
          automatycznie (link: zbiór w dane.gov.pl / API /api/1.4/datasets/1).
```

**Mobile (375 px):** same order, single column. Download buttons stack full width. Field tables and both coverage tables sit in a horizontally scrollable `role="region"` (`tabIndex=0`, `aria-label="Tabela: {group}"`) with the first column sticky — allowed for 2-D data tables under WCAG 1.4.10; the page itself never scrolls horizontally. Long descriptions wrap.

### Components (Reused vs. New)

- **Reused:** `AppShell` (+ new 2-item nav), `Badge` (obligation badges, see below), `ExternalLink` (moved from `components/aed/AedDetails.tsx` to `components/ui/ExternalLink.tsx`), DEC-001 tokens, `useTranslations()`, `getApiBaseUrl()`.
- **New (`frontend/src/components/schema/`):**
  - `SchemaHeader.tsx` (client): title, version/licence badges, description, download buttons, summary counts, in-page nav.
  - `SchemaFieldTable.tsx` (client): one `<table>` per group with `<caption>` (sr-only), `<th scope="col">`, field name `<code>`, allowed values in `<details>`, PL/EN description by locale (`description` / `description_en`).
  - `CoverageSummary.tsx` (client): source summary table.
  - `CoverageMatrix.tsx` (client): field × source matrix.
  - `PublishGuide.tsx` (client): 3-step `<ol>`.
  - `CoverageCell` (inside `CoverageSummary.tsx`, shared by both tables): symbol + percent text + decorative bar.
- **Obligation badges:** `★ wymagane` (`warning` variant — strong but not "error"), `◆ zalecane` (`neutral`, bold), `○ opcjonalne` (`neutral`) — always symbol + text.
- **Pure logic `frontend/src/lib/schema.ts` + `schema.test.mjs`:** `groupFields(fields, groups)`, `obligationCounts(fields)`, `coverageLevel(ratio) -> "high"|"medium"|"low"|"none"` (≥ 0.8 / ≥ 0.4 / > 0 / 0), `formatPercent(ratio, locale)`, `shortSourceName(source)` (Marki/Krosno/Warszawa/Przemyśl/Legionowo/OSM from publisher, fallback title), `qualityFlagLabel(code)` keys.
- **Page:** `frontend/src/app/schemat/page.tsx` (server, `force-dynamic`: fetch schema + sources in parallel, pass to client components); `frontend/src/app/schemat/loading.tsx` (skeleton).
- **API helpers in `src/lib/api.ts`:** `fetchSchemaStandard()`, extend `fetchSources()` (T07) with a variant keeping `coverage`, `publisher`, `valid_count`, `confirmed_by_other_sources`, `quality_flags`.

### Interactive States

- **Loading:** `loading.tsx` skeleton (`role="status"`, "Wczytywanie schematu…") — server render is normally < 200 ms.
- **Success:** static content; `<details>` toggles are native (no live region needed).
- **Empty:** no sources harvested → coverage section shows "Brak zebranych źródeł – uruchom harvest (`harvest_aed`)." (schema part still renders).
- **Error:** schema fetch fails → `role="alert"` "Nie udało się wczytać schematu." + link **Spróbuj ponownie** (`/schemat`, min-h-11) + direct download links still shown (static URLs). Sources fetch fails → coverage section alert "Statystyki źródeł są chwilowo niedostępne." with the same retry link.
- **Hover/focus:** links/buttons/`summary` get the global 2 px `--color-focus` outline; scroll regions focusable and outlined.

### API Fields & Contracts Consumed (server-side via `getApiBaseUrl()`; downloads same-origin)

- **`GET /api/schema-standard/`** (T01): `name`, `version`, `title`, `title_en`, `description`, `license`, `groups[] {code, label}`, `fields[] {name, group, type, obligation ("wymagane"|"zalecane"|"opcjonalne"), required, label, description, description_en, example, allowed_values[] {value, label}, pattern, minimum, maximum, max_length, osm_tag}`.
- **`GET /api/sources/`** (T03): `aed_count`, `record_count`, `multi_source_aed_count`, `updated_at`, `schema_version`, `sources[] {id, title, publisher, kind, url, license_name, status, record_count, valid_count, confirmed_by_other_sources, quality_flags {code: count}, coverage {records, required, recommended, overall, fields {field_name: ratio 0..1}}}`.
- **Downloads (same-origin `<a href download>`):** `/api/schema-standard/aed-schema.xlsx`, `/api/schema-standard/aed-template.csv`, `/api/schema-standard/aed-schema.json`, `/api/schema-standard/table-schema.json`.
- **No backend changes.** Bug found while designing: T07's "Skąd są te dane?" links `/api/schema-standard/aed-schema.csv` (404) — fixed in T08 to `aed-template.csv`, plus a link to `/schemat`.

### WCAG 2.2 AA Checks

- **Contrast:** only DEC-001 tokens (all appearance modes incl. high contrast); obligation/coverage symbols use text colour; decorative bars use `--color-success-badge` / `--color-warning-badge` / `--color-border` on `--color-surface-raised` (≥ 3:1 as non-text, and never the only cue).
- **Non-colour cues:** obligation = symbol + word; coverage = symbol (●◐○–) + percentage text; active nav = `aria-current` + bold underline.
- **Tables:** real `<table>` with `<caption>`, `scope="col"`/`scope="row"`/`scope="rowgroup"`; abbreviated source column headers carry the full title (`<abbr title>` + sr-only text); numbers right-aligned with `tabular-nums`.
- **Targets / focus:** download buttons, nav links, retry, `summary` ≥ 44 px (`min-h-11`); visible `:focus-visible`; scroll regions `tabIndex=0` with accessible names; fixed AccessibilityMenu does not cover content (bottom padding).
- **Structure:** h1 page → h2 per group / coverage / guide → h3 inside coverage ("Podsumowanie źródeł", "Pokrycie pole po polu"); in-page nav `<nav aria-label="Na tej stronie">`; `lang` follows locale; EN descriptions from `description_en`.
- **Reflow / text scale:** usable at 320 px and 200 % text (only data tables scroll, inside their regions); `prefers-reduced-motion` respected (no animation added).

## Technical Implementation Plan

- **Frontend (`frontend/`):** `src/app/schemat/{page,loading}.tsx`, `src/components/schema/{SchemaHeader,SchemaFieldTable,CoverageSummary,CoverageMatrix,PublishGuide}.tsx`, `src/lib/schema.ts` + `schema.test.mjs` (added to `npm test`), `src/lib/api.ts` helpers, header nav in `AppShell`, `ExternalLink` moved to `components/ui/`, fix T07 CSV link + add `/schemat` link in `DataInfo`. No backend changes.

## Acceptance Criteria

- [ ] Schema table matches `/api/schema-standard/`
- [ ] Downloads work through the same-origin proxy
- [ ] Coverage matrix readable without color

## Verification Checklist

### Automated Checks
- [ ] `make test` passes (including new/updated unit & API tests for `T08`)
- [ ] `make lint` passes (`ruff check .`, `npm run typecheck`, `npm run lint`)
- [ ] `make schema-check` passes (`python manage.py spectacular --validate --fail-on-warn`)
- [ ] `make migrations-check` passes; migrations applied cleanly (`make migrate`) if models changed
- [ ] `make build-prod` passes
  (required: frontend code)

### Manual Verification
1. Open `http://localhost:3000/schemat` → fields + downloads; click xlsx → file downloads
2. Coverage shows e.g. Legionowo high on address fields, OSM high on access hours

### Sign-Off
- **Verified By:** `—`
- **Notes / Follow-Ups:** First task to cut if time runs out (schema files are still delivered via T01).
