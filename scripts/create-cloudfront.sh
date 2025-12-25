#!/bin/bash
# Create CloudFront distribution for ui-mobile frontend

set -e

S3_BUCKET="${S3_BUCKET:-}"  # Must be set
REGION="${AWS_REGION:-us-east-1}"
DISTRIBUTION_COMMENT="${DISTRIBUTION_COMMENT:-Nerava Frontend}"

if [ -z "$S3_BUCKET" ]; then
    echo "ERROR: S3_BUCKET must be set"
    echo "Usage: S3_BUCKET='your-bucket-name' ./scripts/create-cloudfront.sh"
    exit 1
fi

echo "=== Creating CloudFront Distribution ==="
echo "S3 Bucket: $S3_BUCKET"
echo "Region: $REGION"
echo ""

# Create Origin Access Control (OAC) for S3
echo "Creating Origin Access Control..."
OAC_NAME="nerava-s3-oac-$(date +%s)"
OAC_RESPONSE=$(aws cloudfront create-origin-access-control \
    --origin-access-control-config \
    Name="$OAC_NAME",OriginAccessControlOriginType=s3,SigningBehavior=always,SigningProtocol=sigv4 \
    --region "$REGION" 2>/dev/null || echo "")

if [ -z "$OAC_RESPONSE" ]; then
    echo "ERROR: Failed to create Origin Access Control"
    exit 1
fi

OAC_ID=$(echo "$OAC_RESPONSE" | jq -r '.OriginAccessControl.Id')
echo "Created OAC: $OAC_ID"

# Get S3 bucket region
BUCKET_REGION=$(aws s3api get-bucket-location --bucket "$S3_BUCKET" --region "$REGION" | jq -r '.LocationConstraint // "us-east-1"')
S3_DOMAIN="$S3_BUCKET.s3.$BUCKET_REGION.amazonaws.com"

# Create CloudFront distribution config
cat > /tmp/cloudfront-config.json <<EOF
{
  "CallerReference": "nerava-frontend-$(date +%s)",
  "Comment": "$DISTRIBUTION_COMMENT",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-$S3_BUCKET",
        "DomainName": "$S3_DOMAIN",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        },
        "OriginAccessControlId": "$OAC_ID"
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-$S3_BUCKET",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 3,
      "Items": ["GET", "HEAD", "OPTIONS"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000,
    "Compress": true
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
  "Enabled": true,
  "PriceClass": "PriceClass_100"
}
EOF

echo "Creating CloudFront distribution..."
DIST_RESPONSE=$(aws cloudfront create-distribution \
    --distribution-config file:///tmp/cloudfront-config.json \
    --region "$REGION")

DIST_ID=$(echo "$DIST_RESPONSE" | jq -r '.Distribution.Id')
DIST_DOMAIN=$(echo "$DIST_RESPONSE" | jq -r '.Distribution.DomainName')

echo ""
echo "=== CloudFront Distribution Created ==="
echo "Distribution ID: $DIST_ID"
echo "Domain: $DIST_DOMAIN"
echo ""
echo "Status: Deploying (this takes 10-15 minutes)"
echo ""
echo "To check status:"
echo "  aws cloudfront get-distribution --id $DIST_ID --region $REGION --query 'Distribution.Status' --output text"
echo ""
echo "Once deployed, update:"
echo "1. Backend ALLOWED_ORIGINS env var: https://$DIST_DOMAIN"
echo "2. ui-mobile/index.html meta tag: <meta name=\"nerava-api-base\" content=\"https://your-app-runner-url\">"
echo ""
echo "Cleanup:"
rm -f /tmp/cloudfront-config.json


