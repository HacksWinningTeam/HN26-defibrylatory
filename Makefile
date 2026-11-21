.PHONY: help up up-d down down-v up-prod down-prod build logs migrate makemigrations createsuperuser shell test lint schema-check migrations-check build-prod

help:
	@echo "Available targets:"
	@echo "  up              Start all services in foreground (with build)"
	@echo "  up-d            Start all services in background (with build)"
	@echo "  down            Stop and remove containers"
	@echo "  down-v          Stop containers and remove volumes"
	@echo "  up-prod         Start production stack (compose.prod.yaml)"
	@echo "  down-prod       Stop production stack (compose.prod.yaml)"
	@echo "  build           Rebuild service images"
	@echo "  logs            Follow logs from all services"
	@echo "  migrate         Run Django migrations"
	@echo "  makemigrations  Create new Django migrations"
	@echo "  createsuperuser Create a Django superuser"
	@echo "  shell           Open Django shell"
	@echo "  test            Run backend pytest suite"
	@echo "  lint            Run backend (ruff) and frontend (typecheck + eslint) checks"
	@echo "  schema-check    Validate drf-spectacular OpenAPI schema"
	@echo "  migrations-check Fail if any model change is missing a migration"
	@echo "  build-prod      Build production backend and frontend images"

up:
	docker compose up --build

up-d:
	docker compose up -d --build

down:
	docker compose down

down-v:
	docker compose down -v

up-prod:
	docker compose -f compose.prod.yaml up -d --build --remove-orphans

down-prod:
	docker compose -f compose.prod.yaml down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec backend python manage.py migrate

makemigrations:
	docker compose exec backend python manage.py makemigrations

createsuperuser:
	docker compose exec backend python manage.py createsuperuser

shell:
	docker compose exec backend python manage.py shell

test:
	docker compose exec -T backend pytest

lint:
	docker compose exec -T backend ruff check .
	docker compose exec -T frontend npm run typecheck
	docker compose exec -T frontend npm run lint

schema-check:
	docker compose exec -T backend python manage.py spectacular --validate --fail-on-warn

migrations-check:
	docker compose exec -T backend python manage.py makemigrations --check --dry-run

build-prod:
	docker build --target prod -t django-nextjs-backend:prod ./backend
	docker build --target prod --build-arg NEXT_PUBLIC_API_URL=$${NEXT_PUBLIC_API_URL:-} -t django-nextjs-frontend:prod ./frontend
