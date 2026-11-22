#!/usr/bin/env bash
# Server side (T10, DEC-018): rewrite the fork's hard-wired "mcod.local" hostnames in the DEPLOYED copy
# to public sslip.io names, e.g. mcod.2.29.205.102.sslip.io / api.mcod.… / admin.mcod.… / cms.mcod.…
# Usage (from the deploy root that contains dane-gov-pl/ and fork-config/): fork-config/hetzner/apply-hostnames.sh <ip>
# Idempotent: only files still containing "mcod.local" are changed. Never run this on a developer machine.
set -euo pipefail
IP="${1:?usage: apply-hostnames.sh <public-ip>}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NEW="mcod.${IP}.sslip.io"
BE="$ROOT/dane-gov-pl/backend_latest"
FE="$ROOT/dane-gov-pl/frontend_latest"
FILES=(
  "$BE/.env"
  "$BE/docker/nginx/config-templates/"*.template
  "$FE/angular.json"
  "$FE/proxy.local.conf.json"
  "$ROOT/fork-config/compose.override.yml"
  "$ROOT/fork-config/backend.env"                 # setup.sh copies these two into the fork again,
  "$ROOT/fork-config/nginx/07-aed.conf.template"  # so their deployed copies are rewritten too
)
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  if grep -q "mcod\.local" "$f"; then
    # keep the fixture admin login e-mail (admin@mcod.local) untouched
    sed -i -E "s/(^|[^@a-z0-9-])((admin|api|cms|forum|mail|aed)\.)?mcod\.local/\1\2${NEW}/g" "$f"
    echo "  rewritten: ${f#$ROOT/}"
  fi
done
# Angular/Vite dev server host check: nginx in front only forwards our server_names, so allow all hosts in
# the deployed angular.json ("local" serve config; the rewritten host list is not honoured behind nginx).
python3 - "$FE/angular.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path) as fh:
    cfg = json.load(fh)
for project in cfg["projects"].values():
    local = project["architect"]["serve"].get("configurations", {}).get("local")
    if local is not None:
        local["allowedHosts"] = True
with open(path, "w") as fh:
    json.dump(cfg, fh, indent=2)
PY
sed -i 's/ --disable-host-check//' "$ROOT/fork-config/compose.override.yml"
grep -q "^ALLOWED_HOSTS" "$BE/.env" && sed -i "s/^ALLOWED_HOSTS=.*/ALLOWED_HOSTS=*/" "$BE/.env" || true
echo "hostnames -> https://${NEW}  https://api.${NEW}  https://admin.${NEW}"
