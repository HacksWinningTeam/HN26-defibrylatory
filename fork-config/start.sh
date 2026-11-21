#!/usr/bin/env bash
# Start (or restart after reboot) the whole local dane.gov.pl fork. Requires setup.sh once.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$HERE/fork-compose.sh" up -d --no-build \
  mcod-db mcod-redis mcod-rabbitmq mcod-elasticsearch mcod-smtp mcod-nginx \
  mcod-local-admin mcod-local-api mcod-local-cms mcod-local-celery mcod-frontend
cat <<'MSG'
Fork starting. Angular dev server compiles for ~1-2 min (first run: npm ci, several minutes):
  docker logs -f mcod-frontend
URLs (needs the /etc/hosts line from fork-config/README.md, accept the self-signed cert):
  https://mcod.local            portal (Angular)
  https://admin.mcod.local      admin (admin@mcod.local / testadmin123!)
  https://api.mcod.local/1.4/   API
  https://aed.mcod.local/       -> our backend on host :8000
  http://127.0.0.1:8025         mailhog
MSG
