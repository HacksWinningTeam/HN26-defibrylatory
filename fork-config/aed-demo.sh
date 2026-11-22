#!/usr/bin/env bash
# Prepare the "Misja AED" demo inside the running dane.gov.pl fork (T09): import the AED source datasets
# (online, falls back to the committed snapshot), wait for the portal + automatic validation, aggregate.
# Usage: fork-config/aed-demo.sh [--offline]     (idempotent; ~1 min)
set -euo pipefail
OFFLINE="${1:-}"
echo "==> 1/3 import AED source datasets (standard aed-pl)"
docker exec mcod-admin python -W ignore manage.py aed_import_sources ${OFFLINE} 2>&1 \
  | grep -E "^(Tryb|Instytucja|Urząd|Współ|Misja|Gotowe|!)" || true
echo "==> 2/3 waiting for the portal's processing + automatic validation (Celery)"
for _ in $(seq 1 36); do
  pending=$(docker exec mcod-admin python -W ignore manage.py shell -c "
from mcod.resources.models import Resource
qs = Resource.raw.filter(dataset__aed_standard_link__standard__code='aed-pl', is_removed=False, dataset__status='published', aed_standard_validation__isnull=True)
print(qs.count())" 2>/dev/null | tail -1) || pending="?"
  [ "${pending:-1}" = "0" ] && break
  sleep 5
done
echo "    resources still waiting for validation: ${pending:-?}"
echo "==> 3/3 aggregate into 'Defibrylatory AED – zbiór ogólnopolski'"
docker exec mcod-admin python -W ignore manage.py aed_aggregate 2>&1 | grep -vE "DEBUG|INFO|sender:|NoneType|^\s*$|UserWarning|warnings.warn"
echo "==> done: https://mcod.local/pl/dataset?q=defibrylator  |  https://api.mcod.local/1.4/aed/sources  |  http://localhost:3000/"
