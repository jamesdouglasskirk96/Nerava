# Nerava Production Deployment Guide

Complete guide for deploying Nerava to AWS using App Runner (backend) and S3/CloudFront (frontends).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Route53 DNS                             │
│  nerava.network → CloudFront (landing)                      │
│  app.nerava.network → CloudFront (driver)                   │
│  merchant.nerava.network → CloudFront (merchant)           │
│  admin.nerava.network → CloudFront (admin)                  │
│  api.nerava.network → App Runner (backend)                  │
│  photos.nerava.network → CloudFront (merchant photos)      │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                     │
┌───────▼────────┐              ┌────────────▼──────────┐
│  CloudFront    │              │   App Runner          │
│  Distributions │              │   (FastAPI Backend)   │
└───────┬────────┘              └────────────┬──────────┘
        │                                     │
┌───────▼────────┐              ┌────────────▼──────────┐
│  S3 Buckets   │              │   RDS PostgreSQL      │
│  (Static Sites)│              │   (Existing)          │
└────────────────┘              └───────────────────────┘
```

## Prerequisites

### Required Tools
- AWS CLI configured with appropriate credentials
- Docker installed and running
- Node.js 18+ and npm
- Python 3.9+
- jq (JSON processor)
- curl

### AWS Resources
- AWS Account: `566287346479`
- Region: `us-east-1`
- Route53 Hosted Zone: `Z03087823KHR6VJQ9AGZL` (nerava.network)
- ACM Certificate: `arn:aws:acm:us-east-1:566287346479:certificate/9abd6168-db05-4455-b53b-0b3d397da70d`
- RDS Database: `nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432`
- ECR Repositories: `nerava/backend`, `nerava/driver`, `nerava/merchant`, `nerava/admin`, `nerava/landing`

### Required Environment Variables

#### Backend (App Runner)
```bash
# Required
DATABASE_URL=postgresql://postgres:<PASSWORD>@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava
JWT_SECRET=<secure-random-value>
ENV=prod

# Optional (can use Secrets Manager)
GOOGLE_PLACES_API_KEY=<your-key>
REDIS_URL=redis://<host>:6379/0
TOKEN_ENCRYPTION_KEY=<44-char-fernet-key>
```

#### Frontend Builds
```bash
# Driver App (nerava-ui 2)
VITE_API_BASE_URL=https://api.nerava.network
VITE_ENV=prod

# Merchant Portal (apps/merchant)
VITE_API_BASE_URL=https://api.nerava.network
VITE_ENV=prod

# Admin Portal (apps/admin)
VITE_API_BASE_URL=https://api.nerava.network
VITE_ENV=prod

# Landing Page (apps/landing)
NEXT_STATIC_EXPORT=true
NEXT_PUBLIC_BASE_PATH=
```

## Deployment Steps

### Step 1: Deploy Backend (App Runner)

```bash
# Set required environment variables
export DATABASE_URL="postgresql://postgres:<PASSWORD>@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"
export JWT_SECRET="<your-secure-secret>"
export ENV="prod"

# Optional: Use Secrets Manager
export JWT_SECRET_SECRET_NAME="nerava/jwt-secret"
export GOOGLE_PLACES_API_KEY_SECRET_NAME="nerava/google-places-api-key"

# Deploy
./scripts/deploy_api_apprunner.sh
```

**What this does:**
1. Builds Docker image from `backend/Dockerfile`
2. Pushes image to ECR: `nerava/backend:latest`
3. Creates/updates App Runner service: `nerava-api`
4. Configures custom domain: `api.nerava.network`
5. Creates Route53 CNAME record for App Runner domain association

**Expected Output:**
- Service ARN
- Service URL (App Runner default domain)
- Custom Domain: `api.nerava.network`
- Health check URL

**Wait Time:** 5-10 minutes for service to reach RUNNING status

### Step 2: Deploy Static Sites (S3 + CloudFront)

```bash
# Set API base URL (used by frontends)
export API_BASE_URL="https://api.nerava.network"

# Deploy
./scripts/deploy_static_sites.sh
```

**What this does:**
1. Builds all frontends with production environment variables
2. Creates S3 buckets (if not exist):
   - `nerava-network-landing`
   - `nerava-network-driver`
   - `nerava-network-merchant`
   - `nerava-network-admin`
   - `nerava-merchant-photos`
3. Creates Origin Access Controls (OAC) for each bucket
4. Creates CloudFront distributions:
   - Landing: `nerava.network`
   - Driver: `app.nerava.network`
   - Merchant: `merchant.nerava.network`
   - Admin: `admin.nerava.network`
   - Photos: `photos.nerava.network`
5. Uploads built assets to S3
6. Uploads merchant photos to S3
7. Creates CloudFront invalidations

**Expected Output:**
- S3 bucket names
- CloudFront distribution IDs
- CloudFront distribution domains

**Wait Time:** 5-15 minutes for CloudFront distributions to deploy

### Step 3: Configure DNS (Route53)

```bash
# Deploy DNS records
./scripts/deploy_dns.sh
```

**What this does:**
1. Finds CloudFront distribution IDs by domain alias
2. Finds App Runner service and custom domain association
3. Creates/updates Route53 A/AAAA alias records for CloudFront distributions
4. Creates/updates Route53 CNAME record for App Runner

**Expected Output:**
- Route53 change IDs
- DNS propagation status

**Wait Time:** 5-15 minutes for DNS propagation

### Step 4: Validate Deployment

```bash
# Validate all endpoints
./scripts/validate_deployment.sh
```

**What this tests:**
- DNS resolution for all domains
- SSL certificates
- API health endpoints
- API OTP endpoints
- Frontend page loads
- CORS configuration
- Merchant photos loading

**Expected Output:**
- Test results (Pass/Warn/Fail)
- Summary with counts
- Manual verification checklist

## Complete Deployment Command Sequence

```bash
# 1. Set environment variables
export DATABASE_URL="postgresql://postgres:<PASSWORD>@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"
export JWT_SECRET="<your-secure-secret>"
export ENV="prod"
export API_BASE_URL="https://api.nerava.network"

