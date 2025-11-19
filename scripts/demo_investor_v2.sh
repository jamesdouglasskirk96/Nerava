#!/usr/bin/env bash
# scripts/demo_investor_v2.sh
# Nerava end-to-end investor demo (no external payments required).
# Shows: Find → Verify → Earn → Pool → Offers → Events → Join → Verify → Wallet → Merchant Dashboard → Anti-Fraud.
set -euo pipefail

############################################
# Config — edit these or export before run #
############################################
: "${BASE_URL:=http://localhost:8001}"   # e.g., https://debug-weekend-...trycloudflare.com
: "${API_KEY:=}"                         # optional: X-Api-Key for public cloud tunnel
: "${USER_ID:=1}"                        # demo user
: "${CENTER_LAT:=30.2672}"               # downtown Austin
: "${CENTER_LNG:=-97.7431}"

# Pretty logging helpers
log()   { printf "\n\033[1;36m[%s]\033[0m %s\n" "$(date +%H:%M:%S)" "$*"; }
ok()    { printf "\033[1;32m✓\033[0m %s\n" "$*"; }
warn()  { printf "\033[1;33m!\033[0m %s\n" "$*"; }
die()   { printf "\033[1;31m✗ %s\033[0m\n" "$*" ; exit 1; }

# curl wrapper
CURL=(curl -sS -f)
HDRS=(-H 'Content-Type: application/json')
if [[ -n "${API_KEY}" ]]; then
  HDRS+=(-H "X-Api-Key: ${API_KEY}")
fi

jq_check() { command -v jq >/dev/null || die "jq is required. brew install jq (mac) or apt-get install jq"; }
jq_check

############################################
# 0) Server health + migrations + seed     #
############################################
log "Health check @ ${BASE_URL}/health"
"${CURL[@]}" "${BASE_URL}/health" | jq .

log "Apply Alembic migrations → head"
cd nerava-backend-v9 || die "Run from repo root"
alembic upgrade head >/dev/null && ok "Migrations applied"

log "Seed minimal data (user, merchants, offers, event)"
python3 -m app.scripts.seed_minimal | tee /tmp/seed.out || true
SEED_EVENT_ID=$(grep -Eo 'event_id=([0-9]+)' /tmp/seed.out | cut -d= -f2 || true)
[[ -n "${SEED_EVENT_ID}" ]] && ok "Seeded event id: ${SEED_EVENT_ID}" || warn "Seed script didn't print event id (might already exist)."

############################################
# 1) Version / Debug                       #
############################################
log "Version & debug"
"${CURL[@]}" "${BASE_URL}/version" | jq .
# debug endpoint name may be /debug or /debug/rewards in your build; try both
if ! "${CURL[@]}" "${BASE_URL}/debug" >/dev/null 2>&1; then
  warn "/debug not found (ok)"; 
else
  "${CURL[@]}" "${BASE_URL}/debug" | jq .
fi

############################################
# 2) GPT-style discovery                   #
############################################
log "Find chargers near downtown Austin (3km)"
"${CURL[@]}" -G "${BASE_URL}/v1/gpt/find_charger" \
  --data-urlencode "lat=${CENTER_LAT}" \
  --data-urlencode "lng=${CENTER_LNG}" \
  --data-urlencode "radius_m=3000" \
  | tee /tmp/chargers.json | jq '.[0:5]'
PRIMARY_CHARGER_NAME=$(jq -r '.[0].name' /tmp/chargers.json 2>/dev/null || echo "")
PRIMARY_CHARGER_ID=$(jq -r '.[0].charger_id' /tmp/chargers.json 2>/dev/null || echo "")

log "Find coffee merchants within 1200m"
"${CURL[@]}" -G "${BASE_URL}/v1/gpt/find_merchants" \
  --data-urlencode "lat=${CENTER_LAT}" \
  --data-urlencode "lng=${CENTER_LNG}" \
  --data-urlencode "category=coffee" \
  --data-urlencode "radius_m=1200" \
  | tee /tmp/merchants.json | jq '.[0:8]'

############################################
# 3) Verify flow → reward (90/10)          #
############################################
log "Create verify link (JWT ~10min, one-time) for user ${USER_ID}"
CREATE_PAYLOAD=$(jq -nc --argjson uid "${USER_ID}" --arg ch "${PRIMARY_CHARGER_ID}" \
  '{user_id:$uid, charger_hint:$ch}')
"${CURL[@]}" -X POST "${BASE_URL}/v1/gpt/create_session_link" "${HDRS[@]}" \
  -d "${CREATE_PAYLOAD}" | tee /tmp/session_link.json | jq .
