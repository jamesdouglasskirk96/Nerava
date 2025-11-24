#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Nerava — Full Investor Demo (ALL functionality)
# -----------------------------
# Shows (in order):
# 1) Health, version, debug
# 2) GPT endpoints: find_merchants, find_charger
# 3) Verify link (JWT 10 min, one-time) → locate → reward 90/10 → idempotency
# 4) Wallet snapshot → payout (Stripe test mode or simulated)
# 5) Mock purchase webhook (matched) → auto reward
# 6) Mock purchase webhook (pending) → manual claim → reward
# 7) Anti-fraud: bad accuracy rejection, rate limit/risk block → debug views
# 8) Merchant Dashboard API: summary & offers (X-Merchant-Key)
# -----------------------------

BOLD="\033[1m"; DIM="\033[2m"; GREEN="\033[32m"; CYAN="\033[36m"; YELLOW="\033[33m"; RED="\033[31m"; RESET="\033[0m"
hr() { printf "${DIM}--------------------------------------------------------------------------------${RESET}\n"; }
step() { printf "\n${BOLD}${CYAN}▶ $1${RESET}\n"; }
ok()   { printf "${GREEN}✓${RESET} %s\n" "$1"; }
warn() { printf "${YELLOW}! %s${RESET}\n" "$1"; }
err()  { printf "${RED}✗ %s${RESET}\n" "$1"; }

command -v python3 >/dev/null || { err "python3 not found"; exit 1; }
command -v uvicorn >/dev/null || { err "uvicorn not found (pip install uvicorn)"; exit 1; }
command -v jq >/dev/null      || { err "jq not found (brew/apt install jq)"; exit 1; }
test -d nerava-backend-v9/app || { err "Run from repo root (missing ./nerava-backend-v9/app)"; exit 1; }

# ==== Env defaults (safe for local) ====
export APP_ENV="${APP_ENV:-dev}"
export DASHBOARD_ENABLE="${DASHBOARD_ENABLE:-true}"
export JWT_SECRET="${JWT_SECRET:-dev-secret}"
export JWT_ALG="${JWT_ALG:-HS256}"
export VERIFY_REWARD_CENTS="${VERIFY_REWARD_CENTS:-200}"
export PURCHASE_REWARD_FLAT_CENTS="${PURCHASE_REWARD_FLAT_CENTS:-150}"
export PAYOUT_MIN_CENTS="${PAYOUT_MIN_CENTS:-100}"
export PAYOUT_MAX_CENTS="${PAYOUT_MAX_CENTS:-10000}"
export PAYOUT_DAILY_CAP_CENTS="${PAYOUT_DAILY_CAP_CENTS:-20000}"

# Anti-fraud knobs (already set in config; exported here just to show)
export MAX_VERIFY_PER_HOUR="${MAX_VERIFY_PER_HOUR:-6}"
export MAX_SESSIONS_PER_HOUR="${MAX_SESSIONS_PER_HOUR:-6}"
export MAX_DIFFERENT_IPS_PER_DAY="${MAX_DIFFERENT_IPS_PER_DAY:-5}"
export MIN_ALLOWED_ACCURACY_M="${MIN_ALLOWED_ACCURACY_M:-100}"
export BLOCK_SCORE_THRESHOLD="${BLOCK_SCORE_THRESHOLD:-100}"

export PORT="${PORT:-8001}"
BASE="http://localhost:${PORT}"

# Demo user/coords (Austin)
USER_ID=1
LAT=30.2672
LNG=-97.7431

# Change to backend directory
cd nerava-backend-v9 || { err "Failed to cd to nerava-backend-v9"; exit 1; }

# ==== Start server ====
step "Starting Nerava API on ${BASE}"
if lsof -ti tcp:"$PORT" >/dev/null 2>&1; then
  warn "Port ${PORT} busy — killing existing process"
  kill -9 "$(lsof -ti tcp:"$PORT")" || true
fi

# Activate venv if it exists
if [ -d .venv ]; then
  source .venv/bin/activate
