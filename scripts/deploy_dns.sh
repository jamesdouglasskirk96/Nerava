#!/bin/bash
# Deploy Route53 DNS records for all Nerava subdomains
# This script creates/updates Route53 records pointing to CloudFront distributions and App Runner

set -euo pipefail

# Configuration
export REGION="${AWS_REGION:-us-east-1}"
export ROUTE53_ZONE_ID="${ROUTE53_ZONE_ID:-Z03087823KHR6VJQ9AGZL}"

# Domain names
export LANDING_DOMAIN="${LANDING_DOMAIN:-nerava.network}"
export DRIVER_DOMAIN="${DRIVER_DOMAIN:-app.nerava.network}"
export MERCHANT_DOMAIN="${MERCHANT_DOMAIN:-merchant.nerava.network}"
export ADMIN_DOMAIN="${ADMIN_DOMAIN:-admin.nerava.network}"
export PHOTOS_DOMAIN="${PHOTOS_DOMAIN:-photos.nerava.network}"
export API_DOMAIN="${API_DOMAIN:-api.nerava.network}"

# App Runner service name
export SERVICE_NAME="${SERVICE_NAME:-nerava-api}"

echo "=========================================="
echo "Nerava DNS Deployment"
echo "=========================================="
echo "Route53 Zone ID: $ROUTE53_ZONE_ID"
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

# Function to get CloudFront distribution ID by domain alias
get_cloudfront_dist_id() {
    local domain=$1
    local dist_id=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Aliases.Items[?@=='$domain']].Id" \
        --output text) || dist_id=""
    
    if [ -z "$dist_id" ]; then
        echo ""
        return 1
    fi
    
    echo "$dist_id"
}

# Function to get CloudFront distribution domain name
get_cloudfront_dist_domain() {
    local dist_id=$1
    aws cloudfront get-distribution --id "$dist_id" \
        --query 'Distribution.DomainName' \
        --output text
}

# Function to create/update Route53 A/AAAA alias record
create_route53_alias() {
    local record_name=$1
    local alias_target=$2
    local alias_hosted_zone_id=$3
    local record_type="${4:-A}"
    
    echo "Creating/updating Route53 $record_type record: $record_name -> $alias_target"
    
    # Check if record exists
    EXISTING_RECORD=$(aws route53 list-resource-record-sets \
        --hosted-zone-id "$ROUTE53_ZONE_ID" \
        --query "ResourceRecordSets[?Name=='$record_name.' && Type=='$record_type']" \
        --output json) || EXISTING_RECORD="[]"
    
    if [ "$EXISTING_RECORD" != "[]" ]; then
        echo "  Record exists, updating..."
        ACTION="UPSERT"
    else
        echo "  Creating new record..."
        ACTION="UPSERT"
    fi
    
    # Create change batch
    cat > /tmp/route53-change-$record_name.json <<EOF
{
  "Changes": [{
    "Action": "$ACTION",
    "ResourceRecordSet": {
      "Name": "$record_name",
      "Type": "$record_type",
      "AliasTarget": {
        "DNSName": "$alias_target",
        "EvaluateTargetHealth": false,
        "HostedZoneId": "$alias_hosted_zone_id"
      }
    }
  }]
}
EOF
    
    CHANGE_RESPONSE=$(aws route53 change-resource-record-sets \
        --hosted-zone-id "$ROUTE53_ZONE_ID" \
        --change-batch file:///tmp/route53-change-$record_name.json \
        --output json)
    
    CHANGE_ID=$(echo "$CHANGE_RESPONSE" | jq -r '.ChangeInfo.Id')
    echo "  ✅ Record $ACTION completed. Change ID: $CHANGE_ID"
}

