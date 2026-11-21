#!/usr/bin/env bash
# Thin wrapper: docker compose for the dane.gov.pl fork with our override.
# Usage: fork-config/fork-compose.sh <compose args...>   (ALWAYS name services for build/up!)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORK_BACKEND="${FORK_BACKEND:-$HERE/../dane-gov-pl/backend_latest}"
cd "$FORK_BACKEND"
exec docker compose -f docker-compose.local.yml -f "$HERE/compose.override.yml" "$@"
