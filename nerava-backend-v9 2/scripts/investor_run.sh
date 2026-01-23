#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8001}"
KEY="${KEY:-demo_admin_key}"
hdr=(-H "Authorization: Bearer $KEY" -H "Content-Type: application/json")
echo "Enable flags"; curl -s -X POST "$API/v1/demo/enable_all" "${hdr[@]}" >/dev/null || true
echo "Seed"; curl -s -X POST "$API/v1/demo/seed" "${hdr[@]}" >/dev/null || true
echo "State"; curl -s "$API/v1/demo/state" "${hdr[@]}" | jq || true
echo "Offpeak"; curl -s -X POST "$API/v1/demo/scenario" "${hdr[@]}" -d '{"key":"grid_state","value":"offpeak"}' >/dev/null || true
echo "Peak"; curl -s -X POST "$API/v1/demo/scenario" "${hdr[@]}" -d '{"key":"grid_state","value":"peak"}' >/dev/null || true
echo "Export"; mkdir -p tmp/demo; curl -s "$API/v1/demo/export" "${hdr[@]}" > "tmp/demo/export-$(date +%Y%m%d-%H%M%S).json"