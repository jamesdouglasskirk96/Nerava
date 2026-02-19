#!/bin/bash
# Remove all existing App Runner services, build new image, and deploy
set -euo pipefail

export REGION="us-east-1"
export ECR_REPO="566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest"
export SERVICE_NAME="nerava-backend"

echo "=== Rebuild and Deploy App Runner Service ==="
echo ""

# Step 1: List and delete existing services
echo "=== Step 1: Removing Existing Services ==="
SERVICES=$(aws apprunner list-services --region "$REGION" --output json | jq -r '.ServiceSummaryList[] | select(.ServiceName | startswith("nerava-backend")) | .ServiceArn')

if [ -z "$SERVICES" ]; then
    echo "No existing services found"
else
    echo "Found services to delete:"
    echo "$SERVICES" | while read -r ARN; do
        SERVICE_NAME=$(echo "$ARN" | awk -F'/' '{print $2}')
        echo "  - $SERVICE_NAME ($ARN)"
    done
    
    echo ""
    echo "Deleting services..."
    echo "$SERVICES" | while read -r ARN; do
        SERVICE_NAME=$(echo "$ARN" | awk -F'/' '{print $2}')
        echo "Deleting $SERVICE_NAME..."
        aws apprunner delete-service --service-arn "$ARN" --region "$REGION" || {
            echo "⚠️  Failed to delete $SERVICE_NAME (may already be deleted or in progress)"
        }
    done
    
    echo ""
    echo "Waiting for services to be deleted (this may take a few minutes)..."
    echo "$SERVICES" | while read -r ARN; do
        SERVICE_NAME=$(echo "$ARN" | awk -F'/' '{print $2}')
        echo "Waiting for $SERVICE_NAME to be deleted..."
        aws apprunner wait service-deleted --service-arn "$ARN" --region "$REGION" || {
            echo "⚠️  Service $SERVICE_NAME may still be deleting (check manually)"
        }
    done
    echo "✅ Services deleted"
fi

# Step 2: Build and push Docker image
echo ""
echo "=== Step 2: Building and Pushing Docker Image ==="
cd nerava-backend-v9

echo "Logging in to ECR..."
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${ECR_REPO%%:*}" || {
    echo "⚠️  ECR login failed, trying to continue..."
}

echo "Building Docker image..."
docker build -t "$ECR_REPO" .

echo "Pushing image to ECR..."
docker push "$ECR_REPO"

echo "✅ Image built and pushed successfully"
cd ..

# Step 3: Load or generate secrets
echo ""
echo "=== Step 3: Loading/Generating Secrets ==="
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

# Step 4: Set environment variables
if [ -z "${DATABASE_URL:-}" ]; then
    echo ""
    echo "⚠️  WARNING: DATABASE_URL is not set!"
    echo "Using dev configuration (SQLite) - NOT for production"
    export ENV="dev"
    export DATABASE_URL="sqlite:///./nerava.db"
else
    export ENV="prod"
    echo "✅ Using DATABASE_URL for production"
fi

if [ -z "${REDIS_URL:-}" ]; then
    echo "⚠️  REDIS_URL not set. Rate limiting will use in-memory fallback."
    export REDIS_URL="redis://localhost:6379/0"
fi

# Step 5: Create new App Runner service
echo ""
echo "=== Step 4: Creating New App Runner Service ==="
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
          "APP_STARTUP_MODE": "light",
          "RUN_MIGRATIONS_ON_BOOT": "false"
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

# Step 6: Wait for service to be running
echo "=== Step 5: Waiting for Service to be Running ==="
echo "This may take 5-10 minutes..."
aws apprunner wait service-running --service-arn "$SERVICE_ARN" --region "$REGION" || {
    echo ""
    echo "⚠️  Service did not reach RUNNING status"
    echo "Checking status..."
    aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --output json | jq -r '{Status: .Service.Status, ServiceUrl: .Service.ServiceUrl}'
    echo ""
    echo "Check CloudWatch logs for details:"
    echo "aws logs tail /aws/apprunner/$SERVICE_NAME/service --follow --region $REGION"
    exit 1
}

echo "✅ Service is RUNNING"

# Step 7: Test health endpoint
echo ""
echo "=== Step 6: Testing Health Endpoint ==="
sleep 5
FULL_URL="https://$SERVICE_URL"
if curl -f -s "$FULL_URL/healthz" > /dev/null; then
    echo "✅ Health check passed: $FULL_URL/healthz"
    curl -s "$FULL_URL/healthz" | jq .
else
    echo "⚠️  Health check failed. Service may still be starting."
    echo "Try again in a few minutes: curl $FULL_URL/healthz"
fi

echo ""
echo "=== Deployment Complete ==="
echo "Service ARN: $SERVICE_ARN"
echo "Service URL: $FULL_URL"
echo "Health Check: $FULL_URL/healthz"
echo ""
echo "Next Steps:"
if [ "$ENV" = "dev" ]; then
    echo "1. Set up RDS PostgreSQL for production"
    echo "2. Update DATABASE_URL and set ENV=prod"
    echo "3. Update the service with new configuration"
fi
echo "1. Check CloudWatch logs: aws logs tail /aws/apprunner/$SERVICE_NAME/service --follow --region $REGION"
echo "2. Monitor service: aws apprunner describe-service --service-arn $SERVICE_ARN --region $REGION"





