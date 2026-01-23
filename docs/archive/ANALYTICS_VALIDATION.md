# Analytics Validation Guide

This document provides step-by-step instructions to validate that analytics events are being captured correctly across all 5 components of the Nerava stack.

## Prerequisites

1. PostHog account set up with project API key
2. HubSpot account set up with private app access token (optional for basic validation)
3. Docker Compose environment running
4. Environment variables configured:
   - `POSTHOG_KEY` (required)
   - `POSTHOG_HOST` (default: `https://app.posthog.com`)
   - `HUBSPOT_ACCESS_TOKEN` (optional)
   - `ANALYTICS_ENABLED=true` (default: `true`)
   - `ENV=dev` (or `staging`/`prod`)

## Validation Steps

### 1. Start the Stack

```bash
docker compose up --build
```

Wait for all services to be healthy. Verify all containers are running:
- `nerava-backend`
- `nerava-landing`
- `nerava-driver`
- `nerava-merchant`
- `nerava-admin`
- `nerava-proxy`

### 2. Landing Page → Driver App Flow

#### 2.1 Landing Page Events

1. Open `http://localhost` in browser
2. Open PostHog Live Events in another tab
3. Navigate around the landing page
4. **Verify in PostHog:**
   - Event: `landing.page.view`
   - Properties include: `app: 'landing'`, `env: 'dev'`, `path`, `referrer`
   - UTM params captured if present in URL

5. Click "Open Nerava" CTA button
6. **Verify in PostHog:**
   - Event: `landing.cta.click`
   - Properties include: `cta_id: 'open_driver'`, `cta_text`, `href`
   - UTM params preserved

#### 2.2 Driver App Session Start

1. Driver app should load at `http://localhost/app/`
2. **Verify in PostHog:**
   - Event: `driver.session.start`
   - Properties include: `src: 'landing'`, `cta: 'open_driver'`
   - UTM params from landing page preserved

### 3. Driver OTP Flow

#### 3.1 OTP Start

1. In driver app, trigger OTP modal (click "Activate Exclusive" or similar)
2. Enter phone number and click "Send code"
3. **Verify in PostHog:**
   - Frontend event: `driver.otp.start`
   - Properties include: `phone_last4` (NOT full phone)
   - Backend event: `server.driver.otp.start`
   - Backend event includes: `request_id`, `ip`, `user_agent`

#### 3.2 OTP Verify Success

1. Enter OTP code (or use stub provider code)
2. **Verify in PostHog:**
   - Frontend event: `driver.otp.verify.success`
   - Properties include: `driver_id`, `phone_last4`
   - Backend event: `server.driver.otp.verify.success`
   - Backend event includes: `user_id`, `request_id`
   - User identified: `distinct_id` switches from anonymous to `driver_id`

3. **Verify in HubSpot (if configured):**
   - Contact created/updated with phone number
   - Properties: `role: 'driver'`, `last_login_at`, `source: 'otp'`

### 4. Intent Capture Flow

1. In driver app, ensure location permission is granted
2. App should automatically capture intent when location is available
3. **Verify in PostHog:**
   - Frontend event: `driver.intent.capture.request`
   - Frontend event: `driver.intent.capture.success` (when response received)
   - Backend event: `server.driver.intent.capture.success`
   - Backend event includes: `session_id`, `location_accuracy`, `merchant_count`

### 5. Exclusive Activation Flow

#### 5.1 Activation Click

1. Click "Activate Exclusive" button on a merchant card
2. **Verify in PostHog:**
   - Event: `driver.exclusive.activate.click`
   - Properties include: `merchant_id`

#### 5.2 Activation Blocked (Outside Radius)

1. If not within charger radius, activation should be blocked
2. **Verify in PostHog:**
   - Frontend event: `driver.exclusive.activate.blocked_outside_radius`
   - Backend event: `server.driver.exclusive.activate.blocked`
   - Properties include: `distance_m`, `required_radius_m`

#### 5.3 Activation Success

