#!/bin/bash
# Script to update App Runner service with Sentry DSN

set -euo pipefail

export REGION="${AWS_REGION:-us-east-1}"
export SERVICE_NAME="${SERVICE_NAME:-nerava-api}"
export SENTRY_DSN="${SENTRY_DSN:-https://1341c6825636c6edf9c2e40f8901c07f@o4510756278697984.ingest.us.sentry.io/4510756291739648}"
export SENTRY_ENVIRONMENT="${SENTRY_ENVIRONMENT:-prod}"

echo "=== Updating App Runner Service with Sentry DSN ==="
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Sentry Environment: $SENTRY_ENVIRONMENT"
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

# Create update configuration with Sentry DSN added
echo "Creating update configuration..."
cat > /tmp/apprunner-sentry-update.json <<EOF
{
  "ImageRepository": {
    "ImageIdentifier": "$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageIdentifier')",
    "ImageConfiguration": {
      "Port": "$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageConfiguration.Port // 8001')",
      "RuntimeEnvironmentVariables": $(echo "$CURRENT_ENV_VARS" | jq --arg dsn "$SENTRY_DSN" --arg env "$SENTRY_ENVIRONMENT" '. + {SENTRY_DSN: $dsn, SENTRY_ENVIRONMENT: $env, SENTRY_ENABLED: "true"}')
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
    --source-configuration file:///tmp/apprunner-sentry-update.json \
    --output json > /tmp/apprunner-update-response.json

echo "✅ Service update initiated"
echo ""
echo "The service will restart with the new Sentry configuration."
echo "Check status with:"
echo "  aws apprunner describe-service --service-arn $SERVICE_ARN --region $REGION"
