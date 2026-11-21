# Backend Agent Rules (`backend/`)

Applies to Django 5.2 LTS, Django REST Framework, `drf-spectacular`, and `uv`.

## App & URL Layout

- Place new domain apps under `backend/apps/<feature>/` with `AppConfig.name = "apps.<feature>"`.
- Register each new app in `INSTALLED_APPS` in `backend/config/settings.py` and include its URLs under `api/` in `backend/config/urls.py`.
- Keep `backend/apps/core/views.py` (`GET /api/health/`) publicly accessible (`authentication_classes = []`, `permission_classes = []`) so Docker healthchecks keep passing even if auth is added later.

## DRF & OpenAPI (`drf-spectacular`)

- Define explicit `Serializer` subclasses and `@extend_schema` annotations (request/response serializers, status codes, tags) on every API view so `/api/schema/`, `/api/docs/`, and `/api/redoc/` remain accurate.
- Keep `python manage.py spectacular --validate --fail-on-warn` passing with zero warnings.

## Authentication & CSRF

- The MVP has no API auth: `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = []` in `backend/config/settings.py`. Do not remove it casually — with DRF's default `SessionAuthentication`, any browser `POST/PUT/PATCH/DELETE` to `/api/...` fails with `403 CSRF Failed` as soon as someone is logged into `/admin/` (same origin through the Next.js proxy).
- If API auth is explicitly requested later, log a `DEC-XXX`, enable it in settings or per view, and make the frontend send the `X-CSRFToken` header (from the `csrftoken` cookie) on unsafe requests.

## Models, Migrations & Settings

- Always generate migrations alongside model changes (`make makemigrations`) and verify `make migrate`; never modify already-applied migration files.
- Confirm no model change is missing a migration: `docker compose exec -T backend python manage.py makemigrations --check --dry-run` (or `make migrations-check`).
- Keep queries and fields compatible with PostgreSQL 18 + `psycopg[binary]` v3, and preserve the SQLite fallback in `backend/config/settings.py` so `collectstatic` works during Docker `prod` image builds.
- Never bypass the production `DJANGO_SECRET_KEY` guard in `backend/config/settings.py`.

## Dependencies (`uv`)

- Add runtime dependencies to `[project] dependencies` and dev/test tools to `[dependency-groups] dev` in `backend/pyproject.toml`, then rebuild the `backend` container (`docker compose up -d --build backend`).
- Never install ad-hoc packages directly inside a running container.

## Unit Tests & Verification

- Write `pytest` unit and API tests (using `@pytest.mark.django_db` and DRF `APIClient`) covering happy paths, validation errors, and permissions for every new/modified endpoint or helper.
- Run all backend checks after edits:
  - `docker compose exec -T backend pytest` (or `make test`)
  - `docker compose exec -T backend ruff check .` (Python 3.12, line-length 100)
  - `docker compose exec -T backend python manage.py spectacular --validate --fail-on-warn` (or `make schema-check`)
  - `docker compose exec -T backend python manage.py makemigrations --check --dry-run` (or `make migrations-check`)
