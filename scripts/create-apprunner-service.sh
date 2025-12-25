#!/bin/bash
# Create a new App Runner service with health check fixes
set -euo pipefail

export REGION="us-east-1"
export ECR_REPO="566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest"
export SERVICE_NAME="nerava-backend-fixed-$(date +%s)"

echo "=== Creating New App Runner Service ==="
echo "Service Name: $SERVICE_NAME"
echo ""

# Load or generate secrets
if [ -f /tmp/secrets.sh ]; then
    source /tmp/secrets.sh
    echo "✅ Loaded secrets from /tmp/secrets.sh"
else
    echo "⚠️  No secrets file found. Generating new secrets..."
    export JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    export TOKEN_ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
    echo "JWT_SECRET=$JWT_SECRET" > /tmp/secrets.sh
    echo "TOKEN_ENCRRYPTION_KEY=$TOKEN_ENCRYPTION_KEY" >> /tmp/secrets.sh
    echo "✅ Generated and saved secrets to /tmp/secrets.sh"
fi

# Use dev config if DATABASE_URL not set
if [ -z "${DATABASE_URL:-}" ]; then
    export ENV="dev"
    export DATABASE_URL="sqlite:///./nerava.db"
    echo "⚠️  Using dev configuration (SQLite)"
else
    export ENV="prod"
    echo "✅ Using production DATABASE_URL"
fi

# Set Redis URL if not provided
if [ -z "${REDIS_URL:-}" ]; then
    export REDIS_URL="redis://localhost:6379/0"
    echo "⚠️  REDIS_URL not set, using default"
fi

# Create App Runner service configuration
cat > /tmp/apprunner-create-config.json <<EOF
{
  "ServiceName": "$SERVICE_NAME",
  "SourceConfiguration": {
    "ImageRepository": {
      "ImageIdentifier": "$ECR_REPO",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "ENV": "$ENV",
          "PORT": "8000",
          "PYTHONPATH": "/app",
          "REGION": "$REGION",
          "JWT_SECRET": "$JWT_SECRET",
          "TOKEN_ENCRYPTION_KEY": "$TOKEN_ENCRYPTION_KEY",
          "DATABASE_URL": "$DATABASE_URL",
          "REDIS_URL": "$REDIS_URL",
          "ALLOWED_ORIGINS": "*",
          "APP_STARTUP_MODE": "light"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::566287346479:role/service-role/AppRunnerECRAccessRole"
    },
    "AutoDeploymentsEnabled": false
  },
  "HealthCheckConfiguration": {
    "Protocol": "HTTP",
    "Path": "/healthz",
    "Interval": 10,
    "Timeout": 10,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  },
  "InstanceConfiguration": {
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }
}
EOF

echo "✅ Configuration file created"

# Create the service
echo ""
echo "=== Creating App Runner Service ==="
aws apprunner create-service \
    --region "$REGION" \
    --cli-input-json file:///tmp/apprunner-create-config.json \
    --output json > /tmp/apprunner-create-response.json

SERVICE_ARN=$(jq -r '.Service.ServiceArn' /tmp/apprunner-create-response.json)
SERVICE_URL=$(jq -r '.Service.ServiceUrl' /tmp/apprunner-create-response.json)

echo "✅ Service created successfully"
echo ""
echo "Service ARN: $SERVICE_ARN"
echo "Service URL: https://$SERVICE_URL"
echo ""
echo "Service is being created. This may take 5-10 minutes."
echo "Monitor status with:"
echo "  aws apprunner describe-service --service-arn \"$SERVICE_ARN\" --region $REGION"
echo ""
echo "Check logs with:"
echo "  aws logs tail /aws/apprunner/$SERVICE_NAME/service --follow --region $REGION"
echo ""
echo "Test health check once running:"
echo "  curl https://$SERVICE_URL/healthz"
