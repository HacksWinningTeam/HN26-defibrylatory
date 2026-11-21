# Accessibility System (WCAG 2.2 AA)

> Adapted from `HackYeah2026-Defence` (`DEC-002`) and integrated with `HN26-PCI` localization (`pl-PL` default / `en-US`) and pre-hydration (`frontend/src/lib/prehydrate.ts`).

## Purpose

The application targets **WCAG 2.2 AA** across every page, component, and user journey. Semantic HTML, keyboard operability, visible focus indicators, and sufficient contrast are the default for everyone; the floating accessibility control and settings view provide additional presentation preferences on top of that baseline.

## Guiding Principles

- **Native HTML before ARIA:** Use native `<button>`, `<input>`, `<label>`, `<select>`, headings, links, and landmarks (`<header>`, `<main>`, `<footer>`).
- **Inclusive defaults:** Every feature must be usable without opening the accessibility control.
- **Semantic tokens only:** Components consume CSS custom properties (`--color-canvas`, `--color-surface`, `--color-text`, `--color-border`, `--color-accent`, etc.), never raw palette colors.
- **Preserve OS & browser preferences:** Respect `prefers-color-scheme`, `prefers-reduced-motion`, `forced-colors: active`, and browser zoom up to 400%.
- **Test behavior, not just markup:** Verify keyboard navigation, focus restoration, 200% in-app text scale, 400% browser zoom, and Polish/English screen-reader labels.

## Preference Contract

Preferences are owned at the application root (`AccessibilityProvider`, extending/unifying `AppearanceProvider`) and persisted in `localStorage` under `hn26-accessibility` (and synced with `hn26-appearance` / `getPrehydrateScript()` before first paint):

```ts
export const APPEARANCE_PREFERENCES = [
  "system",
  "light",
  "dark",
  "hc-black-white",
  "hc-black-yellow",
  "grayscale",
] as const;

export const TEXT_SCALES = [25, 50, 75, 100, 112.5, 125, 150, 175, 200] as const;

export type AccessibilityPreferences = {
  appearance: (typeof APPEARANCE_PREFERENCES)[number]; // default: "system"
  textScale: (typeof TEXT_SCALES)[number];              // default: 100
  underlineLinks: boolean;                              // default: false
};
```

Root `<html>` attributes applied synchronously in `<head>` by `getPrehydrateScript()` and kept in sync by `AccessibilityProvider`:
- `data-appearance`: `"light" | "dark" | "hc-black-white" | "hc-black-yellow" | "grayscale"` (resolved from `"system"` via `prefers-color-scheme`)
- `data-text-scale`: `"25" | ... | "200"` (drives root `font-size` percentage)
- `data-underline-links`: `"true" | "false"` (enforces `text-decoration: underline` on links via CSS token)

## Theme & Token Maps (`globals.css`)

All semantic tokens (`--color-canvas`, `--color-surface`, `--color-surface-raised`, `--color-text`, `--color-text-muted`, `--color-border`, `--color-border-subtle`, `--color-accent`, `--color-accent-hover`, `--color-accent-text`, `--color-on-accent`, `--color-focus`, and semantic success/warning/error tokens) must be mapped for all 5 resolved themes:

1. `light` — WCAG AA light palette (`>= 4.5:1` text, `>= 3:1` controls/borders).
2. `dark` — WCAG AA dark palette.
3. `hc-black-white` — Pure black (`#000000`) surfaces, white (`#ffffff`) text/controls/focus rings.
4. `hc-black-yellow` — Pure black (`#000000`) surfaces, high-contrast yellow (`#ffea00` / `#ffd600`) text, controls, and focus rings.
5. `grayscale` — Explicit neutral grayscale token map (never a blanket `filter: grayscale()` that degrades media).

In `@media (forced-colors: active)`, defer to system colors. In `@media (prefers-reduced-motion: reduce)`, disable non-essential transitions and animations.

## Accessibility Control & Settings Surface

1. **Floating `AccessibilityMenu` (`frontend/src/components/accessibility/AccessibilityMenu.tsx`):**
   - Native `<button>` launcher with `aria-expanded` and `aria-controls`, hidden on `/settings/accessibility`.
   - Non-modal `role="dialog"` panel (no focus trap; Tab continues naturally; `Escape` or launcher closes and returns focus to launcher; outside pointer closes without stealing focus).
   - Opening moves focus to the currently checked appearance radio input.
2. **Controls (`AccessibilityPreferencesControls.tsx`, shared between popover and `/settings/accessibility`):**
   - **Display Mode:** Radio group (`System`, `Light`, `Dark`, `High Contrast: Black/White`, `High Contrast: Black/Yellow`, `Grayscale`) — all labels localized in `pl-PL` and `en-US`.
   - **Text Size:** Decrease (`A−`), `<output aria-live="polite">` showing current `%`, Increase (`A+`), and Reset (`100%`), with native `disabled` at bounds (`25%` / `200%`).
   - **Underline Links:** Native `<input type="checkbox" role="switch">`.
   - **Read Aloud:** Browser `window.speechSynthesis` controls (Play/Pause/Resume, Stop, `aria-live="polite"` status) reading `<main>` content using `document.documentElement.lang` (`pl-PL` or `en-US`).
   - **Reset Settings:** Restores `appearance: "system"`, `textScale: 100`, `underlineLinks: false`.

## Delivery & Verification Checklist

1. **Vertical Slice:**
   - Extend `frontend/src/appearance/` + `frontend/src/lib/prehydrate.ts` into the full `AccessibilityProvider` contract.
   - Add `hc-black-white`, `hc-black-yellow`, `grayscale`, `data-text-scale`, and `data-underline-links` token maps to `frontend/src/app/globals.css`.
   - Add Polish & English translations for all accessibility labels and live announcements to `frontend/src/i18n/messages.ts`.
   - Build `AccessibilityMenu`, `AccessibilityPreferencesControls`, and `/settings/accessibility` route.
2. **Verification:**
   - Unit tests (`node --test`) for preference parsing/validation, pre-hydration script syntax, and i18n catalog parity.
   - `npm run typecheck`, `npm run lint`, and production build.
   - Manual keyboard-only walkthrough (Tab, Shift+Tab, Arrow keys in radio group, Escape focus restoration), 200% in-app text scale, 400% browser zoom, and `pl-PL` / `en-US` Read Aloud check.
