# Tesla Developer Account Setup Guide

Step-by-step instructions for setting up a Tesla Developer Account to enable Virtual Key and Fleet Telemetry integration for Nerava.

---

## Overview

| Step | Action | Timeline |
|------|--------|----------|
| 1 | Create Tesla Developer Account | Day 1 |
| 2 | Create Application | Day 1 |
| 3 | Submit for Approval | Day 1 |
| 4 | Wait for Tesla Review | 5 business days |
| 5 | Host Public Key | After approval |
| 6 | Register as Partner | After approval |
| 7 | Configure Nerava Backend | After approval |
| 8 | Test with Real Vehicle | After configuration |

---

## Step 1: Create Tesla Developer Account

### 1.1 Navigate to Tesla Developer Portal

Go to: **https://developer.tesla.com/**

### 1.2 Sign In or Create Account

- If you have a Tesla Account (vehicle owner), sign in with those credentials
- If not, create a new Tesla Account

### 1.3 Accept Developer Terms

- Read and accept the Tesla Developer Terms of Service
- Accept the Fleet API Terms

---

## Step 2: Create Application

### 2.1 Go to Applications

Navigate to: **Dashboard → Applications → Create Application**

### 2.2 Fill Application Details

| Field | Value |
|-------|-------|
| **Application Name** | Nerava |
| **Description** | EV driver experience platform connecting Tesla drivers with nearby restaurants and merchants while charging |
| **Company Name** | Nerava Inc. |
| **Company Website** | https://nerava.com |
| **Application Type** | Third Party |
| **Redirect URI** | https://api.nerava.com/oauth/tesla/callback |

### 2.3 Select API Scopes

Request these scopes for Virtual Key and arrival tracking:

| Scope | Purpose | Required |
|-------|---------|----------|
| `vehicle_device_data` | Read vehicle location and state | Yes |
| `vehicle_location` | Real-time GPS location | Yes |
| `vehicle_charging_cmds` | Read charging status | Yes |
| `vehicle_cmds` | Send commands (flash lights) | Optional |
| `user_data` | Read user profile | Yes |

### 2.4 Configure OAuth Settings

```
Authorization URL: https://auth.tesla.com/oauth2/v3/authorize
Token URL: https://auth.tesla.com/oauth2/v3/token
```

### 2.5 Save Application

Note your **Client ID** and **Client Secret** - you'll need these later.

---

## Step 3: Submit for Approval

### 3.1 Prepare Submission Materials

Tesla requires:

1. **Application Description** (250+ words)
   - What your app does
   - How it benefits Tesla owners
   - Data usage and privacy practices

2. **Privacy Policy URL**
   - Must cover vehicle data collection
   - Example: https://nerava.com/privacy

3. **Terms of Service URL**
   - Must include vehicle integration terms
   - Example: https://nerava.com/terms

4. **Support Contact**
   - Email for Tesla to contact
   - Example: developers@nerava.com

### 3.2 Sample Application Description

```
Nerava enhances the Tesla charging experience by connecting drivers with
nearby restaurants and merchants while they charge. When a Tesla owner
arrives at a Supercharger, Nerava detects their location and presents
curated dining options within walking distance.

Key features:
- Automatic arrival detection at merchant locations
- Order timing synchronized with charging session
- Seamless Virtual Key pairing for frictionless experience
- Battery level awareness for order timing

Data usage:
- Vehicle location is used only during active sessions
- Charging state is used to time order readiness
- No data is stored beyond the charging session
- Users can revoke access at any time

Nerava improves the charging experience by making downtime productive,
helping Tesla owners discover local businesses while their vehicle charges.
```

### 3.3 Submit Application

Click **Submit for Review** in the Tesla Developer Dashboard.

---

## Step 4: Wait for Approval

### Timeline

- **Standard review:** 5 business days
- **Complex applications:** Up to 10 business days

### What Tesla Reviews

- Application legitimacy
- Data usage compliance
- Privacy policy adequacy
- OAuth implementation correctness
- Terms of service compliance

### If Rejected

Tesla will provide feedback. Common issues:
- Insufficient privacy policy
- Unclear data usage description
- Missing terms of service
- Invalid redirect URI

---

## Step 5: Host Public Key

After approval, you must host a public key for Tesla to verify your requests.

### 5.1 Generate Key Pair

```bash
# Generate private key (keep this secret!)
openssl ecparam -name prime256v1 -genkey -noout -out tesla_private_key.pem

# Generate public key (this gets hosted)
openssl ec -in tesla_private_key.pem -pubout -out tesla_public_key.pem
```

### 5.2 Host Public Key

The public key must be accessible at:
```
https://api.nerava.com/.well-known/appspecific/com.tesla.3p.public-key.pem
```

#### Option A: Static File in Nginx

Add to your nginx configuration:

```nginx
location /.well-known/appspecific/com.tesla.3p.public-key.pem {
    alias /etc/nerava/tesla_public_key.pem;
    add_header Content-Type application/x-pem-file;
}
```

#### Option B: S3 + CloudFront

1. Upload `tesla_public_key.pem` to S3 bucket
2. Configure CloudFront to serve at the required path
3. Ensure proper Content-Type header

### 5.3 Verify Hosting

```bash
curl -I https://api.nerava.com/.well-known/appspecific/com.tesla.3p.public-key.pem
# Should return 200 OK with Content-Type: application/x-pem-file
```

---

## Step 6: Register as Partner

### 6.1 Get Partner Token

