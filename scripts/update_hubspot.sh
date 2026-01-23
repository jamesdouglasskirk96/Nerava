#!/bin/bash
# Script to update App Runner service with HubSpot credentials

set -euo pipefail

export REGION="${AWS_REGION:-us-east-1}"
export SERVICE_NAME="${SERVICE_NAME:-nerava-backend}"
export HUBSPOT_PRIVATE_APP_TOKEN="${HUBSPOT_PRIVATE_APP_TOKEN:-}"
export HUBSPOT_PORTAL_ID="${HUBSPOT_PORTAL_ID:-}"
export HUBSPOT_ENABLED="${HUBSPOT_ENABLED:-true}"
export HUBSPOT_SEND_LIVE="${HUBSPOT_SEND_LIVE:-true}"

if [ -z "$HUBSPOT_PRIVATE_APP_TOKEN" ]; then
    echo "❌ ERROR: HUBSPOT_PRIVATE_APP_TOKEN is required"
    echo "Usage: HUBSPOT_PRIVATE_APP_TOKEN='pat-xxx' HUBSPOT_PORTAL_ID='12345678' ./scripts/update_hubspot.sh"
    exit 1
fi

if [ -z "$HUBSPOT_PORTAL_ID" ]; then
    echo "❌ ERROR: HUBSPOT_PORTAL_ID is required"
    echo "Usage: HUBSPOT_PRIVATE_APP_TOKEN='pat-xxx' HUBSPOT_PORTAL_ID='12345678' ./scripts/update_hubspot.sh"
    exit 1
fi

echo "=== Updating App Runner Service with HubSpot Configuration ==="
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "HubSpot Enabled: $HUBSPOT_ENABLED"
echo "HubSpot Send Live: $HUBSPOT_SEND_LIVE"
echo "HubSpot Portal ID: $HUBSPOT_PORTAL_ID"
echo ""

# Get service ARN
SERVICE_ARN=$(aws apprunner list-services --region "$REGION" --query "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceArn" --output text)

if [ -z "$SERVICE_ARN" ]; then
    echo "❌ ERROR: Service '$SERVICE_NAME' not found"
    exit 1
fi

echo "Service ARN: $SERVICE_ARN"

# Get current configuration
echo "Fetching current service configuration..."
CURRENT_CONFIG=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --output json)

# Extract current environment variables
CURRENT_ENV_VARS=$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables // {}')

# Create update configuration with HubSpot added
echo "Creating update configuration..."
cat > /tmp/apprunner-hubspot-update.json <<EOF
{
  "ImageRepository": {
    "ImageIdentifier": "$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageIdentifier')",
    "ImageConfiguration": {
      "Port": "$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageConfiguration.Port // 8001')",
      "RuntimeEnvironmentVariables": $(echo "$CURRENT_ENV_VARS" | jq --arg token "$HUBSPOT_PRIVATE_APP_TOKEN" --arg portal "$HUBSPOT_PORTAL_ID" --arg enabled "$HUBSPOT_ENABLED" --arg live "$HUBSPOT_SEND_LIVE" '. + {HUBSPOT_PRIVATE_APP_TOKEN: $token, HUBSPOT_PORTAL_ID: $portal, HUBSPOT_ENABLED: $enabled, HUBSPOT_SEND_LIVE: $live}')
    },
    "ImageRepositoryType": "ECR"
  },
  "AutoDeploymentsEnabled": $(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.AutoDeploymentsEnabled // false')
}
EOF

# Update service
echo "Updating service..."
aws apprunner update-service \
    --service-arn "$SERVICE_ARN" \
    --region "$REGION" \
    --source-configuration file:///tmp/apprunner-hubspot-update.json \
    --output json > /tmp/apprunner-update-response.json

echo "✅ Service update initiated"
echo ""
echo "The service will restart with the new HubSpot configuration."
echo "Check status with:"
echo "  aws apprunner describe-service --service-arn $SERVICE_ARN --region $REGION"