1. Ensure you're within charger radius (or use demo mode)
2. Activate exclusive successfully
3. **Verify in PostHog:**
   - Frontend event: `driver.exclusive.activate.success`
   - Backend event: `server.driver.exclusive.activate.success`
   - Properties include: `merchant_id`, `exclusive_id`, `session_id`

### 6. Exclusive Completion Flow

1. Complete an exclusive session (click "Complete" or similar)
2. **Verify in PostHog:**
   - Frontend event: `driver.exclusive.complete.click`
   - Frontend event: `driver.exclusive.complete.success`
   - Backend event: `server.driver.exclusive.complete.success`
   - Properties include: `session_id`, `duration_seconds`

3. **Verify in HubSpot (if configured):**
   - Driver contact updated: `exclusive_completions++`, `last_exclusive_completed_at`
   - If first completion: `lifecycle_stage: 'engaged_driver'`

### 7. Merchant Portal Flow

#### 7.1 Merchant Login

1. Open `http://localhost/merchant/`
2. Log in (if login component exists)
3. **Verify in PostHog:**
   - Event: `merchant.login.success` (or `merchant.login.fail`)
   - User identified: `distinct_id` switches to `merchant_user_id`

#### 7.2 Create Exclusive

1. Navigate to Exclusives page
2. Click "Create Exclusive"
3. **Verify in PostHog:**
   - Event: `merchant.exclusive.create.open`
4. Fill form and submit
5. **Verify in PostHog:**
   - Frontend event: `merchant.exclusive.create.submit.success`
   - Backend event: `server.merchant.exclusive.create`
   - Properties include: `exclusive_id`, `merchant_id`

#### 7.3 Toggle Exclusive

1. Toggle an exclusive on/off
2. **Verify in PostHog:**
   - Frontend event: `merchant.exclusive.toggle.on` or `merchant.exclusive.toggle.off`
   - Backend event: `server.merchant.exclusive.toggle`
   - Properties include: `enabled: true/false`

3. **Verify in HubSpot (if configured):**
   - Merchant contact updated: `has_active_exclusive: true` (when enabled)

#### 7.4 Brand Image Upload

1. Upload a brand image (if feature exists)
2. **Verify in PostHog:**
   - Frontend event: `merchant.brand_image.upload.success`
   - Backend event: `server.merchant.brand_image.set`

#### 7.5 Analytics View

1. Navigate to Overview/Analytics page
2. **Verify in PostHog:**
   - Event: `merchant.analytics.view`

### 8. Admin Portal Flow

#### 8.1 Admin Login

1. Open `http://localhost/admin/`
2. Log in (if login component exists)
3. **Verify in PostHog:**
   - Event: `admin.login.success` (or `admin.login.fail`)

#### 8.2 Demo Location Override

1. Navigate to Demo/Overrides page
2. Set demo location override
3. **Verify in PostHog:**
   - Frontend event: `admin.demo_location.override.set.success`
   - Backend event: `server.admin.demo_location.override`
   - Properties include: `latitude`, `longitude`, `charger_id`

#### 8.3 Admin Exclusive Toggle

1. Toggle an exclusive via admin panel
2. **Verify in PostHog:**
   - Frontend event: `admin.exclusive.toggle.on` or `admin.exclusive.toggle.off`
   - Backend event: `server.admin.exclusive.toggle`

#### 8.4 Audit Log View

1. Navigate to Audit Log page
2. **Verify in PostHog:**
   - Frontend event: `admin.audit_log.view`
   - Backend event: `server.admin.audit_log.view`
   - Properties include: `filter` (if filter applied)

#### 8.5 Merchants View

1. Navigate to Merchants page
2. **Verify in PostHog:**
   - Event: `admin.merchants.view`

### 9. Correlation Validation

For any event chain (e.g., OTP start → verify → intent capture → exclusive activate):

1. **Check request_id correlation:**
   - All events in the same request should have the same `request_id`
   - Backend events include `request_id` from middleware
   - Frontend events may have `client_request_id` for client-side correlation

2. **Check session_id correlation:**
   - Intent capture creates `session_id`
   - Exclusive activation uses `session_id` from intent
   - All related events include the same `session_id`

