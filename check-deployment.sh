#!/bin/bash
# Script to check AWS App Runner deployment status

# Replace with your App Runner service name
SERVICE_NAME="nerava-backend"

echo "Checking AWS App Runner deployment status..."
echo ""

# Get the latest deployment
LATEST_DEPLOYMENT=$(aws apprunner list-services \
  --region us-east-1 \
  --query "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceId" \
  --output text)

if [ -z "$LATEST_DEPLOYMENT" ]; then
  echo "❌ Service '$SERVICE_NAME' not found"
  exit 1
fi

echo "Service ID: $LATEST_DEPLOYMENT"
echo ""

# Get service details
SERVICE_URL=$(aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:$(aws sts get-caller-identity --query Account --output text):service/$LATEST_DEPLOYMENT" \
  --region us-east-1 \
  --query "Service.ServiceUrl" \
  --output text)

echo "Service URL: $SERVICE_URL"
echo ""

# Get deployment status
DEPLOYMENT_STATUS=$(aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:$(aws sts get-caller-identity --query Account --output text):service/$LATEST_DEPLOYMENT" \
  --region us-east-1 \
  --max-results 1 \
  --query "OperationSummaryList[0].Status" \
  --output text)

echo "Latest Deployment Status: $DEPLOYMENT_STATUS"
echo ""

# Test health endpoint
echo "Testing health endpoint..."
if curl -f -s "$SERVICE_URL/healthz" > /dev/null; then
  echo "✅ Health check PASSED"
  curl -s "$SERVICE_URL/healthz" | jq .
else
  echo "❌ Health check FAILED"
  echo "Response:"
  curl -i "$SERVICE_URL/healthz" || echo "Connection failed"
fi


