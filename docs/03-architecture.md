# 03 — System Architecture

> Living technical architecture for backend, API contract, frontend routes, and integrations. Updated by `hackathon-plan`, `hackathon-ui-design` (when UI requires new fields/endpoints), and `hackathon-update-plan`.

## High-Level Data Flow

```text
Browser (same-origin) -> Next.js 16 (src/proxy.ts / SSR via API_INTERNAL_URL) -> Django 5.2 + DRF -> PostgreSQL 18
```

## Backend Apps & Data Models (`backend/`)

- **`apps.core`**: Built-in `GET /api/health/` readiness check.
- **`apps.<feature>`**: `<Models, key fields, relationships, and constraints>`

## API Endpoints Overview (`drf-spectacular`)

| Method & Path | View / App | Purpose | Auth / Permissions | Task |
| --- | --- | --- | --- | --- |
| `GET /api/health/` | `HealthCheckView` (`apps.core`) | DB + service readiness | Public | Starter |
| `GET /api/schema/`, `/api/docs/`, `/api/redoc/` | `drf-spectacular` | OpenAPI 3 spec & docs UI | Public | Starter |

## Frontend Routes & Modules (`frontend/`)

| Route | Component / Type | Purpose | API Endpoints Used | Task |
| --- | --- | --- | --- | --- |
| `/` | `src/app/page.tsx` (SSR `force-dynamic`) | Starter connectivity check | `GET /api/health/` | Starter |

## Environment Variables & External Integrations

- Document every new variable in `.env.example`, `compose.yaml`, and `compose.prod.yaml`.
- `<External APIs, keys, timeouts, fallback behavior>`

## Hackathon Simplifications & Tradeoffs

- `<Explicit shortcuts taken for hackathon speed and why they are safe for the demo>`
