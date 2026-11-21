#!/usr/bin/env bash
# Stop the local dane.gov.pl fork. Keeps containers' volumes (DB, ES, node_modules).
# Never add -v here.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$HERE/fork-compose.sh" stop