VERIFY_URL=$(jq -r '.url' /tmp/session_link.json)
SESSION_ID=$(jq -r '.session_id' /tmp/session_link.json)
ok "Verify URL: ${VERIFY_URL}"

log "Simulate GPS locate to verify (as if user granted location)"
NOW_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOCATE_PAYLOAD=$(jq -nc --arg ts "${NOW_TS}" \
  --argjson lat "${CENTER_LAT}" --argjson lng "${CENTER_LNG}" \
  '{ts:$ts, lat:$lat, lng:$lng, accuracy: 25, ua:"demo-script"}')
TOKEN=$(echo "${VERIFY_URL}" | sed -E 's#.*/verify/##')
"${CURL[@]}" -X POST "${BASE_URL}/v1/sessions/locate" "${HDRS[@]}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "${LOCATE_PAYLOAD}" | tee /tmp/locate.json | jq .
ok "Verify should have rewarded wallet (idempotent on second call)."

log "Wallet snapshot via /v1/gpt/me"
"${CURL[@]}" -G "${BASE_URL}/v1/gpt/me" --data-urlencode "user_id=${USER_ID}" | jq .

############################################
# 4) Offers API (thin)                     #
############################################
log "Offers near me (API wrapper)"
"${CURL[@]}" -G "${BASE_URL}/v1/offers/nearby" \
  --data-urlencode "lat=${CENTER_LAT}" \
  --data-urlencode "lng=${CENTER_LNG}" \
  --data-urlencode "radius_m=1500" \
  --data-urlencode "category=coffee" | jq '.[0:8]'

############################################
# 5) Events → join → verify (geo)          #
############################################
log "Create a public event today 14:00–16:00 (if you want fresh event)"
START_UTC="$(date -u +"%Y-%m-%d")T14:00:00Z"
END_UTC="$(date -u +"%Y-%m-%d")T16:00:00Z"
EVENT_PAYLOAD=$(jq -nc --arg title "Charge & Chill: Cold Plunge + Coffee" \
  --arg desc "Bring a towel. Green Window 2–4pm." \
  --arg city "Austin" --arg start "${START_UTC}" --arg end "${END_UTC}" \
  --arg gw_start "14:00" --arg gw_end "16:00" \
  --argjson lat "${CENTER_LAT}" --argjson lng "${CENTER_LNG}" \
  '{title:$title, description:$desc, category:"wellness", city:$city,
    lat:$lat, lng:$lng, starts_at:$start, ends_at:$end,
    green_window_start:$gw_start, green_window_end:$gw_end,
    price_cents:100, revenue_split:{pool_pct:20, activator_pct:80},
    capacity:40, visibility:"public"}')
CREATE_EVENT_JSON=$("${CURL[@]}" -X POST "${BASE_URL}/v1/events" \
  -H "X-User-Id: ${USER_ID}" "${HDRS[@]}" -d "${EVENT_PAYLOAD}" | tee /tmp/event_create.json)
EVENT_ID=$(echo "${CREATE_EVENT_JSON}" | jq -r '.id // empty')
if [[ -z "${EVENT_ID}" && -n "${SEED_EVENT_ID}" ]]; then
  EVENT_ID="${SEED_EVENT_ID}"
  warn "Using seeded event id: ${EVENT_ID}"
fi
[[ -n "${EVENT_ID}" ]] || die "No event id could be determined."

log "List events nearby within 2km"
"${CURL[@]}" -G "${BASE_URL}/v1/events/nearby" \
  --data-urlencode "lat=${CENTER_LAT}" \
  --data-urlencode "lng=${CENTER_LNG}" \
  --data-urlencode "radius_m=2000" \
  --data-urlencode "now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" | jq .

log "Join event ${EVENT_ID}"
"${CURL[@]}" -X POST "${BASE_URL}/v1/events/${EVENT_ID}/join" -H "X-User-Id: ${USER_ID}" | jq .

log "Start verification for event ${EVENT_ID}"
"${CURL[@]}" -X POST "${BASE_URL}/v1/events/${EVENT_ID}/verify/start" \
  -H "X-User-Id: ${USER_ID}" "${HDRS[@]}" -d '{"mode":"geo"}' \
  | tee /tmp/event_verify_start.json | jq .
VER_ID=$(jq -r '.id' /tmp/event_verify_start.json)

log "Complete verification (geo pass within 120m & time window)"
COMPLETE_PAYLOAD=$(jq -nc --argjson lat "${CENTER_LAT}" --argjson lng "${CENTER_LNG}" \
  '{lat:$lat, lng:$lng}')