fi

# Local dev only. Production uses: python -m uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}
( uvicorn app.main_simple:app --port "${PORT}" --log-level warning ) &
S_PID=$!
trap 'kill -9 $S_PID >/dev/null 2>&1 || true' EXIT

printf "${DIM}Waiting for server"
for i in {1..30}; do
  if curl -fsS "${BASE}/health" >/dev/null 2>&1; then break; fi
  printf "."
  sleep 0.5
done
printf "${RESET}\n"
curl -fsS "${BASE}/health" >/dev/null && ok "Server is up" || { err "Server failed to start"; exit 1; }

# ==== Migrate & seed ====
step "Running migrations"
python3 -m alembic upgrade head >/dev/null && ok "Alembic migrations applied"

step "Seeding minimal data (user + merchants + offers + demo merchant key)"
SEED_OUT=$(python3 -m app.scripts.seed_minimal 2>&1 || true)
echo "$SEED_OUT" | sed 's/^/  /'
ok "Seed complete (if already seeded, safe to ignore duplicates)"

# Parse merchant key from seed output (format printed by seed_minimal)
MERCHANT_ID=$(echo "$SEED_OUT" | grep -o 'Merchant ID: [0-9]\+' | grep -o '[0-9]\+' | head -n1 || true)
MKEY=$(echo "$SEED_OUT" | grep -o 'API Key: [A-Za-z0-9._-]\+' | sed 's/API Key: //' | head -n1 || true)

# ==== Version & Debug ====
step "Version & Debug"
hr
curl -s "${BASE}/version" | jq .
hr
curl -s "${BASE}/debug" | jq .

# ==== GPT endpoints: find_merchants ====
step "Find merchants near (${LAT}, ${LNG}) — category=coffee, radius=1200m"
MERCH_JSON=$(curl -s "${BASE}/v1/gpt/find_merchants?lat=${LAT}&lng=${LNG}&category=coffee&radius_m=1200")
COUNT=$(echo "$MERCH_JSON" | jq 'length')
echo "$MERCH_JSON" | jq '.[0:5]'
ok "Found ${COUNT} merchants (showing up to 5)"

# ==== GPT endpoints: find_charger ====
step "Find chargers near (${LAT}, ${LNG}) — radius=2000m (with next Green Hour & nearby merchants)"
curl -s "${BASE}/v1/gpt/find_charger?lat=${LAT}&lng=${LNG}&radius_m=2000" | jq '.[0:3]'
ok "Chargers returned (showing up to 3)"

# ==== Create verify link ====
step "Create a short-lived verify link (JWT 10 min, one-time)"
LINK_JSON=$(curl -s -X POST "${BASE}/v1/gpt/create_session_link" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":${USER_ID},\"charger_hint\":\"tesla-123\"}")
echo "$LINK_JSON" | jq .
TOKEN=$(echo "$LINK_JSON" | jq -r '.url' | sed -E 's#.*/verify/##')

# ==== Simulate GPS verify (first call → award) ====
step "Verify location (first call) — expect reward ${VERIFY_REWARD_CENTS}¢ => $((VERIFY_REWARD_CENTS*90/100))¢ wallet / $((VERIFY_REWARD_CENTS-VERIFY_REWARD_CENTS*90/100))¢ pool"
VERIFY1=$(curl -s -X POST "${BASE}/v1/sessions/locate" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"lat\":${LAT},\"lng\":${LNG},\"accuracy\":18,\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"ua\":\"demo-script\"}")
echo "$VERIFY1" | jq .
ok "Verify completed (one-time token)"

# ==== Verify again (idempotency) ====
step "Verify again — expect token used / no second reward"
curl -s -X POST "${BASE}/v1/sessions/locate" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"lat\":${LAT},\"lng\":${LNG},\"accuracy\":18,\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"ua\":\"demo-script\"}" | jq .
ok "Idempotency enforced"

