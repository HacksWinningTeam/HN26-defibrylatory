#!/usr/bin/env bash
# Run the mcod.aed plugin tests inside the running fork (mcod-admin container). Usage: fork-config/test.sh [-v]
set -euo pipefail
docker exec mcod-admin python -W ignore -m mcod.aed.tests.run "$@"