# 2. Deploy backend
./scripts/deploy_api_apprunner.sh

# 3. Deploy frontends
./scripts/deploy_static_sites.sh

# 4. Configure DNS
./scripts/deploy_dns.sh

# 5. Validate
./scripts/validate_deployment.sh
```

## Troubleshooting

### Backend Issues

#### App Runner service fails to start
```bash
# Check CloudWatch logs
aws logs tail /aws/apprunner/nerava-api/service --follow --region us-east-1

# Check service status
aws apprunner describe-service --service-arn <arn> --region us-east-1
```

**Common Issues:**
- Database connection failures: Check `DATABASE_URL` and RDS security groups
- Missing environment variables: Verify all required vars are set
- Health check failures: Check `/health` endpoint responds correctly

#### Custom domain not associating
```bash
# Check domain association status
aws apprunner describe-custom-domains --service-arn <arn> --region us-east-1

# Check Route53 CNAME record
aws route53 list-resource-record-sets --hosted-zone-id Z03087823KHR6VJQ9AGZL --query "ResourceRecordSets[?Name=='api.nerava.network']"
```

**Common Issues:**
- Certificate validation pending: Wait for DNS propagation
- CNAME record missing: Run `deploy_api_apprunner.sh` again

### Frontend Issues

#### CloudFront distribution not deploying
```bash
# Check distribution status
aws cloudfront get-distribution --id <distribution-id>

# Check distribution config
aws cloudfront get-distribution-config --id <distribution-id>
```

**Common Issues:**
- Invalid certificate: Ensure ACM cert is in `us-east-1`
- OAC configuration: Verify bucket policy allows CloudFront access
- S3 bucket not found: Run `deploy_static_sites.sh` to create buckets

#### Frontend not loading
```bash
# Check S3 bucket contents
aws s3 ls s3://nerava-network-driver/

# Check CloudFront cache
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

**Common Issues:**
- Build failed: Check Node.js version and npm install output
- Wrong API URL: Verify `VITE_API_BASE_URL` is set correctly
- Cache issues: Create CloudFront invalidation

### DNS Issues

#### DNS not resolving
```bash
# Check DNS propagation
dig api.nerava.network
dig app.nerava.network

# Check Route53 records
aws route53 list-resource-record-sets --hosted-zone-id Z03087823KHR6VJQ9AGZL
```

**Common Issues:**
- DNS propagation delay: Wait 5-15 minutes
- Wrong record type: Verify A/AAAA aliases for CloudFront, CNAME for App Runner
- TTL too high: Records update after TTL expires

### API Connectivity Issues

#### CORS errors in browser
```bash
# Check CORS configuration
curl -H "Origin: https://app.nerava.network" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://api.nerava.network/v1/auth/otp/start -v
```

**Common Issues:**
- Missing origin in `ALLOWED_ORIGINS`: Add all production domains
- Wildcard CORS in production: Use explicit origins list

#### OTP endpoints not working
```bash
# Test OTP start
curl -X POST https://api.nerava.network/v1/auth/otp/start \
     -H "Content-Type: application/json" \
     -d '{"phone_number":"+15551234567"}'
```

**Common Issues:**
- OTP provider not configured: Set `OTP_PROVIDER` env var
- Rate limiting: Check rate limit configuration
- Database connection: Verify RDS is accessible

## Manual Verification Checklist

After deployment, manually verify:

- [ ] Landing page loads: https://nerava.network
- [ ] Driver app loads: https://app.nerava.network
- [ ] Driver app can call API (check browser console)
- [ ] OTP flow works: Enter phone number, receive OTP
- [ ] Merchant portal loads: https://merchant.nerava.network
- [ ] Admin portal loads: https://admin.nerava.network
- [ ] Merchant photos load: https://photos.nerava.network/asadas_grill/asadas_grill_01.jpg
- [ ] API health check: https://api.nerava.network/health
- [ ] API cluster endpoint: https://api.nerava.network/v1/pilot/party/cluster

## Updating Deployment

### Update Backend
```bash
# Make code changes, then:
export DATABASE_URL="..." # Keep existing
export JWT_SECRET="..." # Keep existing
./scripts/deploy_api_apprunner.sh
```

### Update Frontend
```bash
# Make code changes, then:
export API_BASE_URL="https://api.nerava.network"
./scripts/deploy_static_sites.sh
```

### Update Merchant Photos
```bash
# Add new photos to merchant_photos_asadas_grill/ or backend/static/merchant_photos_google/
./scripts/deploy_static_sites.sh
# This will upload photos and create CloudFront invalidation
```

## Cost Optimization

- **CloudFront Caching**: Static assets cached for 1 year, HTML files no-cache
- **S3 Storage**: Only pay for storage used
- **App Runner**: Pay per request and compute time
- **Route53**: $0.50 per hosted zone per month

## Security Considerations

- **S3 Buckets**: Private with OAC (no public access)
- **CloudFront**: HTTPS only, ACM certificate required
- **App Runner**: VPC connector if RDS is private
- **CORS**: Explicit origins only (no wildcards in production)
- **Secrets**: Use AWS Secrets Manager for sensitive values

## Support

For issues or questions:
1. Check CloudWatch logs for errors
2. Review script output for warnings
3. Run validation script to identify issues
4. Check AWS service health dashboards