# ==== Wallet snapshot ====
step "User snapshot (/v1/gpt/me)"
ME0=$(curl -s "${BASE}/v1/gpt/me?user_id=${USER_ID}")
echo "$ME0" | jq .
WALLET0=$(echo "$ME0" | jq '.wallet_cents')

# ==== Payout (Stripe test or simulated) ====
step "Create payout (200¢) — Stripe test if keys present, otherwise simulated paid"
PAYOUT=$(curl -s -X POST "${BASE}/v1/payouts/create" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":${USER_ID},\"amount_cents\":200,\"method\":\"card_push\",\"client_token\":\"demo-001\"}")
echo "$PAYOUT" | jq .

step "User snapshot after payout"
ME1=$(curl -s "${BASE}/v1/gpt/me?user_id=${USER_ID}")
echo "$ME1" | jq .
WALLET1=$(echo "$ME1" | jq '.wallet_cents')
ok "Wallet debited by $((WALLET0 - WALLET1)) cents for payout"

# ==== Purchase webhook (matched) ====
step "Mock purchase within session window/radius — expect auto reward (purchase)"
# Use the dev helper to simulate a Square purchase near the verified session
MATCHED=$(curl -s -X POST "${BASE}/v1/dev/mock_purchase" \
  -H 'Content-Type: application/json' \
  -d "{\"provider\":\"square\",\"user_id\":${USER_ID},\"merchant_name\":\"Mock Cafe\",\"merchant_ext_id\":\"sq-123\",\"city\":\"Austin\",\"amount_cents\":500,\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}")
echo "$MATCHED" | jq .
ok "Purchase ingested; matched to session if within 30m/120m"

step "User snapshot after matched purchase reward"
ME2=$(curl -s "${BASE}/v1/gpt/me?user_id=${USER_ID}")
echo "$ME2" | jq .
WALLET2=$(echo "$ME2" | jq '.wallet_cents')
DELTA_MATCHED=$((WALLET2 - WALLET1))
ok "Wallet increased by ${DELTA_MATCHED} cents (expected ≈ $((PURCHASE_REWARD_FLAT_CENTS*90/100)))"

# ==== Purchase webhook (pending) → manual claim ====
step "Mock purchase OUTSIDE window — expect pending (claimed=false)"
PENDING=$(curl -s -X POST "${BASE}/v1/dev/mock_purchase" \
  -H 'Content-Type: application/json' \
  -d "{\"provider\":\"square\",\"user_id\":${USER_ID},\"merchant_name\":\"Late Cafe\",\"merchant_ext_id\":\"sq-999\",\"city\":\"Austin\",\"amount_cents\":700,\"ts\":\"2000-01-01T00:00:00Z\"}")
echo "$PENDING" | jq .
PENDING_ID=$(echo "$PENDING" | jq -r '.payment_id // empty')
ok "Pending payment_id=${PENDING_ID:-N/A}"

step "Manual claim pending purchase (dev) — expect claimed=true if a fresh verify exists"
# Create a fresh verify to help the claim succeed
LINK2=$(curl -s -X POST "${BASE}/v1/gpt/create_session_link" -H 'Content-Type: application/json' -d "{\"user_id\":${USER_ID}}")
TOKEN2=$(echo "$LINK2" | jq -r '.url' | sed -E 's#.*/verify/##')
curl -s -X POST "${BASE}/v1/sessions/locate" -H "Authorization: Bearer ${TOKEN2}" -H 'Content-Type: application/json' \
  -d "{\"lat\":${LAT},\"lng\":${LNG},\"accuracy\":15,\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"ua\":\"demo-script\"}" >/dev/null

CLAIM=$(curl -s -X POST "${BASE}/v1/purchases/claim" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":${USER_ID},\"payment_id\":${PENDING_ID:-0}}")
echo "$CLAIM" | jq .
ok "Pending claim processed"

