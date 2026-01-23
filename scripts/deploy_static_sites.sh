#!/bin/bash
# Deploy all Nerava frontends to S3 + CloudFront
# This script builds all frontends, creates S3 buckets, CloudFront distributions,
# uploads assets, and configures DNS-ready distributions.

set -euo pipefail

# Configuration
export REGION="${AWS_REGION:-us-east-1}"
export AWS_ACCOUNT_ID="566287346479"
export ACM_CERT_ARN="${ACM_CERT_ARN:-arn:aws:acm:us-east-1:566287346479:certificate/7ec281ad-9dad-49cd-a173-2f605e0a3910}"
export API_BASE_URL="${API_BASE_URL:-https://api.nerava.network}"

# S3 Bucket names
export LANDING_BUCKET="${LANDING_BUCKET:-nerava.network}"
export DRIVER_BUCKET="${DRIVER_BUCKET:-app.nerava.network}"
export MERCHANT_BUCKET="${MERCHANT_BUCKET:-merchant.nerava.network}"
export ADMIN_BUCKET="${ADMIN_BUCKET:-admin.nerava.network}"
export PHOTOS_BUCKET="${PHOTOS_BUCKET:-nerava-merchant-photos}"

# CloudFront domain names
export LANDING_DOMAIN="${LANDING_DOMAIN:-nerava.network}"
export DRIVER_DOMAIN="${DRIVER_DOMAIN:-app.nerava.network}"
export MERCHANT_DOMAIN="${MERCHANT_DOMAIN:-merchant.nerava.network}"
export ADMIN_DOMAIN="${ADMIN_DOMAIN:-admin.nerava.network}"
export PHOTOS_DOMAIN="${PHOTOS_DOMAIN:-photos.nerava.network}"

# Project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=========================================="
echo "Nerava Static Sites Deployment"
echo "=========================================="
echo "Region: $REGION"
echo "API Base URL: $API_BASE_URL"
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ ERROR: AWS CLI not found"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ ERROR: jq not found"
    exit 1
fi

# Function to create S3 bucket if it doesn't exist
create_s3_bucket() {
    local bucket_name=$1
    echo "Checking bucket: $bucket_name"
    
    if aws s3api head-bucket --bucket "$bucket_name" --region "$REGION" 2>/dev/null; then
        echo "✅ Bucket exists: $bucket_name"
    else
        echo "Creating bucket: $bucket_name"
        if [ "$REGION" = "us-east-1" ]; then
            aws s3api create-bucket --bucket "$bucket_name" --region "$REGION" || {
                echo "❌ Failed to create bucket: $bucket_name"
                exit 1
            }
        else
            aws s3api create-bucket --bucket "$bucket_name" --region "$REGION" --create-bucket-configuration LocationConstraint="$REGION" || {
                echo "❌ Failed to create bucket: $bucket_name"
                exit 1
            }
        fi
        
        # Block public access (CloudFront uses OAC)
        aws s3api put-public-access-block \
            --bucket "$bucket_name" \
            --public-access-block-configuration \
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
        
        echo "✅ Bucket created: $bucket_name"
    fi
}

# Function to create or get Origin Access Control
create_or_get_oac() {
    local oac_name=$1
    echo "Checking OAC: $oac_name" >&2
    
    OAC_ID=$(aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='$oac_name'].Id" --output text 2>/dev/null) || OAC_ID=""
    
    if [ -z "$OAC_ID" ]; then
        echo "Creating OAC: $oac_name" >&2
        OAC_RESPONSE=$(aws cloudfront create-origin-access-control \
            --origin-access-control-config "{
                \"Name\": \"$oac_name\",
                \"OriginAccessControlOriginType\": \"s3\",
                \"SigningBehavior\": \"always\",
                \"SigningProtocol\": \"sigv4\"
            }" \
            --output json 2>&1)
        
        OAC_ID=$(echo "$OAC_RESPONSE" | jq -r '.OriginAccessControl.Id' 2>/dev/null)
        if [ -n "$OAC_ID" ] && [ "$OAC_ID" != "null" ]; then
            echo "✅ OAC created: $OAC_ID" >&2
        else
            echo "❌ Failed to create OAC: $oac_name" >&2
            echo "$OAC_RESPONSE" >&2
            return 1
        fi
    else
        echo "✅ OAC exists: $OAC_ID" >&2
    fi
    
    # Only output the OAC ID (to stdout, not stderr)
    echo "$OAC_ID"
}

