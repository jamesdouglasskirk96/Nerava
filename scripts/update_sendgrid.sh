#!/bin/bash
# Script to update App Runner service with SendGrid API key

set -euo pipefail

export REGION="${AWS_REGION:-us-east-1}"
export SERVICE_NAME="${SERVICE_NAME:-nerava-backend}"
export SENDGRID_API_KEY="${SENDGRID_API_KEY:-}"
export EMAIL_PROVIDER="${EMAIL_PROVIDER:-sendgrid}"
export EMAIL_FROM="${EMAIL_FROM:-noreply@nerava.network}"

if [ -z "$SENDGRID_API_KEY" ]; then
    echo "❌ ERROR: SENDGRID_API_KEY is required"
    echo "Usage: SENDGRID_API_KEY='SG.xxx' ./scripts/update_sendgrid.sh"
    exit 1
fi

echo "=== Updating App Runner Service with SendGrid Configuration ==="
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Email Provider: $EMAIL_PROVIDER"
echo "Email From: $EMAIL_FROM"
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

# Create update configuration with SendGrid added
echo "Creating update configuration..."
cat > /tmp/apprunner-sendgrid-update.json <<EOF
{
  "ImageRepository": {
    "ImageIdentifier": "$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageIdentifier')",
    "ImageConfiguration": {
      "Port": "$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageConfiguration.Port // 8001')",
      "RuntimeEnvironmentVariables": $(echo "$CURRENT_ENV_VARS" | jq --arg key "$SENDGRID_API_KEY" --arg provider "$EMAIL_PROVIDER" --arg from "$EMAIL_FROM" '. + {SENDGRID_API_KEY: $key, EMAIL_PROVIDER: $provider, EMAIL_FROM: $from}')
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
    --source-configuration file:///tmp/apprunner-sendgrid-update.json \
    --output json > /tmp/apprunner-update-response.json

echo "✅ Service update initiated"
echo ""
echo "The service will restart with the new SendGrid configuration."
echo "Check status with:"
echo "  aws apprunner describe-service --service-arn $SERVICE_ARN --region $REGION"
