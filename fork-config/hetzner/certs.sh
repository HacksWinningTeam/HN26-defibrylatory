#!/usr/bin/env bash
# Server side (T10): Let's Encrypt certificate for the public fork hostnames (HTTP-01 on port 80, one-off
# certbot container, no e-mail registered). Falls back to a self-signed certificate if issuance fails.
# Installs the files under the names the nginx templates expect: docker/nginx/certs/<NEW>.{crt,key,pem}.
set -euo pipefail
IP="${1:?usage: certs.sh <public-ip>}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NEW="mcod.${IP}.sslip.io"
CERTS="$ROOT/dane-gov-pl/backend_latest/docker/nginx/certs"
LE="/etc/letsencrypt/live/${NEW}"
mkdir -p "$CERTS"
if [ ! -f "$LE/fullchain.pem" ]; then
  echo "==> requesting Let's Encrypt certificate for ${NEW} (+ api./admin./cms.)"
  docker stop mcod-nginx >/dev/null 2>&1 || true   # port 80 must be free for the challenge
  docker run --rm -p 80:80 -v /etc/letsencrypt:/etc/letsencrypt -v /var/lib/letsencrypt:/var/lib/letsencrypt \
    certbot/certbot:v3.1.0 certonly --standalone --non-interactive --agree-tos --register-unsafely-without-email \
    -d "${NEW}" -d "api.${NEW}" -d "admin.${NEW}" -d "cms.${NEW}" || echo "!! Let's Encrypt failed"
fi
if [ -f "$LE/fullchain.pem" ]; then
  cp -L "$LE/fullchain.pem" "$CERTS/${NEW}.crt"
  cp -L "$LE/privkey.pem" "$CERTS/${NEW}.key"
  cp -L "$LE/fullchain.pem" "$CERTS/${NEW}.pem"
  echo "    installed Let's Encrypt certificate"
else
  echo "==> fallback: self-signed certificate"
  openssl req -x509 -nodes -newkey rsa:2048 -days 30 -subj "/CN=${NEW}" \
    -addext "subjectAltName=DNS:${NEW},DNS:api.${NEW},DNS:admin.${NEW},DNS:cms.${NEW}" \
    -keyout "$CERTS/${NEW}.key" -out "$CERTS/${NEW}.crt"
  cp "$CERTS/${NEW}.crt" "$CERTS/${NEW}.pem"
fi
# Celery mounts docker/nginx/certs/mcod.local.pem (CA bundle it trusts for portal->API calls); without the
# file Docker creates a directory there and Celery crashes at start -> install our certificate under that name.
rm -rf "$CERTS/mcod.local.pem" 2>/dev/null || true
cp "$CERTS/${NEW}.pem" "$CERTS/mcod.local.pem"

