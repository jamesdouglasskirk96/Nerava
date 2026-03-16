#!/bin/bash
# Monitor seed jobs, auto-start merchant seed after chargers complete.
# Runs for up to 6 hours, checking every 10 minutes.

SEED_KEY="787044b63251814c8dd160437b395a77fa6e162bdc53e24320cd84d14fa5ed86"
API="https://api.nerava.network/v1/admin/seed-key"
LOG="/tmp/nerava_seed_monitor.log"
MAX_CHECKS=36  # 36 * 10min = 6 hours
MERCHANT_STARTED=0

echo "$(date) - Seed monitor started" | tee -a "$LOG"

for i in $(seq 1 $MAX_CHECKS); do
  sleep 600  # 10 minutes

  # Health check
  health=$(curl -s --max-time 10 https://api.nerava.network/healthz 2>&1)
  if ! echo "$health" | grep -q '"ok":true'; then
    echo "$(date) - WARNING: Health check failed: $health" | tee -a "$LOG"
  fi

  # Get seed status
  seed_result=$(curl -s --max-time 15 "$API/status" -H "X-Seed-Key: $SEED_KEY" 2>&1)

  # Parse charger job status
  charger_status=$(echo "$seed_result" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    jobs=[v for v in d.get('jobs',{}).values() if v['type']=='chargers']
    if jobs:
        j=jobs[-1]
        p=j.get('progress',{})
        print(f\"{j['status']}|{p.get('current_state','?')}|{p.get('total_fetched',0)}\")
        if j.get('error'): print(f\"ERROR:{j['error']}\", file=sys.stderr)
    else:
        print('none')
except: print('parse_error')
" 2>/tmp/seed_charger_err.txt)

  charger_st=$(echo "$charger_status" | cut -d'|' -f1)
  charger_state=$(echo "$charger_status" | cut -d'|' -f2)
  charger_fetched=$(echo "$charger_status" | cut -d'|' -f3)

  # Parse merchant job status
  merchant_status=$(echo "$seed_result" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    jobs=[v for v in d.get('jobs',{}).values() if v['type']=='merchants']
    if jobs:
        j=jobs[-1]
        p=j.get('progress',{})
        print(f\"{j['status']}|{p.get('cells_done',0)}|{p.get('total_cells',0)}\")
        if j.get('error'): print(f\"ERROR:{j['error']}\", file=sys.stderr)
    else:
        print('none')
except: print('parse_error')
" 2>/tmp/seed_merchant_err.txt)

  merchant_st=$(echo "$merchant_status" | cut -d'|' -f1)
  merchant_done=$(echo "$merchant_status" | cut -d'|' -f2)
  merchant_total=$(echo "$merchant_status" | cut -d'|' -f3)

  # Get counts
  stats=$(curl -s --max-time 10 "$API/stats" -H "X-Seed-Key: $SEED_KEY" 2>&1)
  counts=$(echo "$stats" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(f\"{d.get('chargers',0)} chargers, {d.get('merchants',0)} merchants, {d.get('junctions',0)} junctions\")
except: print('?')
" 2>/dev/null)

  echo "$(date) - [Check $i/$MAX_CHECKS] Chargers: $charger_st (state=$charger_state, fetched=$charger_fetched) | Merchants: $merchant_st ($merchant_done/$merchant_total) | DB: $counts" | tee -a "$LOG"

  # If charger seed completed and merchant seed not started yet, start it
  if [ "$charger_st" = "completed" ] && [ "$MERCHANT_STARTED" = "0" ]; then
    echo "$(date) - Charger seed completed! Starting merchant seed..." | tee -a "$LOG"
    merchant_resp=$(curl -s -X POST "$API/merchants" \
      -H "X-Seed-Key: $SEED_KEY" \
      -H "Content-Type: application/json" \
      -d '{}' 2>&1)
    echo "$(date) - Merchant seed response: $merchant_resp" | tee -a "$LOG"
    MERCHANT_STARTED=1
  fi

  # If charger seed failed, try restarting
  if [ "$charger_st" = "failed" ] && [ "$MERCHANT_STARTED" = "0" ]; then
    err=$(cat /tmp/seed_charger_err.txt 2>/dev/null)
    echo "$(date) - Charger seed FAILED: $err. Restarting..." | tee -a "$LOG"
    restart_resp=$(curl -s -X POST "$API/chargers" \
      -H "X-Seed-Key: $SEED_KEY" \
      -H "Content-Type: application/json" \
      -d '{}' 2>&1)
    echo "$(date) - Restart response: $restart_resp" | tee -a "$LOG"
  fi

  # If merchant seed failed, try restarting
  if [ "$merchant_st" = "failed" ]; then
    err=$(cat /tmp/seed_merchant_err.txt 2>/dev/null)
    echo "$(date) - Merchant seed FAILED: $err. Restarting..." | tee -a "$LOG"
    restart_resp=$(curl -s -X POST "$API/merchants" \
      -H "X-Seed-Key: $SEED_KEY" \
      -H "Content-Type: application/json" \
      -d '{}' 2>&1)
    echo "$(date) - Restart response: $restart_resp" | tee -a "$LOG"
  fi

  # If both completed, we're done
  if [ "$charger_st" = "completed" ] && [ "$merchant_st" = "completed" ]; then
    echo "$(date) - Both seeds completed! Final stats: $counts" | tee -a "$LOG"
    exit 0
  fi
done

echo "$(date) - Monitor timeout after 6 hours. Final stats: $counts" | tee -a "$LOG"
