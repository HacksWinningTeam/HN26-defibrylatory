#!/usr/bin/env bash
# Thin wrapper: docker compose for the dane.gov.pl fork with our override.
# Usage: fork-config/fork-compose.sh <compose args...>   (ALWAYS name services for build/up!)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORK_BACKEND="${FORK_BACKEND:-$HERE/../dane-gov-pl/backend_latest}"
# Secrets for connected APIs come from our untracked root .env (never from tracked fork-config files).
if [ -z "${WARSAW_API_TOKEN:-}" ] && [ -f "$HERE/../.env" ]; then
  WARSAW_API_TOKEN="$(grep -E '^WARSAW_API_TOKEN=' "$HERE/../.env" | head -1 | cut -d= -f2- | tr -d "\"' ")"
  export WARSAW_API_TOKEN
fi
cd "$FORK_BACKEND"
exec docker compose -f docker-compose.local.yml -f "$HERE/compose.override.yml" "$@"
