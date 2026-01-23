#!/bin/bash
# Update App Runner service with debug image and SKIP_STARTUP_VALIDATION
set -euo pipefail

SERVICE_ARN="${1:-arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend-v2/bc7e4d4c2f344e8c8af23cbc66ebc926}"
REGION="us-east-1"

echo "=== Updating App Runner Service with Debug Image ==="
echo "Service ARN: $SERVICE_ARN"
echo ""

# Check service status
STATUS=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --query 'Service.Status' --output text)
echo "Current Status: $STATUS"

if [ "$STATUS" = "OPERATION_IN_PROGRESS" ]; then
    echo "❌ Service is still in progress - cannot update"
    echo "Wait for it to fail or complete, then run this script again"
    exit 1
fi

# Create update configuration
cat > /tmp/apprunner-debug-config.json <<'EOF'
{
  "ImageRepository": {
    "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:debug",
    "ImageRepositoryType": "ECR",
    "ImageConfiguration": {
      "Port": "8000",
      "RuntimeEnvironmentVariables": {
        "ENV": "prod",
        "SKIP_STARTUP_VALIDATION": "true",
        "OTP_PROVIDER": "twilio",
        "DATABASE_URL": "postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava",
        "JWT_SECRET": "787044b63251814c8dd160437b395a77fa6e162bdc53e24320cd84d14fa5ed86",
        "TOKEN_ENCRYPTION_KEY": "s1V8FQAFl7IzLcNJuBXBjDLpCb3j_IrbDbLWVzufBm4=",
        "REDIS_URL": "redis://nerava-redis.yagp9v.ng.0001.use1.cache.amazonaws.com:6379/0",
        "ALLOWED_ORIGINS": "https://nerava.network,https://www.nerava.network,https://app.nerava.network,http://app.nerava.network.s3-website-us-east-1.amazonaws.com",
        "SKIP_HTTPS_REDIRECT": "true",
        "TWILIO_ACCOUNT_SID": "YOUR_TWILIO_ACCOUNT_SID_HERE",
        "REGION": "us-east-1"
      }
    }
  },
  "AuthenticationConfiguration": {
    "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
  },
  "AutoDeploymentsEnabled": false
}
EOF

echo "✅ Configuration created"
echo ""

# Update service
echo "Updating service..."
UPDATE_RESPONSE=$(aws apprunner update-service \
    --service-arn "$SERVICE_ARN" \
    --region "$REGION" \
    --source-configuration file:///tmp/apprunner-debug-config.json \
    --output json)

NEW_STATUS=$(echo "$UPDATE_RESPONSE" | jq -r '.Service.Status')
SERVICE_URL=$(echo "$UPDATE_RESPONSE" | jq -r '.Service.ServiceUrl')

echo "✅ Service update initiated"
echo "New Status: $NEW_STATUS"
echo "Service URL: $SERVICE_URL"
echo ""
echo "Monitor with:"
echo "  aws apprunner describe-service --service-arn \"$SERVICE_ARN\" --region $REGION --query 'Service.Status' --output text"
echo ""
echo "Check logs:"
SERVICE_ID=$(echo "$SERVICE_ARN" | awk -F'/' '{print $NF}')
echo "  aws logs tail /aws/apprunner/nerava-backend-v2/$SERVICE_ID/service --follow --region $REGION"


