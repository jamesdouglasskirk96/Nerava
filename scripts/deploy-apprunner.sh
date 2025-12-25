#!/bin/bash
# Deploy App Runner service with proper configuration
# This script updates the App Runner service with the fixed Docker image

set -euo pipefail

export APP_RUNNER_SERVICE_ARN="${APP_RUNNER_SERVICE_ARN:-arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/f80156a7f0e4462c9659de357283f193}"
export REGION="us-east-1"
export ECR_REPO="566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest"
export SERVICE_URL="${SERVICE_URL:-https://bhu9u49jcj.us-east-1.awsapprunner.com}"

echo "=== App Runner Deployment Script ==="
echo "Service ARN: $APP_RUNNER_SERVICE_ARN"
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
    echo "TOKEN_ENCRYPTION_KEY=$TOKEN_ENCRYPTION_KEY" >> /tmp/secrets.sh
    echo "✅ Generated and saved secrets to /tmp/secrets.sh"
fi

# Check if DATABASE_URL is set (required for production)
if [ -z "${DATABASE_URL:-}" ]; then
    echo ""
    echo "⚠️  WARNING: DATABASE_URL is not set!"
    echo "For production (ENV=prod), you need a PostgreSQL database."
    echo ""
    echo "Options:"
    echo "1. Set up RDS PostgreSQL (requires IAM permissions):"
    echo "   DB_PASSWORD='...' ./scripts/setup-rds-postgres.sh"
    echo ""
    echo "2. Use a temporary dev configuration (NOT for production):"
    echo "   This will use SQLite and ENV=dev"
    echo ""
    # Non-interactive: use dev config if DATABASE_URL not set
    echo "Using dev configuration (non-interactive mode)"
    export ENV="dev"
    export DATABASE_URL="sqlite:///./nerava.db"
else
    export ENV="prod"
    echo "✅ Using DATABASE_URL for production"
fi

# Check if REDIS_URL is set
if [ -z "${REDIS_URL:-}" ]; then
    echo "⚠️  REDIS_URL not set. Rate limiting will use in-memory fallback."
    export REDIS_URL="redis://localhost:6379/0"
fi

# Build and push Docker image
echo ""
echo "=== Building and Pushing Docker Image ==="
cd nerava-backend-v9

echo "Logging in to ECR..."
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_REPO" || true

echo "Building image..."
docker build -t "$ECR_REPO" .

echo "Pushing image..."
docker push "$ECR_REPO"

echo "✅ Image pushed successfully"
cd ..

# Create App Runner configuration
echo ""
echo "=== Creating App Runner Configuration ==="
cat > /tmp/apprunner-config.json <<EOF
{
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
        "PUBLIC_BASE_URL": "$SERVICE_URL",
        "FRONTEND_URL": "$SERVICE_URL"
      }
    },
    "ImageRepositoryType": "ECR"
  },
  "AutoDeploymentsEnabled": false
}
EOF

echo "✅ Configuration file created"

# Update App Runner service
echo ""
echo "=== Updating App Runner Service ==="
aws apprunner update-service \
    --service-arn "$APP_RUNNER_SERVICE_ARN" \
    --region "$REGION" \
    --source-configuration file:///tmp/apprunner-config.json \
    --health-check-configuration '{"Protocol":"HTTP","Path":"/healthz","Interval":10,"Timeout":10,"HealthyThreshold":1,"UnhealthyThreshold":5}' \
    --output json > /tmp/apprunner-update-response.json

echo "✅ Service update initiated"
cat /tmp/apprunner-update-response.json | jq -r '{ServiceArn: .Service.ServiceArn, Status: .Service.Status, ServiceUrl: .Service.ServiceUrl}'

# Wait for service to be running
echo ""
echo "=== Waiting for Service to be Running ==="
echo "This may take 5-10 minutes..."
aws apprunner wait service-running --service-arn "$APP_RUNNER_SERVICE_ARN" --region "$REGION" || {
    echo ""
    echo "⚠️  Service did not reach RUNNING status"
    echo "Checking status..."
    aws apprunner describe-service --service-arn "$APP_RUNNER_SERVICE_ARN" --region "$REGION" --output json | jq -r '{Status: .Service.Status}'
    echo ""
    echo "Check CloudWatch logs for details:"
    echo "aws logs tail /aws/apprunner/nerava-backend/service --follow --region $REGION"
    exit 1
}

echo "✅ Service is RUNNING"

# Test health endpoint
echo ""
echo "=== Testing Health Endpoint ==="
sleep 5
if curl -f -s "$SERVICE_URL/healthz" > /dev/null; then
    echo "✅ Health check passed: $SERVICE_URL/healthz"
    curl -s "$SERVICE_URL/healthz" | jq .
else
    echo "⚠️  Health check failed. Service may still be starting."
    echo "Try again in a few minutes: curl $SERVICE_URL/healthz"
fi

echo ""
echo "=== Deployment Complete ==="
echo "Service URL: $SERVICE_URL"
echo "Health Check: $SERVICE_URL/healthz"
echo ""
echo "Next Steps:"
if [ "$ENV" = "dev" ]; then
    echo "1. Set up RDS PostgreSQL for production"
    echo "2. Update DATABASE_URL and set ENV=prod"
    echo "3. Run this script again"
fi
echo "1. Check CloudWatch logs: aws logs tail /aws/apprunner/nerava-backend/service --follow"
echo "2. Monitor service: aws apprunner describe-service --service-arn $APP_RUNNER_SERVICE_ARN"