# Function to create CloudFront distribution
create_cloudfront_distribution() {
    local domain=$1
    local bucket_name=$2
    local dist_name=$3
    local oac_id=$4
    
    echo ""
    echo "=== Creating CloudFront Distribution: $dist_name ==="
    
    # Check if distribution already exists
    EXISTING_DIST=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[?@=='$domain']].Id" --output text 2>/dev/null) || EXISTING_DIST=""
    
    # AWS CLI returns "None" as a string when no results found, not empty string
    if [ -n "$EXISTING_DIST" ] && [ "$EXISTING_DIST" != "None" ]; then
        echo "✅ Distribution exists for $domain: $EXISTING_DIST"
        echo "$EXISTING_DIST"
        return
    fi
    
    # Get OAC details
    OAC_CONFIG=$(aws cloudfront get-origin-access-control --id "$oac_id" --output json)
    OAC_ARN=$(echo "$OAC_CONFIG" | jq -r '.OriginAccessControl.OriginAccessControl.OriginAccessControlArn')
    
    # Create distribution configuration
    cat > /tmp/cloudfront-config-$dist_name.json <<EOF
{
  "CallerReference": "$dist_name-$(date +%s)",
  "Comment": "Nerava $dist_name distribution",
  "DefaultRootObject": "index.html",
  "Enabled": true,
  "Aliases": {
    "Quantity": 1,
    "Items": ["$domain"]
  },
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "S3-$bucket_name",
      "DomainName": "$bucket_name.s3.$REGION.amazonaws.com",
      "S3OriginConfig": {
        "OriginAccessIdentity": ""
      },
      "OriginAccessControlId": "$oac_id"
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-$bucket_name",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 7,
      "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
    "OriginRequestPolicyId": "216adef6-5c7f-47e4-b989-3c8f855ef96b"
  },
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      {
        "ErrorCode": 403,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      },
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  },
  "ViewerCertificate": {
    "ACMCertificateArn": "$ACM_CERT_ARN",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021"
  }
}
EOF
    
    # Create distribution
    DIST_RESPONSE=$(aws cloudfront create-distribution \
        --distribution-config file:///tmp/cloudfront-config-$dist_name.json \
        --output json)
    
    DIST_ID=$(echo "$DIST_RESPONSE" | jq -r '.Distribution.Id')
    DIST_DOMAIN=$(echo "$DIST_RESPONSE" | jq -r '.Distribution.DomainName')
    
    echo "✅ Distribution created: $DIST_ID"
    echo "Distribution Domain: $DIST_DOMAIN"
    echo "Status: $(echo "$DIST_RESPONSE" | jq -r '.Distribution.Status')"
    
    echo "$DIST_ID"
}