# Function to create/update Route53 CNAME record
create_route53_cname() {
    local record_name=$1
    local cname_value=$2
    
    echo "Creating/updating Route53 CNAME record: $record_name -> $cname_value"
    
    cat > /tmp/route53-change-$record_name.json <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "$record_name",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{"Value": "$cname_value"}]
    }
  }]
}
EOF
    
    CHANGE_RESPONSE=$(aws route53 change-resource-record-sets \
        --hosted-zone-id "$ROUTE53_ZONE_ID" \
        --change-batch file:///tmp/route53-change-$record_name.json \
        --output json)
    
    CHANGE_ID=$(echo "$CHANGE_RESPONSE" | jq -r '.ChangeInfo.Id')
    echo "  ✅ CNAME record created. Change ID: $CHANGE_ID"
}

# Get CloudFront distribution IDs
echo "=== Finding CloudFront Distributions ==="
LANDING_DIST_ID=$(get_cloudfront_dist_id "$LANDING_DOMAIN")
DRIVER_DIST_ID=$(get_cloudfront_dist_id "$DRIVER_DOMAIN")
MERCHANT_DIST_ID=$(get_cloudfront_dist_id "$MERCHANT_DOMAIN")
ADMIN_DIST_ID=$(get_cloudfront_dist_id "$ADMIN_DOMAIN")
PHOTOS_DIST_ID=$(get_cloudfront_dist_id "$PHOTOS_DOMAIN")

if [ -z "$LANDING_DIST_ID" ]; then
    echo "❌ ERROR: CloudFront distribution not found for $LANDING_DOMAIN"
    echo "Run scripts/deploy_static_sites.sh first"
    exit 1
fi

echo "✅ Found distributions:"
echo "  Landing: $LANDING_DIST_ID"
echo "  Driver: $DRIVER_DIST_ID"
echo "  Merchant: $MERCHANT_DIST_ID"
echo "  Admin: $ADMIN_DIST_ID"
echo "  Photos: $PHOTOS_DIST_ID"
echo ""

# Get CloudFront distribution domains and hosted zone IDs
# CloudFront uses a fixed hosted zone ID: Z2FDTNDATAQYW2
CLOUDFRONT_HOSTED_ZONE_ID="Z2FDTNDATAQYW2"

LANDING_DIST_DOMAIN=$(get_cloudfront_dist_domain "$LANDING_DIST_ID")
DRIVER_DIST_DOMAIN=$(get_cloudfront_dist_domain "$DRIVER_DIST_ID")
MERCHANT_DIST_DOMAIN=$(get_cloudfront_dist_domain "$MERCHANT_DIST_ID")
ADMIN_DIST_DOMAIN=$(get_cloudfront_dist_domain "$ADMIN_DIST_ID")
PHOTOS_DIST_DOMAIN=$(get_cloudfront_dist_domain "$PHOTOS_DIST_ID")

echo "CloudFront Distribution Domains:"
echo "  Landing: $LANDING_DIST_DOMAIN"
echo "  Driver: $DRIVER_DIST_DOMAIN"
echo "  Merchant: $MERCHANT_DIST_DOMAIN"
echo "  Admin: $ADMIN_DIST_DOMAIN"
echo "  Photos: $PHOTOS_DIST_DOMAIN"
echo ""

# Get App Runner service ARN and domain association
echo "=== Finding App Runner Service ==="
SERVICE_ARN=$(aws apprunner list-services --region "$REGION" \
    --query "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceArn" \
    --output text) || SERVICE_ARN=""

if [ -z "$SERVICE_ARN" ]; then
    echo "❌ ERROR: App Runner service '$SERVICE_NAME' not found"
    echo "Run scripts/deploy_api_apprunner.sh first"
    exit 1
fi

echo "✅ Found App Runner service: $SERVICE_ARN"

# Get App Runner custom domain
APP_RUNNER_DOMAIN=$(aws apprunner describe-custom-domains \
    --service-arn "$SERVICE_ARN" \
    --region "$REGION" \
    --query "CustomDomains[?Domain=='$API_DOMAIN']" \
    --output json) || APP_RUNNER_DOMAIN="[]"

