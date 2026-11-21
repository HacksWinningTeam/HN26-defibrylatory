# 02 — Shared UI System (Global Baseline)

> Lightweight global foundation only. Per-screen layouts, component hierarchies, and interactive states are designed **per task** inside each `docs/tasks/TXX-*.md` via `hackathon-ui-design` immediately before implementing that task.

## Baseline & Constraints

- **Framework:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4 (`@import "tailwindcss";` in `frontend/src/app/globals.css`).
- **Accessibility Baseline:** **WCAG 2.2 AA** with `light` / `dark` / `system` appearance support (`DEC-001`) using CSS `light-dark()` semantic tokens (`--color-canvas`, `--color-surface`, `--color-text`, `--color-border`, `--color-accent`).
- **Localization Baseline:** `pl-PL` (default) and `en-US` via `LocaleProvider` + `useTranslations()` (`DEC-001`), persisted in `localStorage` (`hn26-locale`) with pre-hydration sync.
- **Contrast & Targets:** `>= 4.5:1` normal text contrast, `>= 3:1` borders/controls contrast, visible `:focus-visible` outlines, `>= 44px` (`min-h-11`) interactive targets, non-color status cues (`PASS`/`FAIL` badges or icons + text), and `aria-live="polite"` for live updates.

## App Shell & Navigation

- **Global Layout (`frontend/src/app/layout.tsx`):** `<Header brand/nav, max-width container, footer>`
- **Primary Navigation Items:** `<Links shown across pages>`

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

## Reference Assets (`docs/inputs/ui/`)

- `<List any logo, palette, or screenshot filenames placed in docs/inputs/ui/>`