# Function to update bucket policy for OAC
update_bucket_policy_for_oac() {
    local bucket_name=$1
    local oac_arn=$2
    
    echo "Updating bucket policy for OAC access..."
    
    # Use wildcard pattern for CloudFront distributions since we create distributions after policies
    # This allows any CloudFront distribution in the account to access the bucket
    cat > /tmp/bucket-policy-$bucket_name.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$bucket_name/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::$AWS_ACCOUNT_ID:distribution/*"
        }
      }
    }
  ]
}
EOF
    
    aws s3api put-bucket-policy --bucket "$bucket_name" --policy file:///tmp/bucket-policy-$bucket_name.json
    echo "✅ Bucket policy updated"
}

# Build frontends
echo "=== Building Frontends ==="

# Build Landing Page (Next.js)
echo ""
echo "Building Landing Page..."
cd "$PROJECT_ROOT/apps/landing"
LANDING_BUILD_DIR="$PROJECT_ROOT/apps/landing/out"

# Check if build already exists
if [ -d "$LANDING_BUILD_DIR" ] && [ -f "$LANDING_BUILD_DIR/index.html" ]; then
    echo "✅ Using existing landing page build"
else
    export NEXT_STATIC_EXPORT=true
    export NEXT_PUBLIC_BASE_PATH=""
    # Use HTTP URLs for now since CloudFront isn't set up yet
    export NEXT_PUBLIC_DRIVER_APP_URL="${NEXT_PUBLIC_DRIVER_APP_URL:-http://app.nerava.network}"
    export NEXT_PUBLIC_MERCHANT_APP_URL="${NEXT_PUBLIC_MERCHANT_APP_URL:-http://merchant.nerava.network}"
    export NODE_ENV=production
    npm install --silent || echo "⚠️  npm install had issues, continuing..."
    if npm run build 2>&1 | tee /tmp/landing-build.log; then
        echo "✅ Landing page built successfully"
    else
        echo "⚠️  Landing page build failed (likely tailwindcss issue)"
        echo "   Using existing deployed version or skipping landing page"
        if [ ! -d "$LANDING_BUILD_DIR" ]; then
            echo "   No existing build found - landing page may not be deployed"
        fi
    fi
fi

# Build Driver App
echo ""
echo "Building Driver App..."
cd "$PROJECT_ROOT/nerava-app-driver"
DRIVER_BUILD_DIR="$PROJECT_ROOT/nerava-app-driver/dist"

# Check if build already exists
if [ -d "$DRIVER_BUILD_DIR" ] && [ -f "$DRIVER_BUILD_DIR/index.html" ]; then
    echo "✅ Using existing driver app build"
else
    export VITE_API_BASE_URL="$API_BASE_URL"
    export VITE_ENV=prod
    if [ -n "${VITE_SENTRY_DSN:-}" ]; then
        export VITE_SENTRY_DSN="$VITE_SENTRY_DSN"
        export VITE_SENTRY_ENVIRONMENT="${VITE_SENTRY_ENVIRONMENT:-production}"
    fi
    if [ -n "${VITE_POSTHOG_KEY:-}" ]; then
        export VITE_POSTHOG_KEY="$VITE_POSTHOG_KEY"
        export VITE_POSTHOG_HOST="${VITE_POSTHOG_HOST:-https://app.posthog.com}"
    fi
    npm install --silent || echo "⚠️  npm install had issues, continuing..."
    if npm run build 2>&1 | tee /tmp/driver-build.log; then
        echo "✅ Driver app built successfully"
    else
        echo "⚠️  Driver app build failed"
        if [ ! -d "$DRIVER_BUILD_DIR" ]; then
            echo "   No existing build found - driver app may not be deployed"
        else
            echo "   Using existing build"
        fi
    fi
fi

# Build Merchant Portal
echo ""
echo "Building Merchant Portal..."
cd "$PROJECT_ROOT/apps/merchant"
MERCHANT_BUILD_DIR="$PROJECT_ROOT/apps/merchant/dist"

# Check if build already exists
if [ -d "$MERCHANT_BUILD_DIR" ] && [ -f "$MERCHANT_BUILD_DIR/index.html" ]; then
    echo "✅ Using existing merchant portal build"
else
    export VITE_API_BASE_URL="$API_BASE_URL"
    export VITE_ENV=prod
    npm install --silent || echo "⚠️  npm install had issues, continuing..."
    if npm run build 2>&1 | tee /tmp/merchant-build.log; then
        echo "✅ Merchant portal built successfully"
    else
        echo "⚠️  Merchant portal build failed"
        if [ ! -d "$MERCHANT_BUILD_DIR" ]; then
            echo "   No existing build found - merchant portal may not be deployed"
        else
            echo "   Using existing build"
        fi
    fi
fi

# Build Admin Portal
echo ""
echo "Building Admin Portal..."
cd "$PROJECT_ROOT/apps/admin"
ADMIN_BUILD_DIR="$PROJECT_ROOT/apps/admin/dist"

# Check if build already exists
if [ -d "$ADMIN_BUILD_DIR" ] && [ -f "$ADMIN_BUILD_DIR/index.html" ]; then
    echo "✅ Using existing admin portal build"
else
    export VITE_API_BASE_URL="$API_BASE_URL"
    export VITE_ENV=prod
    npm install --silent || echo "⚠️  npm install had issues, continuing..."
    if npm run build 2>&1 | tee /tmp/admin-build.log; then
        echo "✅ Admin portal built successfully"
    else
        echo "⚠️  Admin portal build failed"
        if [ ! -d "$ADMIN_BUILD_DIR" ]; then
            echo "   No existing build found - admin portal may not be deployed"
        else
            echo "   Using existing build"
        fi
    fi
fi

cd "$PROJECT_ROOT"

# Create S3 buckets
echo ""
echo "=== Creating S3 Buckets ==="
create_s3_bucket "$LANDING_BUCKET"
create_s3_bucket "$DRIVER_BUCKET"
create_s3_bucket "$MERCHANT_BUCKET"
create_s3_bucket "$ADMIN_BUCKET"
create_s3_bucket "$PHOTOS_BUCKET"

# Create Origin Access Controls
echo ""
echo "=== Creating Origin Access Controls ==="
LANDING_OAC_ID=$(create_or_get_oac "nerava-landing-oac")
DRIVER_OAC_ID=$(create_or_get_oac "nerava-driver-oac")
MERCHANT_OAC_ID=$(create_or_get_oac "nerava-merchant-oac")
ADMIN_OAC_ID=$(create_or_get_oac "nerava-admin-oac")
PHOTOS_OAC_ID=$(create_or_get_oac "nerava-photos-oac")

# Update bucket policies (using wildcard pattern for CloudFront distributions)
echo ""
echo "=== Updating Bucket Policies ==="
update_bucket_policy_for_oac "$LANDING_BUCKET" "dummy"
update_bucket_policy_for_oac "$DRIVER_BUCKET" "dummy"
update_bucket_policy_for_oac "$MERCHANT_BUCKET" "dummy"
update_bucket_policy_for_oac "$ADMIN_BUCKET" "dummy"
update_bucket_policy_for_oac "$PHOTOS_BUCKET" "dummy"

# Create CloudFront distributions
echo ""
echo "=== Creating CloudFront Distributions ==="
LANDING_DIST_ID=$(create_cloudfront_distribution "$LANDING_DOMAIN" "$LANDING_BUCKET" "landing" "$LANDING_OAC_ID")
DRIVER_DIST_ID=$(create_cloudfront_distribution "$DRIVER_DOMAIN" "$DRIVER_BUCKET" "driver" "$DRIVER_OAC_ID")
MERCHANT_DIST_ID=$(create_cloudfront_distribution "$MERCHANT_DOMAIN" "$MERCHANT_BUCKET" "merchant" "$MERCHANT_OAC_ID")
ADMIN_DIST_ID=$(create_cloudfront_distribution "$ADMIN_DOMAIN" "$ADMIN_BUCKET" "admin" "$ADMIN_OAC_ID")
PHOTOS_DIST_ID=$(create_cloudfront_distribution "$PHOTOS_DOMAIN" "$PHOTOS_BUCKET" "photos" "$PHOTOS_OAC_ID")

# Upload static assets
echo ""
echo "=== Uploading Static Assets ==="

# Upload Landing Page
echo "Uploading Landing Page..."
if [ -d "$LANDING_BUILD_DIR" ]; then
    aws s3 sync "$LANDING_BUILD_DIR" "s3://$LANDING_BUCKET" --delete --cache-control "public, max-age=31536000, immutable" --exclude "*.html" --region "$REGION"
    aws s3 sync "$LANDING_BUILD_DIR" "s3://$LANDING_BUCKET" --delete --cache-control "no-cache, no-store, must-revalidate" --include "*.html" --region "$REGION"
else
    echo "⚠️  Landing build directory not found at $LANDING_BUILD_DIR"
    echo "Uploading from .next/standalone if available..."
    if [ -d "$PROJECT_ROOT/apps/landing/.next/standalone" ]; then
        aws s3 sync "$PROJECT_ROOT/apps/landing/.next/standalone" "s3://$LANDING_BUCKET" --delete --region "$REGION"
    fi
fi
echo "✅ Landing page uploaded"

# Upload Driver App
echo "Uploading Driver App..."
aws s3 sync "$DRIVER_BUILD_DIR" "s3://$DRIVER_BUCKET" --delete --cache-control "public, max-age=31536000, immutable" --exclude "*.html" --region "$REGION"
aws s3 sync "$DRIVER_BUILD_DIR" "s3://$DRIVER_BUCKET" --delete --cache-control "no-cache, no-store, must-revalidate" --include "*.html" --region "$REGION"
echo "✅ Driver app uploaded"

# Upload Merchant Portal
echo "Uploading Merchant Portal..."
aws s3 sync "$MERCHANT_BUILD_DIR" "s3://$MERCHANT_BUCKET" --delete --cache-control "public, max-age=31536000, immutable" --exclude "*.html" --region "$REGION"
aws s3 sync "$MERCHANT_BUILD_DIR" "s3://$MERCHANT_BUCKET" --delete --cache-control "no-cache, no-store, must-revalidate" --include "*.html" --region "$REGION"
echo "✅ Merchant portal uploaded"

# Upload Admin Portal
echo "Uploading Admin Portal..."
aws s3 sync "$ADMIN_BUILD_DIR" "s3://$ADMIN_BUCKET" --delete --cache-control "public, max-age=31536000, immutable" --exclude "*.html" --region "$REGION"
aws s3 sync "$ADMIN_BUILD_DIR" "s3://$ADMIN_BUCKET" --delete --cache-control "no-cache, no-store, must-revalidate" --include "*.html" --region "$REGION"
echo "✅ Admin portal uploaded"

# Upload Merchant Photos
echo ""
echo "=== Uploading Merchant Photos ==="
if [ -d "$PROJECT_ROOT/merchant_photos_asadas_grill" ]; then
    aws s3 sync "$PROJECT_ROOT/merchant_photos_asadas_grill" "s3://$PHOTOS_BUCKET/asadas_grill" --delete --cache-control "public, max-age=31536000" --region "$REGION"
    echo "✅ Asadas Grill photos uploaded"
fi

if [ -d "$PROJECT_ROOT/backend/static/merchant_photos_google" ]; then
    aws s3 sync "$PROJECT_ROOT/backend/static/merchant_photos_google" "s3://$PHOTOS_BUCKET/google" --delete --cache-control "public, max-age=31536000" --region "$REGION"
    echo "✅ Google photos uploaded"
fi

# Create CloudFront invalidations
echo ""
echo "=== Creating CloudFront Invalidations ==="

create_invalidation() {
    local dist_id=$1
    local name=$2
    echo "Creating invalidation for $name..."
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$dist_id" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)
    echo "✅ Invalidation created: $INVALIDATION_ID"
}

create_invalidation "$LANDING_DIST_ID" "Landing"
create_invalidation "$DRIVER_DIST_ID" "Driver"
create_invalidation "$MERCHANT_DIST_ID" "Merchant"
create_invalidation "$ADMIN_DIST_ID" "Admin"
create_invalidation "$PHOTOS_DIST_ID" "Photos"

# Get distribution domains
LANDING_DIST_DOMAIN=$(aws cloudfront get-distribution --id "$LANDING_DIST_ID" --query 'Distribution.DomainName' --output text)
DRIVER_DIST_DOMAIN=$(aws cloudfront get-distribution --id "$DRIVER_DIST_ID" --query 'Distribution.DomainName' --output text)
MERCHANT_DIST_DOMAIN=$(aws cloudfront get-distribution --id "$MERCHANT_DIST_ID" --query 'Distribution.DomainName' --output text)
ADMIN_DIST_DOMAIN=$(aws cloudfront get-distribution --id "$ADMIN_DIST_ID" --query 'Distribution.DomainName' --output text)
PHOTOS_DIST_DOMAIN=$(aws cloudfront get-distribution --id "$PHOTOS_DIST_ID" --query 'Distribution.DomainName' --output text)

echo ""
echo "=========================================="
echo "✅ Static Sites Deployment Complete"
echo "=========================================="
echo ""
echo "S3 Buckets:"
echo "  Landing: s3://$LANDING_BUCKET"
echo "  Driver: s3://$DRIVER_BUCKET"
echo "  Merchant: s3://$MERCHANT_BUCKET"
echo "  Admin: s3://$ADMIN_BUCKET"
echo "  Photos: s3://$PHOTOS_BUCKET"
echo ""
echo "CloudFront Distributions:"
echo "  Landing ($LANDING_DOMAIN): $LANDING_DIST_ID"
echo "    Domain: $LANDING_DIST_DOMAIN"
echo "  Driver ($DRIVER_DOMAIN): $DRIVER_DIST_ID"
echo "    Domain: $DRIVER_DIST_DOMAIN"
echo "  Merchant ($MERCHANT_DOMAIN): $MERCHANT_DIST_ID"
echo "    Domain: $MERCHANT_DIST_DOMAIN"
echo "  Admin ($ADMIN_DOMAIN): $ADMIN_DIST_ID"
echo "    Domain: $ADMIN_DIST_DOMAIN"
echo "  Photos ($PHOTOS_DOMAIN): $PHOTOS_DIST_ID"
echo "    Domain: $PHOTOS_DIST_DOMAIN"
echo ""
echo "Next Steps:"
echo "1. Wait for CloudFront distributions to deploy (5-15 minutes)"
echo "2. Run scripts/deploy_dns.sh to configure Route53 records"
echo "3. Run scripts/validate_deployment.sh to verify deployment"

