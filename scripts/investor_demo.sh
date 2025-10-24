#!/usr/bin/env bash
set -euo pipefail
BASE=${1:-http://127.0.0.1:8001}
echo "👥 Follow jane → alex"
curl -s -X POST "$BASE/v1/social/follow" -H 'content-type: application/json' \
  -d '{"follower_id":"jane","followee_id":"alex","follow":true}' | jq
echo "⚡ Award \$1.00 to alex"
curl -s -X POST "$BASE/v1/incentives/award?user_id=alex&cents=100" | jq
echo "🏦 Settle follower pool"
curl -s -X POST "$BASE/v1/admin/settle" | jq
echo "📰 Feed (5)"
curl -s "$BASE/v1/social/feed?limit=5" | jq
echo "💧 Pool snapshot"
curl -s "$BASE/v1/social/pool" | jq