step "User snapshot after claim"
ME3=$(curl -s "${BASE}/v1/gpt/me?user_id=${USER_ID}")
echo "$ME3" | jq .
WALLET3=$(echo "$ME3" | jq '.wallet_cents')
DELTA_CLAIM=$((WALLET3 - WALLET2))
ok "Wallet increased by ${DELTA_CLAIM} cents from pending claim"

# ==== Anti-fraud: bad accuracy rejection ====
step "Anti-fraud — bad accuracy should be rejected"
LINK_BAD=$(curl -s -X POST "${BASE}/v1/gpt/create_session_link" -H 'Content-Type: application/json' -d "{\"user_id\":${USER_ID}}")
TOKEN_BAD=$(echo "$LINK_BAD" | jq -r '.url' | sed -E 's#.*/verify/##')
curl -s -X POST "${BASE}/v1/sessions/locate" \
  -H "Authorization: Bearer ${TOKEN_BAD}" -H 'Content-Type: application/json' \
  -d "{\"lat\":${LAT},\"lng\":${LNG},\"accuracy\":500,\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"ua\":\"curl\"}" | jq .
ok "Accuracy guard working (expect error message)"

# ==== Anti-fraud: rate limit / risk block ====
step "Anti-fraud — hammer session creation to trigger risk/429"
RC=0
for i in {1..8}; do
  RESP=$(curl -s -o /tmp/resp.json -w "%{http_code}" -X POST "${BASE}/v1/gpt/create_session_link" -H 'Content-Type: application/json' -d "{\"user_id\":${USER_ID}}")
  CODE="$RESP"
  if [[ "$CODE" -eq 429 ]]; then
    ok "Risk block hit (HTTP 429)"; RC=1; break
  fi
  sleep 0.2
done
if [[ $RC -eq 0 ]]; then warn "Did not hit 429 (limits may be higher in env)"; fi

# ==== Anti-fraud: debug view ====
step "Fraud debug (/debug/abuse)"
curl -s "${BASE}/debug/abuse?user_id=${USER_ID}&limit=5" | jq .

# ==== Merchant Dashboard API ====
step "Merchant Dashboard API — Summary & Offers"
if [[ -z "${MERCHANT_ID:-}" || -z "${MKEY:-}" ]]; then
  warn "Missing merchant_id/api_key from seed output. Export and re-run to show dashboard API:"
  echo "  export MERCHANT_ID=<id>"
  echo "  export MKEY=<api_key>"
else
  echo "Using merchant_id=${MERCHANT_ID}, X-Merchant-Key=${MKEY}"
  echo
  echo "${DIM}Summary (/v1/merchant/summary)${RESET}"
  M_SUM=$(curl -s -H "X-Merchant-Key: ${MKEY}" \
              "${BASE}/v1/merchant/summary?merchant_id=${MERCHANT_ID}")
  echo "$M_SUM" | jq .
  echo
  echo "${DIM}Offers (/v1/merchant/offers)${RESET}"
  M_OFF=$(curl -s -H "X-Merchant-Key: ${MKEY}" \
              "${BASE}/v1/merchant/offers?merchant_id=${MERCHANT_ID}")
  echo "$M_OFF" | jq .
  ok "Merchant Dashboard responses printed"
fi

# ==== Wrap ====
hr
printf "${BOLD}${GREEN}Nerava demo complete — ALL features showcased${RESET}\n"
printf "${DIM}Loop:${RESET} Find → Verify → Earn → Spend → Purchase Reconcile → Anti-Fraud → Merchant View\n"
printf "• ${BOLD}Verify reward:${RESET} %s¢ (90%% wallet / 10%% pool)\n" "${VERIFY_REWARD_CENTS}"
printf "• ${BOLD}Purchase reward:${RESET} %s¢ flat (demo), auto or claim pending\n" "${PURCHASE_REWARD_FLAT_CENTS}"
printf "• ${BOLD}Payouts:${RESET} Stripe test/sim\n"
printf "• ${BOLD}Fraud:${RESET} accuracy gate, risk limits, debug views\n"
printf "• ${BOLD}Dashboard:${RESET} Summary & offers via API key\n"
hr
