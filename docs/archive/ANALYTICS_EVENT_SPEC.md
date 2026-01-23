# Analytics Event Specification

## Overview

This document defines the event taxonomy, naming conventions, and required properties for all analytics events across the Nerava stack.

## Event Naming Convention

All events follow the pattern: `{app}.{domain}.{action}.{outcome}`

### App Prefixes
- `landing.*` - Landing page events
- `driver.*` - Driver app events
- `merchant.*` - Merchant portal events
- `admin.*` - Admin portal events
- `server.*` - Backend truth events

### Examples
- `driver.otp.verify.success` - Driver OTP verification succeeded
- `server.driver.exclusive.activate.blocked` - Server blocked exclusive activation
- `merchant.exclusive.toggle.on` - Merchant toggled exclusive on
- `landing.cta.click` - Landing page CTA clicked

## Required Properties

Every event MUST include these properties:

### Core Properties
- `app`: `landing` | `driver` | `merchant` | `admin` | `backend`
- `env`: `dev` | `staging` | `prod`
- `source`: `ui` | `api`
- `ts`: ISO 8601 timestamp string

### Correlation Properties
- `request_id`: UUID string (generated per request, propagated from backend)
- `session_id`: Intent/exclusive session ID when available
- `user_id`: `driver_id` | `merchant_user_id` | `admin_user_id` (when known)
- `merchant_id`: Merchant ID when relevant
- `charger_id`: Charger ID when relevant

### Frontend-Specific
- `client_request_id`: UUID generated on frontend (optional, for client-side correlation)

### Backend-Specific
- `ip`: Client IP address
- `user_agent`: User agent string

## Distinct ID Strategy

### Driver App
- **Before OTP verification**: Use anonymous ID persisted in `localStorage` (`nerava_anon_id`)
- **After OTP verification**: Switch to `driver_id` as `distinct_id`
- **Identification**: Call `analytics.identify(driver_id, { phone_last4, created_at })` on OTP success

### Merchant Portal
- **Before login**: Use anonymous ID
- **After login**: Use `merchant_user_id` or email as `distinct_id`
- **Identification**: Call `analytics.identify(merchant_user_id, { email, merchant_id })` on login success

### Admin Portal
- **Before login**: Use anonymous ID
- **After login**: Use `admin_user_id` or email as `distinct_id`
- **Identification**: Call `analytics.identify(admin_user_id, { email })` on login success

### Landing Page
- Use anonymous ID (no user identification until app navigation)

## PostHog vs HubSpot Decision Matrix

### PostHog (Product Analytics)
**Send to PostHog:**
- All user interactions (clicks, page views, form submissions)
- Product behavior events (OTP flows, exclusive activation, completions)
- Error events
- Feature usage
- Funnel events
- Debugging events

**Properties**: Include all correlation IDs, user context, but NO full PII (phone_last4 only, not full phone)

### HubSpot (CRM Lifecycle)
**Send to HubSpot:**
- Lifecycle milestones only:
  - Driver OTP verified (create/update contact)
  - Merchant authenticated (create/update contact)
  - Exclusive enabled by merchant (update merchant company)
  - Exclusive completed by driver (update driver contact)
  - First exclusive completion (set lifecycle_stage)

**Properties**: Full PII allowed (phone, email) + business properties (role, merchant_id, lifecycle_stage)

**Rule**: HubSpot writes are LOW-VOLUME, lifecycle-only. Not every click.

## Event Catalog

### Landing Page Events

#### `landing.page.view`
**Properties:**
- `path`: Current page path
- `referrer`: Referrer URL
- `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`: UTM parameters

#### `landing.cta.click`
**Properties:**
- `cta_id`: `open_driver` | `for_businesses` | `admin`
- `cta_text`: Button text
- `utm_*`: UTM parameters

#### `landing.cta.convert`
**Properties:**
- `cta_id`: Original CTA clicked
- `destination_app`: `driver` | `merchant` | `admin`

### Driver App Events

#### `driver.session.start`
**Properties:**
- `src`: Source (`landing`, etc.)
- `cta`: CTA ID if from landing
- `utm_*`: UTM parameters

#### `driver.page.view`
**Properties:**
- `page`: `home` | `merchant_detail` | `otp` | `exclusive_active`

#### `driver.otp.start`
**Properties:**
- `phone_last4`: Last 4 digits of phone