if [ "$APP_RUNNER_DOMAIN" = "[]" ]; then
    echo "⚠️  WARNING: App Runner custom domain '$API_DOMAIN' not found"
    echo "The domain may still be provisioning. Check App Runner service status."
    echo "You may need to run scripts/deploy_api_apprunner.sh to associate the domain."
else
    APP_RUNNER_CNAME=$(echo "$APP_RUNNER_DOMAIN" | jq -r '.[0].CertificateValidationRecords[0].Name // ""')
    APP_RUNNER_CNAME_VALUE=$(echo "$APP_RUNNER_DOMAIN" | jq -r '.[0].CertificateValidationRecords[0].Value // ""')
    
    if [ -n "$APP_RUNNER_CNAME" ] && [ -n "$APP_RUNNER_CNAME_VALUE" ]; then
        echo "✅ Found App Runner CNAME: $APP_RUNNER_CNAME -> $APP_RUNNER_CNAME_VALUE"
    fi
fi

echo ""

# Create Route53 records for CloudFront distributions
echo "=== Creating Route53 Records for CloudFront ==="

create_route53_alias "$LANDING_DOMAIN" "$LANDING_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "A"
create_route53_alias "$LANDING_DOMAIN" "$LANDING_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "AAAA"

create_route53_alias "$DRIVER_DOMAIN" "$DRIVER_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "A"
create_route53_alias "$DRIVER_DOMAIN" "$DRIVER_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "AAAA"

create_route53_alias "$MERCHANT_DOMAIN" "$MERCHANT_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "A"
create_route53_alias "$MERCHANT_DOMAIN" "$MERCHANT_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "AAAA"

create_route53_alias "$ADMIN_DOMAIN" "$ADMIN_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "A"
create_route53_alias "$ADMIN_DOMAIN" "$ADMIN_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "AAAA"

create_route53_alias "$PHOTOS_DOMAIN" "$PHOTOS_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "A"
create_route53_alias "$PHOTOS_DOMAIN" "$PHOTOS_DIST_DOMAIN" "$CLOUDFRONT_HOSTED_ZONE_ID" "AAAA"

# Create Route53 record for App Runner (if CNAME is available)
if [ -n "$APP_RUNNER_CNAME" ] && [ -n "$APP_RUNNER_CNAME_VALUE" ]; then
    echo ""
    echo "=== Creating Route53 Record for App Runner ==="
    create_route53_cname "$APP_RUNNER_CNAME" "$APP_RUNNER_CNAME_VALUE"
else
    echo ""
    echo "⚠️  Skipping App Runner DNS record (domain not yet associated)"
    echo "Run scripts/deploy_api_apprunner.sh to associate the custom domain first"
fi

echo ""
echo "=== Waiting for DNS Propagation ==="
echo "DNS changes are propagating. This may take a few minutes..."
echo "You can check propagation status with:"
echo "  dig $LANDING_DOMAIN"
echo "  dig $DRIVER_DOMAIN"
echo "  dig $API_DOMAIN"

echo ""
echo "=========================================="
echo "✅ DNS Deployment Complete"
echo "=========================================="
echo ""
echo "Route53 Records Created/Updated:"
echo "  $LANDING_DOMAIN -> CloudFront ($LANDING_DIST_ID)"
echo "  $DRIVER_DOMAIN -> CloudFront ($DRIVER_DIST_ID)"
echo "  $MERCHANT_DOMAIN -> CloudFront ($MERCHANT_DIST_ID)"
echo "  $ADMIN_DOMAIN -> CloudFront ($ADMIN_DIST_ID)"
echo "  $PHOTOS_DOMAIN -> CloudFront ($PHOTOS_DIST_ID)"
if [ -n "$APP_RUNNER_CNAME" ]; then
    echo "  $APP_RUNNER_CNAME -> App Runner ($APP_RUNNER_CNAME_VALUE)"
fi
echo ""
echo "Next Steps:"
echo "1. Wait for DNS propagation (5-15 minutes)"
echo "2. Run scripts/validate_deployment.sh to verify all endpoints"
echo "3. Test each subdomain in a browser"