"${CURL[@]}" -X POST "${BASE_URL}/v1/events/verify/${VER_ID}/complete" \
  "${HDRS[@]}" -d "${COMPLETE_PAYLOAD}" | tee /tmp/event_verify_done.json | jq .

log "Wallet snapshot after event verification"
"${CURL[@]}" -G "${BASE_URL}/v1/gpt/me" --data-urlencode "user_id=${USER_ID}" | jq .

############################################
# 6) Community Pool                        #
############################################
log "Pool summary for Austin (today)"
"${CURL[@]}" -G "${BASE_URL}/v1/pool/summary" \
  --data-urlencode "city=Austin" \
  --data-urlencode "range=today" | jq .

log "Pool ledger (first 20 rows)"
"${CURL[@]}" -G "${BASE_URL}/v1/pool/ledger" \
  --data-urlencode "city=Austin" \
  --data-urlencode "limit=20" | jq .

############################################
# 7) Merchant Dashboard API (auth key)     #
############################################
log "Merchant dashboard: summary + offers (using demo merchant key if present)"
DEMO_KEY=$(grep -Eo 'demo_key_[A-Za-z0-9_\-]+' /tmp/seed.out | head -n1 || true)
if [[ -n "${DEMO_KEY}" ]]; then
  "${CURL[@]}" -H "X-Merchant-Key: ${DEMO_KEY}" "${BASE_URL}/v1/merchant/summary" | jq .
  "${CURL[@]}" -H "X-Merchant-Key: ${DEMO_KEY}" "${BASE_URL}/v1/merchant/offers" | jq .
else
  warn "No demo merchant key found in seed output; skipping merchant summary/offers."
fi

############################################
# 8) Anti-Fraud Debug                      #
############################################
log "Anti-fraud debug snapshot"
if "${CURL[@]}" -G "${BASE_URL}/v1/debug/abuse" --data-urlencode "user_id=${USER_ID}" >/dev/null 2>&1; then
  "${CURL[@]}" -G "${BASE_URL}/v1/debug/abuse" --data-urlencode "user_id=${USER_ID}" | jq .
else
  warn "/v1/debug/abuse not present (ok on some builds)."
fi

############################################
# 9) ASCII Summary Cards                   #
############################################
printf "\n\033[1;35m"
printf "═══════════════════════════════════════════════════════════════\n"
printf "                NERAVA INVESTOR DEMO COMPLETE\n"
printf "═══════════════════════════════════════════════════════════════\n"
printf "\033[0m\n"

cat <<EOF
┌─────────────────────────────────────────────────────────────┐
│  📍 DISCOVERY                                               │
│  • EV Chargers found via geo search                        │
│  • Merchants (coffee, gym, etc.) with Green Hour offers    │
│  • Events within 2km of user location                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  ✅ VERIFICATION FLOW                                       │
│  • JWT-based short-lived verify links (10 min)             │
│  • GPS-based location verification (one-time use)          │
│  • 90/10 reward split (wallet / community pool)            │
│  • Idempotent (no double-rewards)                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  💰 WALLET & REWARDS                                        │
│  • Real-time wallet balance tracking                       │
│  • Event verification rewards                              │
│  • Purchase reconciliation (pending / matched)             │
│  • Stripe Connect payouts (test mode / simulated)          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🎉 EVENTS & CHECK-INS                                      │
│  • Public/private events with capacity                     │
│  • Join events (RSVP-style)                                │
│  • Geo verification (120m, time window enforced)           │
│  • Pool rewards for verified attendance                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🏪 MERCHANT DASHBOARD                                      │
│  • Analytics (verified sessions, rewards paid)             │
│  • Offer management (local + external feed)                │
│  • API key authentication                                  │
│  • Real-time KPI tracking                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🛡️  ANTI-FRAUD                                             │
│  • Device fingerprinting                                   │
│  • Rate limiting (verify attempts, sessions)               │
│  • Geo jump detection                                      │
│  • Risk scoring with actionable thresholds                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🔗 API ENDPOINTS                                           │
│  • GPT Actions: /v1/gpt/find_* /create_session_link       │
│  • Events: /v1/events/*                                    │
│  • Pool: /v1/pool/*                                        │
│  • Wallet: /v1/gpt/me                                      │
│  • Merchant: /v1/merchant/*                                │
└─────────────────────────────────────────────────────────────┘

EOF

printf "\033[1;36m"
printf "Next Steps:\n"
printf "  • Deploy to production with your cloud tunnel URL\n"
printf "  • Configure ChatGPT Actions with openapi-actions.yaml\n"
printf "  • Onboard merchants via merchant dashboard\n"
printf "  • Enable Stripe Connect for real payouts\n"
printf "\033[0m"

ok "Done."

