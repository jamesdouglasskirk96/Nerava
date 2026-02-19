# V0 Web-First EV Arrival — Rollout Steps

---

## Pre-Flight (Before Day 1)

- [ ] Verify all EV Arrival tables exist in staging DB: `arrival_sessions`, `merchant_notification_config`, `merchant_pos_credentials`, `billing_events`
- [ ] Verify pilot merchant data: Asadas Grill has `ordering_url` set
- [ ] Verify Twilio SMS is working: send test SMS from staging backend
- [ ] Verify driver OTP auth works on staging: phone login → token → API call
- [ ] Confirm 5 EVArrival components exist at `apps/driver/src/components/EVArrival/`
- [ ] Have a test phone number ready for merchant SMS notifications

---

## Day 1: Backend + Driver App Wiring

### Hour 1-2: Backend Tasks (Cursor Tasks 1-4)

```bash
# 1. Run Cursor Task 1: Session expiry background task
# 2. Run Cursor Task 2: Web confirm support
# 3. Run Cursor Task 3: Billing CSV export
# 4. Run Cursor Task 4: Daily rate limit
```

**Verify backend locally:**
```bash
cd backend
uvicorn app.main:app --port 8001 --reload

# Test session expiry (check logs for "Expired N sessions")
# Test web confirm
curl -X POST http://localhost:8001/v1/arrival/test-session-id/confirm-arrival \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"web_confirm": true, "lat": 30.2672, "lng": -97.7431, "accuracy_m": 50}'

# Test billing export
curl http://localhost:8001/v1/admin/billing-export?month=2026-02 \
  -H "Authorization: Bearer {admin_token}"
```

### Hour 3-4: Driver App Wiring (Cursor Tasks 5-8)

```bash
# 5. Run Cursor Task 5: Wire EVArrival into DriverHome
# 6. Run Cursor Task 6: Add /arrival route
# 7. Run Cursor Task 7: Add "Add EV Arrival" to merchant detail
# 8. Run Cursor Task 8: Web geolocation + polling
```

**Verify driver app locally:**
```bash
cd apps/driver
npm run dev  # port 5173

# Open http://localhost:5173
# 1. Login via OTP
# 2. See merchant cards with "Add EV Arrival" button
# 3. Tap → ModeSelector → select mode → confirm
# 4. Active session screen renders with ordering link
# 5. "I'm at the charger" button appears (web mode)
```

### Hour 5: Run Codex Test Suites 1-4

```bash
cd backend

# Run backend tests
pytest tests/test_session_expiry.py -v
pytest tests/test_web_confirm_arrival.py -v
pytest tests/test_billing_export.py -v
pytest tests/test_arrival_rate_limit.py -v
```

Fix any failures before proceeding to Day 2.

---

## Day 2: Polish + Merchant Portal + Deploy

### Hour 1-2: Merchant Portal + Polish (Cursor Tasks 9-11)

```bash
# 9. Run Cursor Task 9: Hide email toggle + add export
# 10. Run Cursor Task 10: Notification service email warning
# 11. Run Cursor Task 11: Post-claim Google Maps instructions
```

**Verify merchant portal locally:**
```bash
cd apps/merchant
npm run dev  # port 5174

# Open http://localhost:5174
# 1. Navigate to EVArrivals tab
# 2. Email toggle shows "Coming soon"
# 3. "Download Billing CSV" button visible
# 4. Complete a claim flow → Google Maps instructions appear
```

### Hour 3: Full End-to-End Manual Test

Run this test against local dev (backend + driver app + merchant portal all running):

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open driver app, login via OTP | Dashboard loads, merchant cards visible |
| 2 | Tap "Add EV Arrival" on Asadas Grill card | ModeSelector opens |
| 3 | Select "EV Curbside", confirm | Session created, active session screen shown |
| 4 | Tap "Order from Asadas" link | Toast ordering page opens in new tab |
| 5 | Return to Nerava, enter order # "1234" | Order bound, status = awaiting_arrival |
| 6 | Tap "I'm at the charger" | Browser requests geolocation permission |
| 7 | Allow geolocation | Arrival confirmed, merchant notified |
| 8 | Check test phone | SMS received with order details |
| 9 | Reply "DONE 1234" to SMS | — |
| 10 | Check driver app (within 10s) | Completion screen appears |
| 11 | Tap thumbs-up, add comment | Feedback saved |
| 12 | Check billing_events table | Row exists with correct amounts |
| 13 | Open merchant portal → EVArrivals | Completed arrival visible in list |
| 14 | Download billing CSV | CSV file downloads with correct data |