3. **Check user_id correlation:**
   - After OTP verify, all events should include `user_id: driver_id`
   - Merchant events include `user_id: merchant_user_id`
   - Admin events include `user_id: admin_user_id`

4. **Check distinct_id:**
   - Before OTP: `distinct_id` is anonymous ID
   - After OTP: `distinct_id` is `driver_id`
   - All events from same user have same `distinct_id`

### 10. Error Handling Validation

1. **Test PostHog failure:**
   - Temporarily set invalid `POSTHOG_KEY`
   - Perform actions (OTP, exclusive activation, etc.)
   - **Verify:** No errors in browser console, app continues to work
   - **Verify:** Errors logged in backend logs

2. **Test HubSpot failure:**
   - Temporarily set invalid `HUBSPOT_ACCESS_TOKEN`
   - Complete OTP verification
   - **Verify:** PostHog events still captured
   - **Verify:** HubSpot errors logged but don't crash request

### 11. UTM Propagation Validation

1. Visit landing page with UTM params:
   ```
   http://localhost/?utm_source=test&utm_medium=email&utm_campaign=launch
   ```

2. Click CTA to open driver app
3. **Verify in PostHog:**
   - Landing events include UTM params
   - Driver `session.start` event includes UTM params
   - Subsequent driver events include UTM params (stored in localStorage)

### 12. Conversion Tracking Validation

1. Click CTA on landing page (`landing.cta.click`)
2. Driver app loads (`driver.session.start`)
3. **Verify in PostHog:**
   - Both events have matching `cta` property
   - Can create funnel: `landing.cta.click` → `driver.session.start`

## Common Issues & Troubleshooting

### No Events Appearing in PostHog

1. **Check environment variables:**
   ```bash
   docker compose exec backend env | grep POSTHOG
   docker compose exec driver env | grep VITE_POSTHOG
   ```

2. **Check analytics enabled:**
   - Verify `ANALYTICS_ENABLED=true` (or `VITE_ANALYTICS_ENABLED=true`)

3. **Check PostHog key:**
   - Verify key is valid and has correct permissions

4. **Check browser console:**
   - Look for analytics initialization logs
   - Check for PostHog errors

5. **Check backend logs:**
   ```bash
   docker compose logs backend | grep -i analytics
   ```

### Events Missing Properties

1. **Check request_id:**
   - Verify `RequestIDMiddleware` is added to middleware stack
   - Check response headers include `X-Request-ID`

2. **Check user_id:**
   - Verify user is authenticated
   - Check `identify()` was called after login

3. **Check session_id:**
   - Verify intent capture succeeded
   - Check session_id is propagated from backend response

### HubSpot Not Updating

1. **Check token:**
   - Verify `HUBSPOT_ACCESS_TOKEN` is set
   - Verify token has correct permissions (contacts write)

2. **Check logs:**
   ```bash
   docker compose logs backend | grep -i hubspot
   ```

3. **Verify contact exists:**
   - Check HubSpot UI for contact with phone/email
   - Verify properties are updating

## Success Criteria

All of the following should be true:

- [ ] Landing page events captured (`landing.page.view`, `landing.cta.click`)
- [ ] Driver app session start captured with UTM params
- [ ] OTP flow events captured (start, verify success/fail) on frontend and backend
- [ ] Intent capture events captured
- [ ] Exclusive activation events captured (click, blocked, success)
- [ ] Exclusive completion events captured
- [ ] Merchant events captured (create, toggle, brand image)
- [ ] Admin events captured (demo override, exclusive toggle, audit log view)
- [ ] Request IDs correlate frontend and backend events
- [ ] Session IDs correlate intent and exclusive events
- [ ] User IDs consistent across events for same user
- [ ] HubSpot contacts created/updated (if configured)
- [ ] No errors in browser console or backend logs
- [ ] App continues to work even if PostHog/HubSpot fail

## Next Steps

After validation:

1. Review PostHog dashboards and funnels
2. Set up HubSpot workflows based on lifecycle events
3. Create alerts for critical events (OTP failures, activation blocks, etc.)
4. Monitor event volume and adjust sampling if needed
5. Set up retention policies in PostHog




