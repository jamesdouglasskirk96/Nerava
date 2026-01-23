# Nerava Production Quality Gate - Task List

**Generated**: 2025-12-25
**Status**: 28 items total, 6 blocking production

---

## P0 - Critical (Must Fix Before Production)

### P0-1: Verify JWT_SECRET Configuration
- [ ] Check App Runner env var: `JWT_SECRET`
- [ ] Verify it is NOT "dev-secret"
- [ ] Verify it does NOT match DATABASE_URL
- [ ] If invalid, generate new: `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`
- [ ] Update SSM: `/nerava/prod/JWT_SECRET`
- [ ] Redeploy App Runner

**Risk**: Auth bypass if using weak secret
**LOE**: 15 minutes
**Owner**: DevOps

### P0-2: Set TOKEN_ENCRYPTION_KEY
- [ ] Generate Fernet key: `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`
- [ ] Store in SSM: `/nerava/prod/TOKEN_ENCRYPTION_KEY`
- [ ] Update App Runner service configuration
- [ ] Verify startup succeeds (`/healthz` returns 200)

**Risk**: OAuth tokens stored unencrypted
**LOE**: 15 minutes
**Owner**: DevOps

### P0-3: Set STRIPE_WEBHOOK_SECRET
- [ ] Get webhook secret from Stripe Dashboard → Webhooks → Signing secret
- [ ] Store in SSM: `/nerava/prod/STRIPE_WEBHOOK_SECRET`
- [ ] Update App Runner service configuration
- [ ] Test webhook via Stripe CLI: `stripe trigger payment_intent.succeeded`

**Risk**: Webhook spoofing allows fake payments
**LOE**: 15 minutes
**Owner**: DevOps

### P0-4: Configure CloudWatch Alarms
- [ ] Create SNS topic: `nerava-alerts`
- [ ] Subscribe email/PagerDuty to topic
- [ ] Create alarm: HealthCheckFailed (< 1 for 2 periods)
- [ ] Create alarm: HighErrorRate (> 10 5XX/5min)
- [ ] Create alarm: HighLatency (P95 > 2000ms)
- [ ] Test by triggering a 500 error

**Risk**: Outages go undetected
**LOE**: 2 hours
**Owner**: DevOps

### P0-5: Verify DEMO_MODE=false
- [ ] Check App Runner env var: `DEMO_MODE`
- [ ] Ensure it is `false` or not set
- [ ] Test: Demo login should fail on production URL
- [ ] If set to `true`, update and redeploy

**Risk**: Auth bypass via demo mode
**LOE**: 15 minutes
**Owner**: DevOps

### P0-6: Implement Apple Sign-In
- [ ] Create `POST /v1/auth/apple` endpoint in `auth_domain.py`
- [ ] Implement Apple JWT validation (fetch Apple public keys)
- [ ] Create user or log in existing user
- [ ] Update `login.js` to call new endpoint
- [ ] Test on iOS device with Apple ID

**Risk**: iOS users cannot authenticate
**LOE**: 4 hours
**Owner**: Backend

---

## P1 - High Priority (Week 1)

### P1-1: Configure Twilio for OTP
- [ ] Get Twilio Account SID and Auth Token
- [ ] Set `TWILIO_ACCOUNT_SID` in SSM
- [ ] Set `TWILIO_AUTH_TOKEN` in SSM
- [ ] Set `TWILIO_PHONE_NUMBER` in SSM
- [ ] Test OTP send/verify flow

**Risk**: Phone authentication broken
**LOE**: 1 hour
**Owner**: DevOps

### P1-2: Configure Google SSO
- [ ] Get Google OAuth Client ID from GCP Console
- [ ] Set `GOOGLE_CLIENT_ID` in SSM
- [ ] Update App Runner configuration
- [ ] Test Google sign-in button

**Risk**: Google authentication disabled
**LOE**: 30 minutes
**Owner**: DevOps

### P1-3: Configure Square OAuth
- [ ] Get Square Production credentials from Square Dashboard
- [ ] Set `SQUARE_APPLICATION_ID_PRODUCTION` in SSM
- [ ] Set `SQUARE_APPLICATION_SECRET_PRODUCTION` in SSM
- [ ] Set `SQUARE_ENV=production`
- [ ] Test merchant onboarding flow

**Risk**: Merchant Square connection blocked
**LOE**: 1 hour
**Owner**: DevOps

### P1-4: Add CSRF Protection
- [ ] Add CSRF middleware to FastAPI
- [ ] Generate CSRF token on login
- [ ] Include token in auth cookie
- [ ] Validate token on state-changing requests
- [ ] Update frontend to send token

**Risk**: Session hijack via CSRF
**LOE**: 4 hours
**Owner**: Backend

### P1-5: Remove wallet GET user_id Parameter
- [ ] Update `GET /v1/wallet` to use auth only
- [ ] Remove `user_id` query parameter
- [ ] Update frontend callers
- [ ] Add deprecation warning if param is passed

**Risk**: Information disclosure
**LOE**: 1 hour
**Owner**: Backend