### Hour 4: Run Integration Tests + Deploy

```bash
# Run full integration test suite
cd backend
pytest tests/integration/test_ev_arrival_flow.py -v
pytest tests/test_notification_config.py -v

# If all pass, deploy to staging
```

### Staging Deploy

```bash
# Build and deploy backend
cd backend
# Use existing deploy script
python scripts/deploy_aws.py --env staging

# Build and deploy driver app
cd apps/driver
npm run build
# Deploy to S3/CloudFront (existing script)
cd ../../
./scripts/deploy-frontend-s3.sh driver staging

# Build and deploy merchant portal
cd apps/merchant
npm run build
./scripts/deploy-frontend-s3.sh merchant staging
```

### Staging Smoke Test

Repeat the E2E manual test on staging:
- Driver app: `https://staging.nerava.network`
- Merchant portal: `https://staging-merchant.nerava.network`
- Backend: `https://staging-api.nerava.network`

### Production Deploy

After staging passes:

```bash
# Deploy backend to production
python scripts/deploy_aws.py --env prod

# Deploy frontends to production
./scripts/deploy-frontend-s3.sh driver prod
./scripts/deploy-frontend-s3.sh merchant prod
```

### Production Verification

| Check | Command/Action |
|-------|---------------|
| Backend health | `curl https://api.nerava.network/v1/health` |
| Driver app loads | Open `https://app.nerava.network` |
| Merchant portal loads | Open `https://merchant.nerava.network` |
| OTP works | Login with test phone number |
| Session expiry running | Check backend logs for expiry task output |
| SMS works | Create test arrival → verify SMS received |

---

## Post-Deploy Monitoring (Day 2 evening + Day 3)

### PostHog Dashboard
Create a PostHog dashboard with these metrics:
- `ev_arrival.created` — count per day
- `ev_arrival.completed` — count per day
- `ev_arrival.completed` / `ev_arrival.created` — completion rate
- `ev_arrival.web_confirm` — count (web vs native usage)
- `ev_arrival.expired` — count (are sessions timing out?)
- `ev_arrival.billing_export` — admin usage
- `merchant_funnel.gmb_visit` — Google Maps referrals

### Alerts to Set
- **Session expiry task not running:** If 0 `ev_arrival.expired` events for 24 hours and there are sessions past expires_at
- **SMS delivery failure:** Monitor Twilio dashboard for failed deliveries
- **High error rate:** 5xx errors on arrival endpoints > 5% in 15 min window

### Rollback Plan
If critical issues are found:
1. **Backend:** Redeploy previous version via App Runner revision rollback
2. **Frontend:** S3/CloudFront — revert to previous build artifacts
3. **Database:** No migrations to roll back (all tables already exist)
4. **Feature kill switch:** Set `EV_ARRIVAL_ENABLED=false` env var (add a check in `arrival.py` create endpoint)

---

## Merchant Onboarding (Day 3+)

### First 5 Merchants
1. Generate preview URLs: `POST /v1/merchant/funnel/resolve` for each merchant
2. Text preview links to merchant owners via `POST /v1/merchant/funnel/text-preview-link`
3. Follow up with phone call (Calendly link is on the preview page)
4. Walk them through: claim → set SMS phone → test arrival notification

### Track Onboarding Funnel
| Stage | PostHog Event |
|-------|---------------|
| Preview page viewed | `merchant_funnel.preview_view` |
| Claim started | `merchant.claim_started` |
| Phone verified | `merchant.phone_verified` |
| Claim completed | `merchant.claim_completed` |
| First arrival received | `ev_arrival.merchant_notified` (first per merchant) |
| First DONE reply | `ev_arrival.merchant_confirmed` (first per merchant) |

---

## Success Criteria (Week 1)

| Metric | Target |
|--------|--------|
| Merchants onboarded | >= 3 |
| Driver sessions created | >= 10 |
| Sessions completed | >= 5 (50% completion rate) |
| SMS notifications delivered | 100% of confirmed arrivals |
| Billing events created | >= 3 with non-zero amounts |
| Zero critical bugs | No data loss, no stuck sessions, no billing errors |
