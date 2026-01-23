#!/bin/bash
# Deploy OTP Fix to AWS App Runner
# This script builds, tags, pushes to ECR, and updates App Runner

set -e  # Exit on error

REGISTRY="566287346479.dkr.ecr.us-east-1.amazonaws.com"
IMAGE_NAME="nerava-backend"
VERSION="v12-otp-fix"
REGION="us-east-1"
SERVICE_ARN="arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3"

FULL_IMAGE_URI="${REGISTRY}/${IMAGE_NAME}:${VERSION}"

echo "🚀 Deploying OTP Fix (${VERSION})..."
echo ""

echo "Step 1: Authenticating Docker client to ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${REGISTRY}

echo ""
echo "Step 2: Building Docker image (platform: linux/amd64)..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:${VERSION} .

echo ""
echo "Step 3: Tagging image for ECR..."
docker tag ${IMAGE_NAME}:${VERSION} ${FULL_IMAGE_URI}

echo ""
echo "Step 4: Pushing image to ECR..."
docker push ${FULL_IMAGE_URI}

echo ""
echo "Step 5: Creating App Runner update configuration..."
cat > /tmp/apprunner-update.json << 'EOF'
{
  "ImageRepository": {
    "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v12-otp-fix",
    "ImageRepositoryType": "ECR",
    "ImageConfiguration": {
      "Port": "8000",
      "RuntimeEnvironmentVariables": {
        "DATABASE_URL": "postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava",
        "JWT_SECRET": "787044b63251814c8dd160437b395a77fa6e162bdc53e24320cd84d14fa5ed86",
        "ENV": "prod",
        "REGION": "us-east-1",
        "SKIP_HTTPS_REDIRECT": "true",
        "SKIP_STARTUP_VALIDATION": "true",
        "APP_STARTUP_MODE": "light",
        "REDIS_URL": "redis://nerava-redis.yagp9v.ng.0001.use1.cache.amazonaws.com:6379/0",
        "ALLOWED_ORIGINS": "https://nerava.network,https://www.nerava.network,https://app.nerava.network,http://app.nerava.network",
        "TOKEN_ENCRYPTION_KEY": "s1V8FQAFl7IzLcNJuBXBjDLpCb3j_IrbDbLWVzufBm4=",
        "OTP_PROVIDER": "twilio_verify",
        "TWILIO_ACCOUNT_SID": "YOUR_TWILIO_ACCOUNT_SID_HERE",
        "TWILIO_AUTH_TOKEN": "7566751c593a16c1f011a9c82dee6d91",
        "TWILIO_VERIFY_SERVICE_SID": "VAd22350253af88b2c0868d0a77b8b0265"
      }
    }
  },
  "AutoDeploymentsEnabled": false
}
EOF

echo ""
echo "Step 6: Updating App Runner service..."
aws apprunner update-service \
  --service-arn "${SERVICE_ARN}" \
  --source-configuration "$(cat /tmp/apprunner-update.json)"

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "Step 7: Waiting for deployment (120 seconds)..."
sleep 120

echo ""
echo "Step 8: Testing OTP endpoint..."
curl -s -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' | jq .

echo ""
echo "Step 9: Checking logs for OTP activity..."
aws logs tail "/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application" --since 5m | grep -i "otp\|twilio" || echo "No OTP logs found yet (may need to wait a bit longer)"

echo ""
echo "✅ Deployment script complete!"
echo ""
echo "Next steps:"
echo "1. Verify SMS was received on +17133056318"
echo "2. Check App Runner service status: aws apprunner describe-service --service-arn ${SERVICE_ARN}"
echo "3. Monitor logs: aws logs tail \"/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application\" --follow"


