#!/usr/bin/env bash
# One-shot, idempotent setup of the local dane.gov.pl fork.
#   1. copy our config into dane-gov-pl/backend_latest (and create 4 empty dirs)
#   2. pre-pull Docker Hub base images via mirror.gcr.io (Docker Hub rate limit workaround)
#   3. build ONLY the services we use (never the private discourse image)
#   4. start infra, init DB (migrate + fixtures) + ES index (only on first run)
#   5. start app services + Angular dev server (see start.sh)
# Safe to re-run. Never deletes volumes.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORK="$HERE/../dane-gov-pl"
BE="$FORK/backend_latest"
FE="$FORK/frontend_latest"
FC="$HERE/fork-compose.sh"

[ -d "$BE" ] && [ -d "$FE" ] || { echo "dane-gov-pl/{backend_latest,frontend_latest} not found" >&2; exit 1; }

echo "==> [1/5] Copying fork-config into dane-gov-pl/"
cp "$HERE/backend.env" "$BE/.env"
cp "$HERE/local.py" "$BE/mcod/settings/local.py"
cp "$HERE/nginx/07-aed.conf.template" "$BE/docker/nginx/config-templates/07-aed.conf.template"
# bind-mount targets (created as the current user, not root)
mkdir -p "$BE/test-data" "$FE/node_modules" "$FE/.angular"

echo "==> [2/5] Pre-pulling base images from mirror.gcr.io (skips ones already present)"
pull_mirror() {  # $1 = local name, $2 = mirror path
  if ! docker image inspect "$1" >/dev/null 2>&1; then
    docker pull -q "mirror.gcr.io/$2" && docker tag "mirror.gcr.io/$2" "$1"
  fi
}
for img in python:3.8.20-bullseye postgres:17-trixie redis:8.4.2-trixie \
           rabbitmq:4.2.5-management-alpine nginx:1.31.6 node:22-bookworm-slim; do
  pull_mirror "$img" "library/$img"
done
pull_mirror mailhog/mailhog mailhog/mailhog:latest

echo "==> [3/5] Building images (app image: python 3.8 + pipenv, slow on first run)"
"$FC" build mcod-db mcod-rabbitmq mcod-redis mcod-elasticsearch mcod-nginx
if ! docker image inspect mcod-app:local >/dev/null 2>&1; then
  (cd "$BE" && docker build -f docker/app/Dockerfile -t mcod-app:local .)
fi

echo "==> [4/5] Starting infra + bootstrapping DB / ES"
"$FC" up -d --no-build mcod-db mcod-redis mcod-rabbitmq mcod-elasticsearch mcod-smtp mcod-nginx

echo "    waiting for postgres + elasticsearch..."
for _ in $(seq 1 60); do
  docker exec mcod-db pg_isready -U mcod >/dev/null 2>&1 \
    && docker exec mcod-elasticsearch curl -fs localhost:9200/_cluster/health >/dev/null 2>&1 && break
  sleep 2
done

run() { "$FC" run --rm --no-deps mcod-local-run "$@"; }

if docker exec mcod-db psql -U mcod -d mcod -tAc "select 1 from \"user\" where email='admin@mcod.local'" 2>/dev/null | grep -q 1; then
  echo "    DB already initialised (admin@mcod.local exists) - running migrate only"
  run python manage.py migrate --noinput
else
  echo "    init_mcod_db (migrate + fixtures)"
  run python manage.py init_mcod_db
fi

if docker exec mcod-elasticsearch curl -fs "localhost:9200/_cat/indices" | grep -q datasets; then
  echo "    ES indices exist - skipping rebuild (force: fork-compose.sh run --rm --no-deps mcod-local-run python manage.py search_index --rebuild -f)"
else
  echo "    search_index --rebuild -f"
  run python manage.py search_index --rebuild -f
fi

echo "==> [5/5] Starting app services"
"$HERE/start.sh"
