# Nerava Network Configuration Report

## Current Deployment Status

### Static Sites (S3) - ✅ Working

| Site | S3 URL | Status |
|------|--------|--------|
| Landing Page | http://nerava.network.s3-website-us-east-1.amazonaws.com | ✅ Live |
| Driver App | http://app.nerava.network.s3-website-us-east-1.amazonaws.com | ✅ Live |
| Merchant Portal | http://merchant.nerava.network.s3-website-us-east-1.amazonaws.com | ✅ Live |
| Admin Portal | http://admin.nerava.network.s3-website-us-east-1.amazonaws.com | ✅ Live |

### Backend API (App Runner) - ⚠️ Needs Fix

**Issue:** Health check fails because App Runner cannot establish database connection within timeout.

**Root Cause:** App Runner's VPC connector may not have proper NAT gateway routing to reach RDS, or the app startup is too slow.

---

## Required Network Configurations for nerava.network/app

### Option 1: CloudFront with Path-Based Routing (Recommended)

Create a CloudFront distribution that routes:
- `nerava.network/*` → S3 bucket `nerava.network` (landing page)
- `nerava.network/app/*` → S3 bucket `app.nerava.network` (driver app)

**Steps:**
1. Create CloudFront distribution with origin `nerava.network.s3-website-us-east-1.amazonaws.com`
2. Add second origin for `app.nerava.network.s3-website-us-east-1.amazonaws.com`
3. Create cache behavior: `/app/*` → driver app origin
4. Update Route53 A record to point to CloudFront distribution

### Option 2: S3 Redirect Rules

Configure S3 bucket `nerava.network` to redirect `/app/*` requests:

```xml
<RoutingRules>
  <RoutingRule>
    <Condition>
      <KeyPrefixEquals>app/</KeyPrefixEquals>
    </Condition>
    <Redirect>
      <HostName>app.nerava.network</HostName>
      <ReplaceKeyPrefixWith></ReplaceKeyPrefixWith>
    </Redirect>
  </RoutingRule>
</RoutingRules>
```

---

## DNS Configuration (Route53 Zone: Z03087823KHR6VJQ9AGZL)

### Current Records

| Record | Type | Target |
|--------|------|--------|
| nerava.network | A (Alias) | S3 website endpoint |
| app.nerava.network | A (Alias) | S3 website endpoint |
| merchant.nerava.network | A (Alias) | S3 website endpoint |
| admin.nerava.network | A (Alias) | S3 website endpoint |
| api.nerava.network | CNAME | xvrgepvyr3.us-east-1.awsapprunner.com |

### Required for HTTPS (CloudFront)

For HTTPS support, you need:
1. ACM certificate for `*.nerava.network` (already exists: `arn:aws:acm:us-east-1:566287346479:certificate/9abd6168-db05-4455-b53b-0b3d397da70d`)
2. CloudFront distributions for each site
3. Update Route53 A records to point to CloudFront

---

## Backend Deployment Alternatives

### Alternative 1: ECS Fargate (Recommended)

Use the existing ECS cluster `nerava-cluster` with Fargate:
- Better network control
- VPC networking built-in
- ALB integration

**Steps:**
```bash
# 1. Create ECS task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 2. Create ECS service with ALB
aws ecs create-service --cluster nerava-cluster --service-name nerava-api ...
```

### Alternative 2: Fix App Runner

Make the backend app more resilient to slow database connections:
1. Add retry logic for database connections
2. Increase health check timeout (already at 10s)
3. Make health endpoint return 200 even if DB is not ready

---

## AWS Resources Summary

| Resource | ARN/ID |
|----------|--------|
| Route53 Zone | Z03087823KHR6VJQ9AGZL |
| ACM Certificate | arn:aws:acm:us-east-1:566287346479:certificate/9abd6168-db05-4455-b53b-0b3d397da70d |
| RDS Instance | nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com |
| ECR Repository | 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava/backend |
| ECS Cluster | nerava-cluster |
| VPC Connector | arn:aws:apprunner:us-east-1:566287346479:vpcconnector/nerava-vpc-connector/1/b07c0001ddf341b8b426d7fa83d93ad8 |

---

## Next Steps

1. **For nerava.network/app routing:** Set up CloudFront distribution with path-based routing
2. **For backend:** Either fix App Runner health check or migrate to ECS Fargate
3. **For HTTPS:** Deploy CloudFront distributions with ACM certificate
