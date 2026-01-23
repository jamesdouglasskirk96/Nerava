# Nerava API Keys & Accounts Setup Guide

This guide walks you through setting up all the external services needed for full production functionality.

---

## Current Status

### Already Configured ✅
| Service | Keys | Status |
|---------|------|--------|
| PostgreSQL (RDS) | DATABASE_URL | ✅ Working |
| Redis (ElastiCache) | REDIS_URL | ✅ Working |
| JWT Auth | JWT_SECRET, TOKEN_ENCRYPTION_KEY | ✅ Working |
| Twilio SMS | TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_VERIFY_SERVICE_SID | ✅ Working |

### Needs Setup ❌
| Service | Priority | Purpose |
|---------|----------|---------|
| Stripe | 🔴 HIGH | Payment processing, merchant payouts |
| Sentry | 🟡 MEDIUM | Error tracking & monitoring |
| SendGrid | 🟡 MEDIUM | Transactional emails |
| Smartcar | 🟡 MEDIUM | EV vehicle data integration |
| Google Places | 🟡 MEDIUM | Already hardcoded - move to env var |
| Square | 🟢 LOW | Merchant POS integration |
| PostHog | 🟢 LOW | Analytics |
| Google Sign-In | 🟢 LOW | Social login |
| Apple Sign-In | 🟢 LOW | Social login |
| HubSpot | 🟢 LOW | CRM integration |

---

## 1. Stripe (Payment Processing) 🔴 HIGH PRIORITY

### What It's Used For
- Processing driver payments
- Merchant payouts
- Subscription billing (Primary Experience)
- Webhook notifications for payment events

### Step-by-Step Setup

1. **Create Stripe Account**
   - Go to: https://dashboard.stripe.com/register
   - Enter your email and create password
   - Verify your email

2. **Complete Business Verification**
   - Go to: https://dashboard.stripe.com/account/onboarding
   - Fill in business details (name, address, tax ID)
   - Add bank account for payouts
   - This can take 1-2 business days for verification

3. **Get API Keys**
   - Go to: https://dashboard.stripe.com/apikeys
   - Copy **Secret key** (starts with `sk_live_` or `sk_test_`)
   - Copy **Publishable key** (starts with `pk_live_` or `pk_test_`)

4. **Set Up Stripe Connect (for merchant payouts)**
   - Go to: https://dashboard.stripe.com/settings/connect
   - Enable Connect
   - Copy **Connect Client ID** (starts with `ca_`)

5. **Set Up Webhooks**
   - Go to: https://dashboard.stripe.com/webhooks
   - Click "Add endpoint"
   - URL: `https://api.nerava.network/v1/stripe/webhook`
   - Events to listen for:
     - `checkout.session.completed`
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `account.updated` (for Connect)
   - Copy **Webhook signing secret** (starts with `whsec_`)

### Environment Variables to Add
```
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxx
STRIPE_CONNECT_CLIENT_ID=ca_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

### Testing
- Use test mode first (keys start with `sk_test_`)
- Test card: `4242 4242 4242 4242` (any future date, any CVC)

---

## 2. Sentry (Error Tracking) 🟡 MEDIUM PRIORITY

### What It's Used For
- Automatic error capture and alerting
- Performance monitoring
- Stack traces for debugging production issues

### Step-by-Step Setup

1. **Create Sentry Account**
   - Go to: https://sentry.io/signup/
   - Sign up with email or GitHub
   - Free tier includes 5,000 errors/month

2. **Create a New Project**
   - Click "Create Project"
   - Select **Python** as platform
   - Select **FastAPI** as framework
   - Name it: `nerava-backend`

3. **Get DSN**
   - After creating project, you'll see the DSN
   - Or go to: Settings → Projects → nerava-backend → Client Keys (DSN)
   - Copy the DSN URL

### Environment Variables to Add
```
SENTRY_DSN=https://xxxx@xxxx.ingest.sentry.io/xxxx
SENTRY_ENVIRONMENT=prod
SENTRY_ENABLED=true
```

### Testing
- Trigger a test error: `curl https://api.nerava.network/v1/sentry-test`
- Check Sentry dashboard for the error

---

## 3. SendGrid (Email) 🟡 MEDIUM PRIORITY

### What It's Used For
- Welcome emails
- Password reset emails
- Merchant portal invitations
- Transaction receipts

### Step-by-Step Setup

1. **Create SendGrid Account**
   - Go to: https://signup.sendgrid.com/
   - Sign up (free tier: 100 emails/day)

2. **Verify Your Domain (Recommended)**
   - Go to: Settings → Sender Authentication
   - Click "Authenticate Your Domain"
   - Add DNS records to your domain (nerava.network)
   - Records needed: CNAME for email links and DKIM

3. **Create API Key**
   - Go to: Settings → API Keys
   - Click "Create API Key"
   - Name: `nerava-backend`
   - Permissions: "Full Access" or "Restricted Access" with Mail Send
   - Copy the API key (shown only once!)

