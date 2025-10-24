#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://127.0.0.1:8001}"
curl -fsS "$BASE/app/js/core/map.js" >/dev/null
echo "OK: core map helper served"
