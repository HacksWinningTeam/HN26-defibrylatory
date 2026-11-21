#!/usr/bin/env bash
# Publish / refresh the national AED dataset in the running fork (T06). Idempotent.
# Usage: fork-config/publish.sh            (AED_BASE_URL, AED_WAIT_SECONDS, AED_REVALIDATE=1 optional)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker exec -i \
  -e AED_BASE_URL="${AED_BASE_URL:-https://aed.mcod.local}" \
  -e AED_WAIT_SECONDS="${AED_WAIT_SECONDS:-600}" \
  -e AED_REVALIDATE="${AED_REVALIDATE:-0}" \
  mcod-admin python manage.py shell < "$HERE/publish_aed.py" 2>&1 \
  | grep -v -i -E '^(20[0-9]{2}-[0-9]{2}-[0-9]{2} .*(DEBUG|INFO)|\[[a-z0-9_]+\] sender:|NoneType: None|.*warn)'