#### `driver.otp.verify.success` / `driver.otp.verify.fail`
**Properties:**
- `phone_last4`: Last 4 digits
- `attempt_count`: Number of attempts

#### `driver.intent.capture.request` / `driver.intent.capture.success` / `driver.intent.capture.fail`
**Properties:**
- `location_accuracy`: Location accuracy in meters
- `merchant_count`: Number of merchants returned

#### `driver.exclusive.activate.click`
**Properties:**
- `merchant_id`: Merchant ID
- `exclusive_id`: Exclusive ID

#### `driver.exclusive.activate.blocked_outside_radius`
**Properties:**
- `merchant_id`: Merchant ID
- `distance_m`: Distance from merchant in meters
- `required_radius_m`: Required radius

#### `driver.exclusive.activate.success` / `driver.exclusive.activate.fail`
**Properties:**
- `merchant_id`: Merchant ID
- `exclusive_id`: Exclusive ID
- `session_id`: Exclusive session ID

#### `driver.exclusive.complete.click` / `driver.exclusive.complete.success` / `driver.exclusive.complete.fail`
**Properties:**
- `merchant_id`: Merchant ID
- `exclusive_id`: Exclusive ID
- `session_id`: Exclusive session ID

#### `driver.location.permission.granted` / `driver.location.permission.denied`
**Properties:**
- None (permission state only)

#### `driver.cta.open_maps.click`
**Properties:**
- `merchant_id`: Merchant ID

#### `driver.preferences.submit`
**Properties:**
- `preferences`: Object with preference keys

### Merchant Portal Events

#### `merchant.login.success` / `merchant.login.fail`
**Properties:**
- `email`: Email address (hashed or last part only for PostHog)

#### `merchant.exclusive.create.open`
**Properties:**
- None

#### `merchant.exclusive.create.submit.success` / `merchant.exclusive.create.submit.fail`
**Properties:**
- `exclusive_id`: Exclusive ID (on success)
- `error`: Error message (on fail)

#### `merchant.exclusive.toggle.on` / `merchant.exclusive.toggle.off`
**Properties:**
- `exclusive_id`: Exclusive ID

#### `merchant.brand_image.upload.success` / `merchant.brand_image.upload.fail`
**Properties:**
- `image_size_bytes`: Image size
- `error`: Error message (on fail)

#### `merchant.analytics.view`
**Properties:**
- None

### Admin Portal Events

#### `admin.login.success` / `admin.login.fail`
**Properties:**
- `email`: Email address (hashed or last part only for PostHog)

#### `admin.demo_location.override.set.success` / `admin.demo_location.override.set.fail`
**Properties:**
- `driver_id`: Driver ID
- `latitude`: Override latitude
- `longitude`: Override longitude
- `error`: Error message (on fail)

#### `admin.exclusive.toggle.on` / `admin.exclusive.toggle.off`
**Properties:**
- `exclusive_id`: Exclusive ID
- `merchant_id`: Merchant ID

#### `admin.audit_log.view`
**Properties:**
- `filter`: Filter applied (if any)

#### `admin.merchants.view`
**Properties:**
- None

#### `admin.operation.error`
**Properties:**
- `operation`: Operation name
- `error`: Error message
- `error_code`: Error code if available

### Backend Server Events

#### `server.driver.otp.start`
**Properties:**
- `phone_last4`: Last 4 digits
- `ip`: Client IP

#### `server.driver.otp.verify.success` / `server.driver.otp.verify.fail`
**Properties:**
- `driver_id`: Driver ID (on success)
- `phone_last4`: Last 4 digits
- `attempt_count`: Attempt number
- `ip`: Client IP

#### `server.driver.intent.capture.success` / `server.driver.intent.capture.fail`
**Properties:**
- `driver_id`: Driver ID
- `location_accuracy`: Location accuracy in meters
- `merchant_count`: Number of merchants returned
- `error`: Error message (on fail)

#### `server.driver.exclusive.activate.success` / `server.driver.exclusive.activate.blocked` / `server.driver.exclusive.activate.fail`
**Properties:**
- `driver_id`: Driver ID
- `merchant_id`: Merchant ID
- `exclusive_id`: Exclusive ID
- `session_id`: Exclusive session ID (on success)
- `block_reason`: Reason for block (on blocked)
- `distance_m`: Distance from merchant (on blocked)
- `error`: Error message (on fail)

