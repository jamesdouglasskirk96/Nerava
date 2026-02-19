#!/bin/bash
# Script to update Route53 records after CloudFront distribution is created
# Usage: ./FIX_ROUTE53_AFTER_CLOUDFRONT.sh <cloudfront-distribution-id>

set -euo pipefail

CLOUDFRONT_DIST_ID="${1:-}"
HOSTED_ZONE_ID="Z03087823KHR6VJQ9AGZL"

if [ -z "$CLOUDFRONT_DIST_ID" ]; then
    echo "ERROR: CloudFront Distribution ID required"
    echo "Usage: $0 <cloudfront-distribution-id>"
    echo ""
    echo "To find your CloudFront distribution ID:"
    echo "  aws cloudfront list-distributions --query \"DistributionList.Items[?contains(Aliases.Items, 'nerava.network')].{Id:Id,DomainName:DomainName}\" --output table"
    exit 1
fi

echo "Getting CloudFront distribution details..."
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution --id "$CLOUDFRONT_DIST_ID" --query "Distribution.DomainName" --output text)

if [ -z "$CLOUDFRONT_DOMAIN" ]; then
    echo "ERROR: Could not find CloudFront distribution with ID: $CLOUDFRONT_DIST_ID"
    exit 1
fi

echo "CloudFront Domain: $CLOUDFRONT_DOMAIN"
echo ""

# Step 1: Update root domain A record
echo "Updating nerava.network A record to point to CloudFront..."
aws route53 change-resource-record-sets \
  --hosted-zone-id "$HOSTED_ZONE_ID" \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"UPSERT\",
      \"ResourceRecordSet\": {
        \"Name\": \"nerava.network\",
        \"Type\": \"A\",
        \"AliasTarget\": {
          \"HostedZoneId\": \"Z2FDTNDATAQYW2\",
          \"DNSName\": \"$CLOUDFRONT_DOMAIN\",
          \"EvaluateTargetHealth\": false
        }
      }
    }]
  }"

echo "✅ Root domain updated"
echo ""

# Step 2: Delete www CNAME and create A record alias
echo "Deleting www CNAME record..."
aws route53 change-resource-record-sets \
  --hosted-zone-id "$HOSTED_ZONE_ID" \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"DELETE\",
      \"ResourceRecordSet\": {
        \"Name\": \"www.nerava.network\",
        \"Type\": \"CNAME\",
        \"TTL\": 300,
        \"ResourceRecords\": [{
          \"Value\": \"nerava.network\"
        }]
      }
    }]
  }" 2>/dev/null || echo "  (CNAME may not exist, continuing...)"

echo "Creating www A record alias to CloudFront..."
aws route53 change-resource-record-sets \
  --hosted-zone-id "$HOSTED_ZONE_ID" \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"UPSERT\",
      \"ResourceRecordSet\": {
        \"Name\": \"www.nerava.network\",
        \"Type\": \"A\",
        \"AliasTarget\": {
          \"HostedZoneId\": \"Z2FDTNDATAQYW2\",
          \"DNSName\": \"$CLOUDFRONT_DOMAIN\",
          \"EvaluateTargetHealth\": false
        }
      }
    }]
  }"

echo "✅ www subdomain updated"
echo ""

echo "=========================================="
echo "✅ Route53 records updated successfully!"
echo "=========================================="
echo ""
echo "DNS propagation may take 5-60 minutes."
echo ""
echo "Test with:"
echo "  curl -I https://nerava.network"
echo "  curl -I https://www.nerava.network"
echo ""
echo "Note: CloudFront distribution takes 10-15 minutes to fully deploy."
echo "Check status: aws cloudfront get-distribution --id $CLOUDFRONT_DIST_ID --query 'Distribution.Status' --output text"





