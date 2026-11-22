#!/usr/bin/env bash
# Local side (T10, DEC-018): deploy the dane.gov.pl fork + mcod.aed to the Hetzner server.
#   fork-config/hetzner/deploy.sh [ssh-host] [public-ip]      (defaults: hack 2.29.205.102)
# Images are shipped separately once: docker save <fork images> | zstd | ssh hack 'zstd -d | docker load'.
# Code goes to /home/github/apps/danegov-fork (outside the CI-synced app dir). Secrets: only WARSAW_API_TOKEN,
# copied from the repo .env into the server-side danegov-fork/.env.
set -euo pipefail
HOST="${1:-hack}"
IP="${2:-2.29.205.102}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
DEST=/home/github/apps/danegov-fork

echo "==> sync code to $HOST:$DEST"
ssh "$HOST" "mkdir -p $DEST"
rsync -az --delete \
  --exclude 'backend_latest/media/' --exclude 'node_modules/' --exclude '.angular/' --exclude '__pycache__/' \
  --exclude 'backend_latest/.env' --exclude 'backend_latest/docker/nginx/certs/' --exclude '.git/' \
  "$REPO/dane-gov-pl/" "$HOST:$DEST/dane-gov-pl/"
rsync -az --delete --exclude '__pycache__/' "$REPO/fork-config/" "$HOST:$DEST/fork-config/"
TOKEN="$(grep -E '^WARSAW_API_TOKEN=' "$REPO/.env" 2>/dev/null | head -1 | cut -d= -f2- || true)"
ssh "$HOST" "umask 077; printf 'WARSAW_API_TOKEN=%s\n' '$TOKEN' > $DEST/.env"

echo "==> server: config, hostnames, certificate, setup"
ssh "$HOST" "set -e; cd $DEST
  mkdir -p dane-gov-pl/backend_latest/media
  cp fork-config/backend.env dane-gov-pl/backend_latest/.env
  fork-config/hetzner/apply-hostnames.sh $IP
  fork-config/hetzner/certs.sh $IP
  FORK_SKIP_BUILD=1 fork-config/setup.sh"
echo "==> done. Next: ssh $HOST 'cd $DEST && fork-config/aed-demo.sh'"
