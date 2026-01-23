# Driver App Deployment Guide

This guide covers deploying the Nerava Driver App to AWS using S3 + CloudFront.

## Prerequisites

- AWS CLI configured with appropriate permissions
- GitHub repository with Actions enabled
- AWS account with permissions to create S3 buckets, CloudFront distributions, and IAM roles (if using OIDC)

## Infrastructure Setup

### Step 1: Create CloudFormation Stack

Deploy the infrastructure using the CloudFormation template:

```bash
cd nerava-app-driver
aws cloudformation create-stack \
  --stack-name nerava-driver-app \
  --template-body file://infrastructure/cloudformation.yml \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM
```

**Note:** CloudFront distributions must be created in `us-east-1` region, even if your S3 bucket is in another region.

### Step 2: Wait for Stack Creation

Monitor the stack creation:

```bash
aws cloudformation wait stack-create-complete \
  --stack-name nerava-driver-app \
  --region us-east-1
```

### Step 3: Get Stack Outputs

Retrieve the required values for GitHub secrets:

```bash
aws cloudformation describe-stacks \
  --stack-name nerava-driver-app \
  --region us-east-1 \
  --query 'Stacks[0].Outputs' \
  --output table
```

You'll need:
- `S3BucketName` - S3 bucket name
- `CloudFrontDistributionId` - CloudFront distribution ID
- `CloudFrontDomainName` - CloudFront domain name (e.g., `d1234abcd.cloudfront.net`)

## GitHub Secrets Configuration

### Option A: Using OIDC (Recommended)

OIDC is more secure as it doesn't require long-lived AWS access keys.

#### 1. Create IAM Role for GitHub Actions

