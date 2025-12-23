#!/bin/bash
# Update App Runner environment variables and redeploy
# Detects locked states, provides clear error messages, and validates health

set -e

APP_RUNNER_SERVICE_ARN="${APP_RUNNER_SERVICE_ARN:-}"
APP_RUNNER_URL="${APP_RUNNER_URL:-}"
REGION="${AWS_REGION:-us-east-1}"
POLL_INTERVAL="${POLL_INTERVAL:-30}"  # seconds
MAX_WAIT_TIME="${MAX_WAIT_TIME:-900}"  # 15 minutes

if [ -z "$APP_RUNNER_SERVICE_ARN" ]; then
    echo "ERROR: APP_RUNNER_SERVICE_ARN must be set"
    echo "Usage: APP_RUNNER_SERVICE_ARN='arn:...' [APP_RUNNER_URL='https://...'] ./scripts/update-app-runner-env.sh"
    exit 1
fi

echo "=== App Runner Environment Update Helper ==="
echo "Service ARN: $APP_RUNNER_SERVICE_ARN"
echo "Region: $REGION"
echo ""

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq is required but not installed. Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi

# Get current service configuration
echo "Fetching current service configuration..."
CURRENT_CONFIG=$(aws apprunner describe-service \
    --service-arn "$APP_RUNNER_SERVICE_ARN" \
    --region "$REGION" \
    --output json 2>&1)

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to fetch service configuration"
    echo "$CURRENT_CONFIG"
    exit 1
fi

# Check service status
SERVICE_STATUS=$(echo "$CURRENT_CONFIG" | jq -r '.Service.Status')
echo "Current service status: $SERVICE_STATUS"
echo ""

# Detect locked states
if [ "$SERVICE_STATUS" = "OPERATION_IN_PROGRESS" ]; then
    echo "⚠️  WARNING: Service is in OPERATION_IN_PROGRESS state (locked)"
    echo ""
    echo "The service is currently deploying or updating. You cannot modify configuration while in this state."
    echo ""
    echo "Options:"
    echo "1. Wait for the operation to complete (check status with):"
    echo "   aws apprunner describe-service --service-arn \"$APP_RUNNER_SERVICE_ARN\" --region \"$REGION\" --query 'Service.Status'"
    echo ""
    echo "2. If stuck for >30 minutes, delete and recreate the service:"
    echo "   See AWS_DEPLOYMENT_RUNBOOK.md section 'Recreate App Runner Service'"
    echo ""
    exit 1
fi

if [ "$SERVICE_STATUS" != "RUNNING" ] && [ "$SERVICE_STATUS" != "CREATE_FAILED" ] && [ "$SERVICE_STATUS" != "UPDATE_FAILED" ]; then
    echo "⚠️  WARNING: Service is in $SERVICE_STATUS state"
    echo "Proceeding may not work as expected."
    echo ""
fi

# Extract current source configuration
HAS_IMAGE_REPO=$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository // empty')
HAS_CODE_REPO=$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.CodeRepository // empty')

echo "=== Current Configuration ==="
if [ -n "$HAS_IMAGE_REPO" ]; then
    echo "Service type: Image Repository"
    IMAGE_IDENTIFIER=$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageIdentifier')
    CURRENT_PORT=$(echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageConfiguration.Port // "8000"')
    echo "Image: $IMAGE_IDENTIFIER"
    echo "Port: $CURRENT_PORT"
    echo ""
    echo "Current environment variables:"
    echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables // {}' | jq '.'
    echo ""
    echo "To update environment variables, create a service-config.json file with:"
    cat <<EOF
{
  "ImageRepository": {
    "ImageIdentifier": "$IMAGE_IDENTIFIER",
    "ImageConfiguration": {
      "Port": "$CURRENT_PORT",
      "RuntimeEnvironmentVariables": {
        "ENV": "prod",
        "DATABASE_URL": "postgresql+psycopg2://...",
        "JWT_SECRET": "...",
        "TOKEN_ENCRYPTION_KEY": "...",
        "ALLOWED_ORIGINS": "https://...",
        "PUBLIC_BASE_URL": "https://...",
        "FRONTEND_URL": "https://..."
      }
    }
  }
}
EOF
    echo ""
    echo "Then run:"
    echo "aws apprunner update-service \\"
    echo "  --service-arn \"$APP_RUNNER_SERVICE_ARN\" \\"
    echo "  --region \"$REGION\" \\"
    echo "  --source-configuration file://service-config.json"
elif [ -n "$HAS_CODE_REPO" ]; then
    echo "Service type: Source Code Repository"
    echo ""
    echo "Current environment variables:"
    echo "$CURRENT_CONFIG" | jq -r '.Service.SourceConfiguration.CodeRepository.CodeConfiguration.RuntimeEnvironmentVariables // {}' | jq '.'
    echo ""
    echo "To update environment variables:"
    echo "1. AWS Console: App Runner > Service > Configuration > Environment variables"
    echo "2. AWS CLI: aws apprunner update-service with source-configuration"
else
    echo "ERROR: Could not determine service source type"
    exit 1
fi

echo ""
echo "=== Health Check Configuration ==="
HEALTH_CHECK=$(echo "$CURRENT_CONFIG" | jq -r '.Service.HealthCheckConfiguration // {}')
echo "$HEALTH_CHECK" | jq '.'
HEALTH_PATH=$(echo "$HEALTH_CHECK" | jq -r '.Path // "/healthz"')
echo ""
echo "Health check path: $HEALTH_PATH"
echo ""

# If APP_RUNNER_URL is provided, test health endpoint
if [ -n "$APP_RUNNER_URL" ]; then
    echo "=== Testing Health Endpoint ==="
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_RUNNER_URL/healthz" || echo "000")
    if [ "$HEALTH_RESPONSE" = "200" ]; then
        echo "✅ Health check passed: $APP_RUNNER_URL/healthz returned 200"
        HEALTH_BODY=$(curl -s "$APP_RUNNER_URL/healthz")
        echo "Response: $HEALTH_BODY"
    else
        echo "⚠️  Health check failed: $APP_RUNNER_URL/healthz returned $HEALTH_RESPONSE"
        echo "This may indicate the service is not running correctly."
    fi
    echo ""
fi

echo "=== Next Steps ==="
echo ""
echo "1. Update your environment variables (see commands above)"
echo "2. Wait for deployment to complete (service will enter OPERATION_IN_PROGRESS)"
echo "3. Monitor deployment status:"
echo "   aws apprunner describe-service --service-arn \"$APP_RUNNER_SERVICE_ARN\" --region \"$REGION\" --query 'Service.Status'"
echo ""
echo "4. Once RUNNING, test health endpoint:"
if [ -n "$APP_RUNNER_URL" ]; then
    echo "   curl -i \"$APP_RUNNER_URL/healthz\""
else
    echo "   curl -i \"https://YOUR_APP_RUNNER_URL/healthz\""
fi
echo ""
echo "For detailed recreation steps, see AWS_DEPLOYMENT_RUNBOOK.md section 'Recreate App Runner Service'"