#### `server.driver.exclusive.complete.success` / `server.driver.exclusive.complete.fail`
**Properties:**
- `driver_id`: Driver ID
- `merchant_id`: Merchant ID
- `exclusive_id`: Exclusive ID
- `session_id`: Exclusive session ID
- `error`: Error message (on fail)

#### `server.driver.exclusive.expire`
**Properties:**
- `driver_id`: Driver ID
- `merchant_id`: Merchant ID
- `exclusive_id`: Exclusive ID
- `session_id`: Exclusive session ID
- `expired_at`: Expiration timestamp

#### `server.merchant.exclusive.create` / `server.merchant.exclusive.update`
**Properties:**
- `merchant_user_id`: Merchant user ID
- `merchant_id`: Merchant ID
- `exclusive_id`: Exclusive ID

#### `server.merchant.exclusive.toggle`
**Properties:**
- `merchant_user_id`: Merchant user ID
- `merchant_id`: Merchant ID
- `exclusive_id`: Exclusive ID
- `enabled`: Boolean

#### `server.merchant.brand_image.set`
**Properties:**
- `merchant_user_id`: Merchant user ID
- `merchant_id`: Merchant ID
- `image_url`: Image URL

#### `server.admin.demo_location.override`
**Properties:**
- `admin_user_id`: Admin user ID
- `driver_id`: Driver ID
- `latitude`: Override latitude
- `longitude`: Override longitude

#### `server.admin.exclusive.toggle`
**Properties:**
- `admin_user_id`: Admin user ID
- `exclusive_id`: Exclusive ID
- `merchant_id`: Merchant ID
- `enabled`: Boolean

#### `server.admin.audit_log.view`
**Properties:**
- `admin_user_id`: Admin user ID
- `filter`: Filter applied (if any)

## PII Handling

### PostHog
- **Never send**: Full phone numbers, full email addresses (use last part or hash)
- **Allowed**: `phone_last4`, email domain, hashed identifiers
- **Rationale**: PostHog is for product analytics, not CRM

### HubSpot
- **Allowed**: Full phone numbers, full email addresses
- **Rationale**: HubSpot is CRM, needs full PII for contact management

## Correlation Strategy

### Request ID Flow
1. Backend generates `request_id` UUID per request (via middleware)
2. Backend includes `request_id` in response header `X-Request-ID`
3. Frontend can send `X-Request-ID` in subsequent requests
4. All events (frontend + backend) include `request_id` in properties

### Session ID Flow
- `session_id` represents an intent session or exclusive session
- Generated by backend when session starts
- Propagated to frontend via API responses
- Included in all related events

### User ID Flow
- `user_id` is the authenticated user ID (`driver_id`, `merchant_user_id`, `admin_user_id`)
- Set by backend after authentication
- Frontend includes in events after identification

## Environment Configuration

### Frontend (Vite)
- `VITE_POSTHOG_KEY`: PostHog project API key
- `VITE_POSTHOG_HOST`: PostHog host (default: `https://app.posthog.com`)
- `VITE_ANALYTICS_ENABLED`: Enable/disable analytics (default: `true`)

### Frontend (Next.js)
- `NEXT_PUBLIC_POSTHOG_KEY`: PostHog project API key
- `NEXT_PUBLIC_POSTHOG_HOST`: PostHog host (default: `https://app.posthog.com`)
- `NEXT_PUBLIC_ANALYTICS_ENABLED`: Enable/disable analytics (default: `true`)

### Backend
- `POSTHOG_KEY`: PostHog project API key
- `POSTHOG_HOST`: PostHog host (default: `https://app.posthog.com`)
- `HUBSPOT_ACCESS_TOKEN`: HubSpot private app access token
- `ANALYTICS_ENABLED`: Enable/disable analytics (default: `true`)
- `ENV`: Environment (`dev` | `staging` | `prod`)

## Error Handling

### Frontend
- Analytics failures must never break user flows
- Log errors to console in development
- Silently fail in production

### Backend
- Analytics failures must never crash requests
- Log errors with appropriate log level
- Continue request processing even if analytics fails

## Sampling

- **Current**: No sampling (100% of events)
- **Future**: Can reduce sampling if volume is high
- **Note**: Sampling should be configurable per environment