Create an IAM role with trust policy allowing GitHub OIDC:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/YOUR_REPO:*"
        }
      }
    }
  ]
}
```

#### 2. Attach Permissions Policy

The role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::nerava-driver-app-*",
        "arn:aws:s3:::nerava-driver-app-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetDistribution"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 3. Configure GitHub Secret

In GitHub repository settings → Secrets and variables → Actions, add:

- `AWS_ROLE_ARN`: The ARN of the IAM role created above (e.g., `arn:aws:iam::123456789012:role/github-actions-role`)

#### 4. Update Deploy Workflow

Uncomment the OIDC lines in `.github/workflows/deploy.yml`:

```yaml
role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
aws-region: us-east-1
```

And comment out the static key lines.

### Option B: Using Static AWS Keys (Not Recommended)

If you cannot use OIDC, configure these GitHub secrets:

- `AWS_ACCESS_KEY_ID`: AWS access key ID (shared with other apps)
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key (shared with other apps)
- `AWS_S3_BUCKET_DRIVER`: S3 bucket name for driver app (from stack outputs)
- `AWS_CLOUDFRONT_DISTRIBUTION_ID_DRIVER`: CloudFront distribution ID for driver app (from stack outputs)

**Security Note:** Static keys are less secure. Rotate them regularly and use least-privilege IAM policies.

## Deployment Process

### Automatic Deployment

The app automatically deploys when:
1. Code is pushed to the `main` branch
2. Files in `nerava-app-driver/` directory change
3. CI checks pass successfully

The deployment workflow:
1. Runs CI checks (lint, build, tests)
2. Builds the application (`npm run build`)
3. Uploads assets to S3 with proper cache headers:
   - `index.html` → `Cache-Control: no-cache`
   - `assets/*` → `Cache-Control: public,max-age=31536000,immutable`
4. Invalidates CloudFront cache for `/index.html` and `/assets/*`
5. Verifies deployment by checking CloudFront URL

### Manual Deployment

To deploy manually:

```bash
cd nerava-app-driver

# Build the app
npm ci
npm run build

# Deploy to S3
aws s3 sync dist/assets/ s3://YOUR_BUCKET_NAME/assets/ \
  --cache-control "public,max-age=31536000,immutable" \
  --delete

aws s3 cp dist/index.html s3://YOUR_BUCKET_NAME/index.html \
  --cache-control "no-cache"

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/index.html" "/assets/*"
```

## Deployment Verification Checklist

After deployment, verify:

- [ ] **CloudFront URL returns app**: Visit `https://YOUR_DISTRIBUTION_ID.cloudfront.net`
- [ ] **SPA routing works**: Navigate to a non-existent route (e.g., `/test-route`) - should show app, not 404
- [ ] **Assets have long cache**: Check response headers for `assets/*` files - should have `Cache-Control: public,max-age=31536000,immutable`
- [ ] **index.html has no-cache**: Check response header for `index.html` - should have `Cache-Control: no-cache` or short TTL
- [ ] **HTTPS redirect works**: Visit HTTP URL - should redirect to HTTPS
- [ ] **App functionality**: Test critical user flows in the deployed app

### Quick Verification Commands

```bash
# Get CloudFront URL
DIST_ID=$(aws cloudformation describe-stacks \
  --stack-name nerava-driver-app \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
  --output text)

DOMAIN=$(aws cloudformation describe-stacks \
  --stack-name nerava-driver-app \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomainName`].OutputValue' \
  --output text)

echo "CloudFront URL: https://$DOMAIN"

# Check index.html
curl -I "https://$DOMAIN/index.html"

# Check asset cache headers
curl -I "https://$DOMAIN/assets/index-*.js" | grep -i cache-control

# Test SPA routing (should return 200, not 404)
curl -I "https://$DOMAIN/nonexistent-route"
```

## Troubleshooting

### CloudFormation Stack Creation Fails

**Error: "OriginAccessControlId and S3OriginConfig cannot both be specified"**
- This should be fixed in the template. Ensure you're using the latest version.

**Error: "Bucket already exists"**
- The bucket name includes your AWS account ID. If it still conflicts, modify the bucket name in the template.

### Deployment Fails: "Access Denied"

- Verify IAM permissions for S3 and CloudFront
- Check GitHub secrets are correctly configured
- If using OIDC, verify the IAM role trust policy matches your GitHub repository

### CloudFront Shows Old Content

- CloudFront invalidation can take 1-5 minutes
- Check invalidation status:
  ```bash
  aws cloudfront list-invalidations --distribution-id YOUR_DISTRIBUTION_ID
  ```
- Ensure cache headers are set correctly on S3 objects

### SPA Routing Returns 404

- Verify CloudFormation template has `CustomErrorResponses` configured:
  - 403 → 200 `/index.html`
  - 404 → 200 `/index.html`
- Check CloudFront distribution settings

### Assets Not Loading

- Verify `assets/` directory exists in S3
- Check CloudFront origin path configuration
- Ensure bucket policy allows CloudFront access via OAC

## Stack Updates

To update the infrastructure:

```bash
aws cloudformation update-stack \
  --stack-name nerava-driver-app \
  --template-body file://infrastructure/cloudformation.yml \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM
```

## Stack Deletion

To delete the stack (removes S3 bucket and CloudFront distribution):

```bash
# Empty S3 bucket first (CloudFormation won't delete non-empty buckets)
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name nerava-driver-app \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

aws s3 rm s3://$BUCKET_NAME --recursive

# Delete stack
aws cloudformation delete-stack \
  --stack-name nerava-driver-app \
  --region us-east-1
```

## Monitoring

### CloudFront Metrics

Monitor CloudFront distribution in AWS Console:
- Requests
- Error rates (4xx, 5xx)
- Cache hit ratio
- Origin latency

### S3 Metrics

Monitor S3 bucket:
- Storage size
- Request metrics
- Data transfer

## Cost Optimization

- **CloudFront**: Uses `PriceClass_100` (US, Canada, Europe) - cheapest option
- **S3**: Standard storage, minimal requests for static hosting
- **Invalidations**: Limited to `/index.html` and `/assets/*` to reduce costs

Estimated monthly cost for low traffic (< 10k requests/month):
- S3: < $1
- CloudFront: < $1
- **Total: < $2/month**

## Security Best Practices

1. **Use OIDC** instead of static AWS keys
2. **Enable S3 bucket versioning** (optional, for rollback capability)
3. **Enable CloudFront access logs** (optional, for debugging)
4. **Use AWS WAF** (optional, for DDoS protection)
5. **Rotate credentials** regularly if using static keys
6. **Monitor CloudTrail** for unauthorized access

## Support

For issues or questions:
1. Check GitHub Actions logs for deployment errors
2. Review CloudFormation stack events in AWS Console
3. Check CloudFront distribution status
4. Verify S3 bucket permissions and policies