4. **Verify Sender Identity**
   - Go to: Settings → Sender Authentication → Single Sender Verification
   - Add: `noreply@nerava.network`
   - Verify via email link

### Environment Variables to Add
```
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
EMAIL_FROM=noreply@nerava.network
EMAIL_PROVIDER=sendgrid
```

### Testing
- Send a test email from SendGrid dashboard
- Check spam folder if not received

---

## 4. Smartcar (EV Data) 🟡 MEDIUM PRIORITY

### What It's Used For
- Connect to user's EV (Tesla, Ford, etc.)
- Get real-time battery level
- Get charging status
- Get vehicle location

### Step-by-Step Setup

1. **Create Smartcar Account**
   - Go to: https://dashboard.smartcar.com/signup
   - Sign up for Developer account

2. **Create Application**
   - Go to: https://dashboard.smartcar.com/apps
   - Click "Create Application"
   - Name: `Nerava`
   - Select vehicle brands to support (Tesla, Ford, etc.)

3. **Configure OAuth**
   - In your app settings, add Redirect URI:
     - `https://api.nerava.network/oauth/smartcar/callback`
   - Copy **Client ID** and **Client Secret**

4. **Request Production Access**
   - Smartcar requires approval for production
   - Fill out their application form
   - Describe your use case (EV charging app)

### Environment Variables to Add
```
SMARTCAR_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SMARTCAR_CLIENT_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SMARTCAR_REDIRECT_URI=https://api.nerava.network/oauth/smartcar/callback
SMARTCAR_STATE_SECRET=random-secret-for-jwt-state
SMARTCAR_MODE=live
SMARTCAR_ENABLED=true
```

### Testing
- Use Smartcar's test mode first
- They provide simulated vehicles for testing

---

## 5. Google Places API 🟡 MEDIUM PRIORITY

### Current Status
- API key is **hardcoded** in `app/utils/pwa_responses.py`
- Current key: `AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg`
- Should be moved to environment variable

### What It's Used For
- Searching for nearby merchants
- Getting place details (hours, ratings, photos)
- Autocomplete for addresses

### Step-by-Step Setup

1. **Create Google Cloud Project** (if not exists)
   - Go to: https://console.cloud.google.com/
   - Create new project or select existing

2. **Enable APIs**
   - Go to: APIs & Services → Enable APIs
   - Enable:
     - Places API
     - Maps JavaScript API
     - Geocoding API

3. **Create API Key**
   - Go to: APIs & Services → Credentials
   - Click "Create Credentials" → API Key
   - Copy the key

4. **Restrict API Key** (Important for security)
   - Click on the API key
   - Under "Application restrictions":
     - Add your server IP or use HTTP referrers
   - Under "API restrictions":
     - Select the APIs you enabled

### Environment Variables to Add
```
GOOGLE_PLACES_API_KEY=AIzaSy...
```

### Action Required
- Move hardcoded key to environment variable
- Or create a new restricted key for production

---

## 6. Square (Merchant POS) 🟢 LOW PRIORITY

### What It's Used For
- Merchant point-of-sale integration
- Real-time transaction data
- Automatic perk validation

### Step-by-Step Setup

1. **Create Square Developer Account**
   - Go to: https://developer.squareup.com/
   - Sign up or log in

2. **Create Application**
   - Go to: https://developer.squareup.com/apps
   - Click "Create Application"
   - Name: `Nerava`

3. **Get Production Credentials**
   - In app dashboard, switch to "Production"
   - Copy **Application ID** and **Application Secret**

4. **Set Up OAuth**
   - Add Redirect URL: `https://api.nerava.network/oauth/square/callback`

5. **Set Up Webhooks**
   - Add webhook URL: `https://api.nerava.network/v1/square/webhook`
   - Subscribe to: `payment.completed`, `order.created`

### Environment Variables to Add
```
SQUARE_APPLICATION_ID_PRODUCTION=sq0idp-xxxxx
SQUARE_APPLICATION_SECRET_PRODUCTION=sq0csp-xxxxx
SQUARE_REDIRECT_URL_PRODUCTION=https://api.nerava.network/oauth/square/callback
SQUARE_WEBHOOK_SIGNATURE_KEY=xxxxx
```

---

## 7. PostHog (Analytics) 🟢 LOW PRIORITY

### What It's Used For
- User behavior analytics
- Feature usage tracking
- Funnel analysis

### Step-by-Step Setup

1. **Create PostHog Account**
   - Go to: https://app.posthog.com/signup
   - Free tier: 1M events/month

2. **Get API Key**
   - Go to: Project Settings
   - Copy **Project API Key**

### Environment Variables to Add
```
POSTHOG_API_KEY=phc_xxxxx
POSTHOG_HOST=https://app.posthog.com
ANALYTICS_ENABLED=true
```

---

## 8. Google Sign-In 🟢 LOW PRIORITY

### What It's Used For
- "Sign in with Google" button
- Faster user registration

### Step-by-Step Setup

1. **Go to Google Cloud Console**
   - https://console.cloud.google.com/apis/credentials