Use your Client ID and Client Secret to get a partner authentication token:

```bash
curl -X POST https://fleet-api.prd.na.vn.cloud.tesla.com/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=openid vehicle_device_data vehicle_location"
```

### 6.2 Register Public Key

```bash
curl -X POST https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/partner_accounts \
  -H "Authorization: Bearer YOUR_PARTNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "api.nerava.com"
  }'
```

### 6.3 Verify Registration

```bash
curl https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/partner_accounts \
  -H "Authorization: Bearer YOUR_PARTNER_TOKEN"
```

---

## Step 7: Configure Nerava Backend

### 7.1 Environment Variables

Add to your `.env` or environment configuration:

```bash
# Tesla Fleet API Credentials
TESLA_CLIENT_ID=your_client_id_from_step_2
TESLA_CLIENT_SECRET=your_client_secret_from_step_2

# Public Key URL (must match hosted location)
TESLA_PUBLIC_KEY_URL=https://api.nerava.com/.well-known/appspecific/com.tesla.3p.public-key.pem

# Webhook Secret (generate a random string)
TESLA_WEBHOOK_SECRET=your_random_webhook_secret_32chars

# Fleet Telemetry Endpoint (if self-hosting)
TESLA_FLEET_TELEMETRY_ENDPOINT=wss://fleet-telemetry.nerava.com

# Enable the feature
FEATURE_VIRTUAL_KEY_ENABLED=true

# Disable mock mode for production
TESLA_MOCK_MODE=false
```

### 7.2 Store Private Key Securely

The private key (`tesla_private_key.pem`) must be stored securely:

- **AWS:** Use AWS Secrets Manager or Parameter Store
- **Docker:** Mount as a secret volume
- **Kubernetes:** Use a Secret resource

```bash
# Example: AWS Secrets Manager
aws secretsmanager create-secret \
  --name nerava/tesla-private-key \
  --secret-string "$(cat tesla_private_key.pem)"
```

### 7.3 Run Database Migration

```bash
cd backend
alembic upgrade head  # Creates virtual_keys table
```

---

## Step 8: Test with Real Vehicle

### 8.1 OAuth Flow Test

1. Open your app in a browser (or Tesla browser)
2. Trigger Virtual Key provisioning
3. Scan the QR code with Tesla mobile app
4. Approve the connection in Tesla app
5. Verify pairing completes

### 8.2 Verify Vehicle Data Access

```bash
# After user authorizes, you can fetch vehicle data
curl https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles \
  -H "Authorization: Bearer USER_ACCESS_TOKEN"
```

### 8.3 Test Location Tracking

1. Create an arrival session in Nerava
2. Drive to the merchant location
3. Verify arrival is detected automatically

---

## Costs

Tesla Fleet API uses pay-per-use pricing:

| Operation | Cost |
|-----------|------|
| Vehicle wake | $0.001 |
| Command (flash, honk) | $0.001 |
| Data streaming (per hour) | $0.002 |
| Location request | $0.0005 |

**Monthly credit:** $10 free (covers ~2 vehicles with normal usage)

---

## Fleet Telemetry Server (Optional)

For real-time vehicle tracking, you can self-host a Fleet Telemetry server.

### Option A: Use Tesla Webhooks (Recommended)

- Simpler setup
- Tesla sends webhooks to your endpoint
- Configure at `/v1/virtual-key/webhook/tesla`

### Option B: Self-Hosted Fleet Telemetry

1. Deploy Tesla's Fleet Telemetry server (Go binary)
2. Configure TLS certificates
3. Register telemetry endpoint with Tesla

See: https://github.com/teslamotors/fleet-telemetry

---

## Security Checklist

- [ ] Private key stored in secrets manager (not in code)
- [ ] Public key hosted via HTTPS only
- [ ] Webhook signature verification enabled
- [ ] OAuth tokens encrypted at rest
- [ ] Rate limiting on provisioning endpoint
- [ ] Audit logging for all Virtual Key operations
- [ ] Vehicle data retention policy implemented

---

## Support Resources

- **Tesla Developer Documentation:** https://developer.tesla.com/docs/fleet-api
- **Fleet API Reference:** https://developer.tesla.com/docs/fleet-api/endpoints
- **Fleet Telemetry GitHub:** https://github.com/teslamotors/fleet-telemetry
- **Tesla Developer Support:** developer@tesla.com

---

## Timeline Summary

| Week | Milestone |
|------|-----------|
| Week 1 | Submit application, host public key |
| Week 2 | Receive approval, register as partner |
| Week 3 | Configure backend, test with vehicle |
| Week 4 | Production deployment, monitor usage |

---

## Troubleshooting

### "Invalid client_id"

- Verify Client ID is correct in environment
- Check application status is "Approved" in dashboard

### "Public key not found"

- Verify key is hosted at exact URL
- Check Content-Type header is correct
- Ensure HTTPS is working

### "Unauthorized" on Fleet API calls

- Partner token may be expired (refresh it)
- User access token may be expired (re-authenticate user)
- Check required scopes are granted

### "Domain not registered"

- Complete partner registration (Step 6)
- Verify domain matches your API domain exactly

---

## Quick Reference

```bash
# Fleet API Base URL (North America)
https://fleet-api.prd.na.vn.cloud.tesla.com

# Auth URLs
https://auth.tesla.com/oauth2/v3/authorize
https://auth.tesla.com/oauth2/v3/token

# Public Key Path (must host at this path)
/.well-known/appspecific/com.tesla.3p.public-key.pem
```