### P1-6: Deploy CloudFront CDN
- [ ] Create CloudFront distribution
- [ ] Configure S3 origin
- [ ] Set up SSL certificate
- [ ] Update DNS/CNAME
- [ ] Invalidate cache after frontend deploys

**Risk**: S3 direct access has higher latency
**LOE**: 2 hours
**Owner**: DevOps

### P1-7: Add Webhook Timestamp Validation
- [ ] Parse `Stripe-Signature` timestamp
- [ ] Reject webhooks older than 5 minutes
- [ ] Log rejected webhook attempts
- [ ] Add metric for monitoring

**Risk**: Webhook replay window
**LOE**: 2 hours
**Owner**: Backend

### P1-8: Create CI/CD Pipeline
- [ ] Set up GitHub Actions workflow
- [ ] Build and test on PR
- [ ] Push to ECR on main merge
- [ ] Trigger App Runner deployment
- [ ] Add status badges to README

**Risk**: Manual deploys are error-prone
**LOE**: 4 hours
**Owner**: DevOps

---

## P2 - Medium Priority (Week 2-3)

### P2-1: Configure Smartcar Integration
- [ ] Get Smartcar credentials from dashboard
- [ ] Set `SMARTCAR_CLIENT_ID`
- [ ] Set `SMARTCAR_CLIENT_SECRET`
- [ ] Set `SMARTCAR_REDIRECT_URI`
- [ ] Test vehicle linking flow

**LOE**: 2 hours

### P2-2: Apple Wallet Cert Deployment
- [ ] Obtain Apple Developer cert for Wallet
- [ ] Export as P12 file
- [ ] Store cert in secure location (S3 or SSM)
- [ ] Set `APPLE_WALLET_SIGNING_ENABLED=true`
- [ ] Configure all APPLE_WALLET_* env vars
- [ ] Test pass generation

**LOE**: 4 hours

### P2-3: Configure Stripe Payment Flow
- [ ] Set `STRIPE_SECRET_KEY`
- [ ] Configure Stripe checkout session
- [ ] Set up webhook endpoint
- [ ] Test merchant Nova purchase

**LOE**: 2 hours

### P2-4: Add Sentry Error Tracking
- [ ] Create Sentry project
- [ ] Install `sentry-sdk[fastapi]`
- [ ] Initialize in `main_simple.py`
- [ ] Set `SENTRY_DSN` env var
- [ ] Test error reporting

**LOE**: 2 hours

### P2-5: Create CloudWatch Dashboard
- [ ] Create dashboard for Nerava
- [ ] Add request count widget
- [ ] Add latency P50/P95 widget
- [ ] Add error count widget
- [ ] Add database connections widget

**LOE**: 2 hours

### P2-6: Enable HubSpot Production
- [ ] Get HubSpot API token
- [ ] Set `HUBSPOT_ENABLED=true`
- [ ] Set `HUBSPOT_SEND_LIVE=true`
- [ ] Set `HUBSPOT_PRIVATE_APP_TOKEN`
- [ ] Verify events flowing to HubSpot

**LOE**: 1 hour

### P2-7: Google Wallet Integration
- [ ] Get Google Wallet API access
- [ ] Configure service account
- [ ] Implement pass creation endpoint
- [ ] Add to wallet UI

**LOE**: 4 hours

### P2-8: Audit Raw SQL Queries
- [ ] Search for `text()` SQL calls
- [ ] Verify all use parameterized queries
- [ ] Add input validation where missing
- [ ] Document any exceptions

**LOE**: 4 hours

---

## P3 - Low Priority (Backlog)

- [ ] P3-1: Add APM (X-Ray or Datadog)
- [ ] P3-2: Set up uptime monitoring (StatusCake)
- [ ] P3-3: Load testing with k6
- [ ] P3-4: Migrate secrets to Secrets Manager
- [ ] P3-5: Remove 49 TODO/FIXME comments
- [ ] P3-6: Consolidate duplicate Settings classes

---

## Verification Commands

```bash
# Check P0 status
curl -s https://your-app.awsapprunner.com/healthz | jq
curl -s https://your-app.awsapprunner.com/readyz | jq

# Check CloudWatch alarms
aws cloudwatch describe-alarms --alarm-names nerava-healthcheck nerava-high-error-rate

# Check App Runner config
aws apprunner describe-service --service-arn YOUR_SERVICE_ARN | jq '.Service.SourceConfiguration'

# Test demo mode is disabled
curl -X POST https://your-app.awsapprunner.com/v1/auth/dev_login \
  -H "Content-Type: application/json" \
  -d '{}'
# Should return 401 or 404 in production
```

---

## Progress Tracking

| Phase | Items | Done | Remaining |
|-------|-------|------|-----------|
| P0 | 6 | 0 | 6 |
| P1 | 8 | 0 | 8 |
| P2 | 8 | 0 | 8 |
| P3 | 6 | 0 | 6 |
| **Total** | **28** | **0** | **28** |

---

Last Updated: 2025-12-25
