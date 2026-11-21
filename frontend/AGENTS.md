# Frontend Agent Rules (`frontend/`)

Applies to Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, and ESLint 9.

## Next.js 16 App Router & Standalone Builds

- Default to Server Components; add `"use client"` only on interactive leaf components.
- Export `export const dynamic = "force-dynamic";` on SSR pages that fetch live data from Django so `next build` in `frontend/Dockerfile` succeeds without a running backend.
- Keep `frontend/public/.gitkeep` committed so `COPY --from=builder /app/public ./public` in `frontend/Dockerfile` always succeeds.

## API Client & Single-Port Proxy

- Route all backend requests through helpers in `frontend/src/lib/api.ts` (`getApiBaseUrl()` uses `API_INTERNAL_URL` on the server and same-origin `""` in the browser).
- Never hardcode `http://localhost:8000` (or any backend origin) in browser-executed code; the only allowed fallback is the server-side one inside `getApiBaseUrl()`.
- Keep `frontend/src/proxy.ts` (Next.js 16 convention — never add deprecated `middleware.ts`) and `skipTrailingSlashRedirect: true` in `frontend/next.config.ts` so `/api/...`, `/admin/...`, and `/static/...` forward to Django without redirect loops.

## Tailwind CSS v4 & WCAG 2.2 AA Light Baseline

- Use Tailwind CSS v4 CSS-first configuration (`@import "tailwindcss";` in `frontend/src/app/globals.css`); do not add a legacy `tailwind.config.js`.
- Stick to the light WCAG 2.2 AA baseline — do **not** add dark mode or theme toggles unless explicitly requested.
- Maintain >= 4.5:1 normal text contrast and >= 3:1 contrast for UI controls and borders.
- Preserve visible `:focus-visible` outlines, >= 44px (`min-h-11`) interactive click/touch targets, semantic landmarks (`<header>`, `<main>`, `<footer>`, sequential headings), text/icon indicators alongside color, and `aria-live="polite"` for live status updates.

## TypeScript, Linting, Tests & Dependencies

- Keep strict TypeScript enabled (`frontend/tsconfig.json`); avoid `any` and lint suppressions.
- Always run `npm run typecheck` (`tsc --noEmit`) and `npm run lint` (`eslint .` using `frontend/eslint.config.mjs` — never the removed `next lint`) inside the `frontend` container or local toolchain after edits.
- If a unit test runner (e.g., Vitest) is added for frontend code, write unit tests for new client logic/utilities and run the test suite alongside `typecheck` and `lint`.
- After modifying `frontend/package.json`, run `docker compose up -V --build` to renew the anonymous `/app/node_modules` volume.
