#!/bin/bash
# Script to update Route53 after CloudFront distribution is created
# Usage: ./setup-nerava-network-https.sh <cloudfront-distribution-id>

set -e

CLOUDFRONT_ID="${1:-}"
HOSTED_ZONE_ID="Z03087823KHR6VJQ9AGZL"

if [ -z "$CLOUDFRONT_ID" ]; then
    echo "ERROR: CloudFront Distribution ID required"
    echo "Usage: $0 <cloudfront-distribution-id>"
    echo ""
    echo "To find your CloudFront distribution ID:"
    echo "  aws cloudfront list-distributions --query \"DistributionList.Items[?Aliases.Items[?contains(@, 'nerava.network')]].{Id:Id,DomainName:DomainName}\" --output table"
    exit 1
fi

echo "Getting CloudFront distribution details..."
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution --id "$CLOUDFRONT_ID" --query "Distribution.DomainName" --output text)

if [ -z "$CLOUDFRONT_DOMAIN" ]; then
    echo "ERROR: Could not find CloudFront distribution with ID: $CLOUDFRONT_ID"
    exit 1
fi

echo "CloudFront Domain: $CLOUDFRONT_DOMAIN"
echo ""

# Update nerava.network A record
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

echo ""
echo "✅ Route53 updated successfully!"
echo ""
echo "DNS propagation may take a few minutes."
echo "Test with: curl -I https://nerava.network"
echo ""
echo "Note: CloudFront distribution takes 10-15 minutes to fully deploy."
echo "Check status: aws cloudfront get-distribution --id $CLOUDFRONT_ID --query 'Distribution.Status' --output text"


