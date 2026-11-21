# 02 — Shared UI System (Global Baseline)

> Lightweight global foundation only. Per-screen layouts, component hierarchies, and interactive states are designed **per task** inside each `docs/tasks/TXX-*.md` via `hackathon-ui-design` immediately before implementing that task.

## Baseline & Constraints

- **Framework:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4 (`@import "tailwindcss";` in `frontend/src/app/globals.css`).
- **Accessibility Baseline:** **WCAG 2.2 AA** with `light` / `dark` / `system` appearance support (`DEC-001`) using CSS `light-dark()` semantic tokens (`--color-canvas`, `--color-surface`, `--color-text`, `--color-border`, `--color-accent`).
- **Localization Baseline:** `pl-PL` (default) and `en-US` via `LocaleProvider` + `useTranslations()` (`DEC-001`), persisted in `localStorage` (`hn26-locale`) with pre-hydration sync.
- **Contrast & Targets:** `>= 4.5:1` normal text contrast, `>= 3:1` borders/controls contrast, visible `:focus-visible` outlines, `>= 44px` (`min-h-11`) interactive targets, non-color status cues (`PASS`/`FAIL` badges or icons + text), and `aria-live="polite"` for live updates.

## App Shell & Navigation

- **Global Layout (`frontend/src/app/layout.tsx`):** `<Header brand/nav, max-width container, footer>`
- **Primary Navigation Items:** Brand "Misja AED · Dane na ratunek"; `Start` (`/`), `Mapa AED` (`/mapa`, Must per DEC-003), `Schemat` (`/schemat`, added by T08); `aria-current="page"` on the active item. `/mapa` renders full-bleed (no `max-w-4xl` main) — T07. The dane.gov.pl fork is the primary portal UI; our Next.js app hosts the map.

## Color & Typography Tokens

- **Page Surface / Card Surface:** `#f8fafc` (`bg-slate-50`) / `#ffffff` (`bg-white`)
- **Primary / Secondary Text:** `#0f172a` (`text-slate-900`) / `#334155` (`text-slate-700`)
- **Primary Action / Focus Accent:** `#1d4ed8` (`bg-blue-700` / `hover:bg-blue-800`)
- **Semantic Statuses:** Success (`emerald-50` / `emerald-700` / `emerald-950`), Warning (`amber-50` / `amber-700` / `amber-950`), Error (`red-50` / `red-700` / `red-950`)
- **Typography Scale:** `<Display / H1 / H2 / Body / Mono notes>`

## Shared UI Primitives

Track reusable components as tasks create or update them:

| Component | Path | Purpose | Introduced In |
| --- | --- | --- | --- |
| `HealthStatusCard` | `frontend/src/components/HealthStatusCard.tsx` | Live API & DB connectivity banner pattern | Starter template |
| `EmergencyBanner` | `frontend/src/components/EmergencyBanner.tsx` | "W nagłym wypadku dzwoń 112" `<aside>` with `tel:112` button, on `/` and `/mapa` | T07 |
| `Badge` | `frontend/src/components/ui/Badge.tsx` | Status pill, `variant: neutral/success/warning/error`, always icon + text (non-colour cue) | T07 |
| Warning tokens | `frontend/src/app/globals.css` | `--color-warning-bg/-border/-text/-badge/-on-badge` for every appearance mode (locked AED, restricted access) | T07 |

| AED map styles | `frontend/src/app/globals.css` (`.aed-map`, `.aed-pin`, `.aed-pin--ranked`, `.aed-cluster`, `.aed-you`) | Leaflet overrides (44 px controls, token colours), AED pin (green `#00703c` + white outline), white ringed clusters, "Jesteś tutaj" marker | T07 |
| `ExternalLink` | `frontend/src/components/aed/AedDetails.tsx` | New-tab link with ↗ icon + sr-only "(otwiera się w nowej karcie)" | T07 |

## Reference Assets (`docs/inputs/ui/`)

- None yet. Campaign logo/brand colors to be added here once produced (REQ-11).
