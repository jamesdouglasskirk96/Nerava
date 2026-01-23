#!/bin/bash
# Script to update App Runner service with PostHog API key

set -euo pipefail

export REGION="${AWS_REGION:-us-east-1}"
export SERVICE_NAME="${SERVICE_NAME:-nerava-backend}"
export POSTHOG_API_KEY="${POSTHOG_API_KEY:-}"
export POSTHOG_HOST="${POSTHOG_HOST:-https://app.posthog.com}"
export ANALYTICS_ENABLED="${ANALYTICS_ENABLED:-true}"

if [ -z "$POSTHOG_API_KEY" ]; then
    echo "❌ ERROR: POSTHOG_API_KEY is required"
    echo "Usage: POSTHOG_API_KEY='phc_xxx' ./scripts/update_posthog.sh"
    exit 1
fi

echo "=== Updating App Runner Service with PostHog Configuration ==="
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "PostHog Host: $POSTHOG_HOST"
echo "Analytics Enabled: $ANALYTICS_ENABLED"
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

# Create update configuration with PostHog added
echo "Creating update configuration..."
cat > /tmp/apprunner-posthog-update.json <<EOF
{
  "ImageRepository": {
    "ImageIdentifier": "$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageIdentifier')",
    "ImageConfiguration": {
      "Port": "$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageConfiguration.Port // 8001')",
      "RuntimeEnvironmentVariables": $(echo "$CURRENT_ENV_VARS" | jq --arg key "$POSTHOG_API_KEY" --arg host "$POSTHOG_HOST" --arg enabled "$ANALYTICS_ENABLED" '. + {POSTHOG_API_KEY: $key, POSTHOG_HOST: $host, ANALYTICS_ENABLED: $enabled}')
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
    --source-configuration file:///tmp/apprunner-posthog-update.json \
    --output json > /tmp/apprunner-update-response.json

echo "✅ Service update initiated"
echo ""
echo "The service will restart with the new PostHog configuration."
echo "Check status with:"
echo "  aws apprunner describe-service --service-arn $SERVICE_ARN --region $REGION"