2. **Create OAuth 2.0 Client**
   - Click "Create Credentials" → OAuth client ID
   - Application type: Web application
   - Add authorized redirect URIs:
     - `https://api.nerava.network/auth/google/callback`
     - `https://app.nerava.network/auth/callback`

3. **Configure Consent Screen**
   - Go to: OAuth consent screen
   - Add app name, logo, support email
   - Add scopes: email, profile

### Environment Variables to Add
```
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
```

---

## 9. Apple Sign-In 🟢 LOW PRIORITY

### What It's Used For
- "Sign in with Apple" button
- Required for iOS App Store apps

### Step-by-Step Setup

1. **Apple Developer Account Required**
   - Cost: $99/year
   - Go to: https://developer.apple.com/account

2. **Create App ID**
   - Go to: Certificates, Identifiers & Profiles
   - Create new App ID with Sign In with Apple capability

3. **Create Service ID**
   - Create Service ID for web authentication
   - Configure domains and redirect URLs

4. **Create Key**
   - Create a new key with Sign In with Apple enabled
   - Download the .p8 file

### Environment Variables to Add
```
APPLE_CLIENT_ID=com.nerava.service
APPLE_TEAM_ID=XXXXXXXXXX
APPLE_KEY_ID=XXXXXXXXXX
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIGT...
```

---

## 10. HubSpot (CRM) 🟢 LOW PRIORITY

### What It's Used For
- Track merchant leads
- Automated email sequences
- Sales pipeline management

### Step-by-Step Setup

1. **Create HubSpot Account**
   - Go to: https://www.hubspot.com/
   - Free CRM tier available

2. **Create Private App**
   - Go to: Settings → Integrations → Private Apps
   - Create new app with required scopes

3. **Get Access Token**
   - Copy the access token from the app

### Environment Variables to Add
```
HUBSPOT_PRIVATE_APP_TOKEN=pat-na1-xxxxx
HUBSPOT_PORTAL_ID=12345678
HUBSPOT_ENABLED=true
HUBSPOT_SEND_LIVE=true
```

---

## Quick Reference: All Environment Variables

```bash
# Stripe (Payment Processing)
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_CONNECT_CLIENT_ID=ca_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Sentry (Error Tracking)
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
SENTRY_ENVIRONMENT=prod
SENTRY_ENABLED=true

# SendGrid (Email)
SENDGRID_API_KEY=SG.xxxxx
EMAIL_FROM=noreply@nerava.network
EMAIL_PROVIDER=sendgrid

# Smartcar (EV Data)
SMARTCAR_CLIENT_ID=xxxxx
SMARTCAR_CLIENT_SECRET=xxxxx
SMARTCAR_REDIRECT_URI=https://api.nerava.network/oauth/smartcar/callback
SMARTCAR_STATE_SECRET=random-secret
SMARTCAR_MODE=live
SMARTCAR_ENABLED=true

# Google Places
GOOGLE_PLACES_API_KEY=AIzaSy...

# Square (Merchant POS)
SQUARE_APPLICATION_ID_PRODUCTION=sq0idp-xxxxx
SQUARE_APPLICATION_SECRET_PRODUCTION=sq0csp-xxxxx
SQUARE_REDIRECT_URL_PRODUCTION=https://api.nerava.network/oauth/square/callback
SQUARE_WEBHOOK_SIGNATURE_KEY=xxxxx

# PostHog (Analytics)
POSTHOG_API_KEY=phc_xxxxx
POSTHOG_HOST=https://app.posthog.com
ANALYTICS_ENABLED=true

# Google Sign-In
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx

# Apple Sign-In
APPLE_CLIENT_ID=com.nerava.service
APPLE_TEAM_ID=XXXXXXXXXX
APPLE_KEY_ID=XXXXXXXXXX
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...

# HubSpot (CRM)
HUBSPOT_PRIVATE_APP_TOKEN=pat-na1-xxxxx
HUBSPOT_PORTAL_ID=12345678
HUBSPOT_ENABLED=true
```

---

## Recommended Setup Order

1. **Week 1 - Critical**
   - [ ] Stripe (payments are core functionality)
   - [ ] Sentry (need visibility into production errors)

2. **Week 2 - Important**
   - [ ] SendGrid (user communications)
   - [ ] Move Google Places key to env var

3. **Week 3 - Nice to Have**
   - [ ] Smartcar (EV integration)
   - [ ] PostHog (analytics)

4. **Later**
   - [ ] Square (merchant POS)
   - [ ] Google/Apple Sign-In
   - [ ] HubSpot (CRM)

---

## Adding Keys to App Runner

Once you have the keys, update the App Runner service:

```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          ... existing vars ...,
          "STRIPE_SECRET_KEY": "sk_live_xxxxx",
          "SENTRY_DSN": "https://xxxxx@xxxxx.ingest.sentry.io/xxxxx",
          ... new vars ...
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
    }
  }' \
  --region us-east-1
```

---

## Questions?

If you need help with any of these integrations, let me know which one and I can provide more detailed guidance.
