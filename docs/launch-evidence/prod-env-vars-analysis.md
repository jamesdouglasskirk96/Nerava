# Production Environment Variables Analysis

**Generated**: 2025-01-27  
**Purpose**: Compare required env vars for production against App Runner current state

## Required Environment Variables for Production

Based on analysis of:
- [`ENV.example`](ENV.example) - root level
- [`nerava-backend-v9/ENV.example`](nerava-backend-v9/ENV.example) - backend specific  
- [`nerava-backend-v9/app/config.py`](nerava-backend-v9/app/config.py) - Settings class
- [`AWS_DEPLOYMENT_STATUS.md`](AWS_DEPLOYMENT_STATUS.md) - deployment context

### Critical Required Variables

| Variable | Purpose | Required In Prod | Default Value |
|----------|---------|-----------------|---------------|
| `ENV` | Environment identifier | ✅ Yes | `prod` (not "production") |
| `DATABASE_URL` | PostgreSQL connection string | ✅ Yes | `sqlite:///./nerava.db` (dev only) |
| `REDIS_URL` | Redis connection string | ✅ Yes | `redis://localhost:6379/0` (dev only) |
| `JWT_SECRET` | JWT signing secret | ✅ Yes | `dev-secret` (must be secure random in prod) |
| `TOKEN_ENCRYPTION_KEY` | Fernet key for token encryption | ✅ Yes | Must be 44-char base64 (required in non-local) |
| `PUBLIC_BASE_URL` | Public API URL for callbacks/webhooks | ✅ Yes | `http://127.0.0.1:8001` (dev) |
| `FRONTEND_URL` | Frontend URL for OAuth redirects | ✅ Yes | `http://localhost:8001/app` (dev) |
| `ALLOWED_ORIGINS` | CORS allowed origins | ✅ Yes | `*` (dev), explicit origins in prod |
| `SQUARE_WEBHOOK_SIGNATURE_KEY` | Square webhook verification | ⚠️ If Square enabled | Empty |
| `STRIPE_SECRET` | Stripe API key | ⚠️ If payouts enabled | Empty |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification | ⚠️ If Stripe enabled | Empty |

### Optional but Recommended Variables

| Variable | Purpose | Recommended |
|----------|---------|-------------|
| `SENTRY_DSN` | Error tracking | Yes (non-local) |
| `GOOGLE_PLACES_API_KEY` | Google Places API | Yes (if using merchant discovery) |
| `NREL_API_KEY` | NREL charger data | Yes (if using charger discovery) |
| `SMARTCAR_CLIENT_ID` | Smartcar OAuth | Yes (if using EV integration) |
| `SMARTCAR_CLIENT_SECRET` | Smartcar OAuth | Yes (if using EV integration) |

## App Runner Current State

**Service ARN**: `arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/73985bebdfe94f63b978cc605e656d3f`  
**Service URL**: `https://9bjh9xzirw.us-east-1.awsapprunner.com`  
**Status**: `OPERATION_IN_PROGRESS` (from AWS_DEPLOYMENT_STATUS.md)

### Currently Set Variables (from AWS_DEPLOYMENT_STATUS.md)

According to deployment status document:
- ✅ `ALLOWED_ORIGINS` - Set
- ✅ `DATABASE_URL` - Set (but SQLite, not PostgreSQL)
- ✅ `DEMO_MODE` - Set
- ✅ `ENV` - Set to `prod` (was fixed from "production")
- ✅ `JWT_SECRET` - Set
- ✅ `PORT` - Set
- ✅ `PYTHONPATH` - Set
- ✅ `REGION` - Set

### Missing Variables (from AWS_DEPLOYMENT_STATUS.md)

- ❌ `REDIS_URL` - Missing
- ❌ `TOKEN_ENCRYPTION_KEY` - Missing
- ❌ `PUBLIC_BASE_URL` - Missing
- ❌ `FRONTEND_URL` - Missing

## AWS CLI Command to Extract Current Env Vars

If MCP aws-iac is blocked, run this command to get current App Runner environment variables:

```bash
export APP_RUNNER_SERVICE_ARN="arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/73985bebdfe94f63b978cc605e656d3f"
aws apprunner describe-service \
  --service-arn "$APP_RUNNER_SERVICE_ARN" \
  --region us-east-1 \
  --query 'Service.ServiceConfiguration.RuntimeEnvironmentVariables' \
  --output json > apprunner-env-vars.json
```

## Missing Variables and Runtime Consequences

| Variable | Required | Currently Set | Missing Impact | Severity |
|----------|----------|---------------|----------------|----------|
| `REDIS_URL` | ✅ Yes | ❌ No | Rate limiting fails, session storage broken, `/readyz` endpoint fails | **Critical** |
| `TOKEN_ENCRYPTION_KEY` | ✅ Yes | ❌ No | Token encryption disabled, security risk for stored tokens (Square, vehicle tokens) | **Critical** |
| `PUBLIC_BASE_URL` | ✅ Yes | ❌ No | OAuth redirects fail, webhook callbacks fail, QR code URLs incorrect | **High** |
| `FRONTEND_URL` | ✅ Yes | ❌ No | OAuth callbacks fail, frontend redirects broken | **High** |
| `DATABASE_URL` | ✅ Yes | ⚠️ SQLite | Using SQLite instead of PostgreSQL - not production-ready, no concurrent writes, no replication | **Critical** |

### Detailed Runtime Consequences

#### REDIS_URL Missing
- **What breaks**: Rate limiting middleware, session storage, `/readyz` health check
- **Error users see**: 500 errors on rate-limited endpoints, `/readyz` returns 503
- **Security implications**: Rate limiting disabled, potential DDoS vulnerability

#### TOKEN_ENCRYPTION_KEY Missing  
- **What breaks**: Token encryption for Square tokens, vehicle tokens, sensitive data
- **Error users see**: May work but tokens stored in plaintext
- **Security implications**: **CRITICAL** - Sensitive tokens exposed if database compromised

#### PUBLIC_BASE_URL Missing
- **What breaks**: OAuth redirects (Square, Smartcar), webhook callbacks, QR code generation
- **Error users see**: OAuth flows fail, webhooks not received, QR codes point to wrong URL
- **Security implications**: Medium - OAuth flows broken, webhook verification may fail

#### FRONTEND_URL Missing
- **What breaks**: OAuth callback redirects, magic link redirects
- **Error users see**: OAuth flows complete but redirect fails, users stuck
- **Security implications**: Low - UX issue, not security risk

#### DATABASE_URL Using SQLite
- **What breaks**: Concurrent writes, production scalability, data durability
- **Error users see**: Database locked errors under load, data loss risk
- **Security implications**: High - Not suitable for production, no backup strategy

## Recommendations

1. **Immediate (Critical)**:
   - Set `REDIS_URL` to ElastiCache endpoint (after Phase 4 completion)
   - Set `TOKEN_ENCRYPTION_KEY` to generated Fernet key (already generated in `/tmp/secrets.sh`)
   - Update `DATABASE_URL` to PostgreSQL connection string (after Phase 3 completion)

2. **High Priority**:
   - Set `PUBLIC_BASE_URL` to App Runner URL: `https://9bjh9xzirw.us-east-1.awsapprunner.com`
   - Set `FRONTEND_URL` to CloudFront URL (after Phase 6 completion)

3. **After CloudFront Deployment**:
   - Update `ALLOWED_ORIGINS` to include CloudFront domain (remove wildcard `*`)









