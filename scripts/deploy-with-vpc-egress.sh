#!/bin/bash
# Deploy App Runner with VPC egress (NAT Gateway already configured)

set -e

SERVICE_ARN="arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3"
VPC_CONNECTOR_ARN="arn:aws:apprunner:us-east-1:566287346479:vpcconnector/nerava-vpc-connector/1/b07c0001ddf341b8b426d7fa83d93ad8"
IMAGE="566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix-fixed"
MAX_WAIT=600  # 10 minutes max
CHECK_INTERVAL=30  # Check every 30 seconds

echo "=== Deploying App Runner with VPC Egress ==="
echo "NAT Gateway: nat-0d7b414381999725d (already configured)"
echo "Image: $IMAGE"
echo ""

# Wait for any in-progress operation to complete
echo "Checking for in-progress operations..."
elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
  STATUS=$(aws apprunner list-operations \
    --service-arn "$SERVICE_ARN" \
    --query 'OperationSummaryList[0].Status' \
    --output text 2>/dev/null)
  
  if [ "$STATUS" != "IN_PROGRESS" ]; then
    echo "✅ Current operation completed: $STATUS"
    break
  fi
  
  minutes=$((elapsed / 60))
  seconds=$((elapsed % 60))
  printf "\r[%02d:%02d] Waiting for operation to complete (status: %s)..." $minutes $seconds "$STATUS"
  sleep $CHECK_INTERVAL
  elapsed=$((elapsed + CHECK_INTERVAL))
done

if [ "$STATUS" = "IN_PROGRESS" ]; then
  echo ""
  echo "❌ Timeout: Operation took longer than $((MAX_WAIT / 60)) minutes"
  exit 1
fi

echo ""
echo "Deploying with VPC egress..."

# Get environment variables
echo "Loading environment variables..."
aws apprunner describe-service \
  --service-arn "$SERVICE_ARN" \
  --query 'Service.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables' \
  --output json > /tmp/env_vars.json

# Create service config
python3 << 'PYTHON_EOF'
import json

with open('/tmp/env_vars.json', 'r') as f:
    env_vars = json.load(f)

config = {
    "ImageRepository": {
        "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix-fixed",
        "ImageRepositoryType": "ECR",
        "ImageConfiguration": {
            "Port": "8000",
            "RuntimeEnvironmentVariables": env_vars
        }
    },
    "AutoDeploymentsEnabled": False,
    "AuthenticationConfiguration": {
        "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
    }
}

with open('/tmp/service_config_vpc.json', 'w') as f:
    json.dump(config, f, indent=2)

print("Service config created")
PYTHON_EOF

# Deploy
OPERATION_ID=$(aws apprunner update-service \
  --service-arn "$SERVICE_ARN" \
  --network-configuration "{\"EgressConfiguration\":{\"EgressType\":\"VPC\",\"VpcConnectorArn\":\"$VPC_CONNECTOR_ARN\"}}" \
  --source-configuration file:///tmp/service_config_vpc.json \
  --query 'OperationId' \
  --output text)

echo "✅ Deployment initiated!"
echo "Operation ID: $OPERATION_ID"
echo ""
echo "Monitoring deployment..."

# Monitor deployment
elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
  STATUS=$(aws apprunner list-operations \
    --service-arn "$SERVICE_ARN" \
    --query 'OperationSummaryList[0].Status' \
    --output text 2>/dev/null)
  
  if [ "$STATUS" = "SUCCEEDED" ]; then
    echo ""
    echo "✅✅✅ Deployment succeeded! ✅✅✅"
    echo ""
    
    # Wait a bit for service to be ready
    sleep 10
    
    # Verify configuration
    echo "Verifying configuration..."
    EGRESS=$(aws apprunner describe-service \
      --service-arn "$SERVICE_ARN" \
      --query 'Service.NetworkConfiguration.EgressConfiguration.EgressType' \
      --output text)
    IMAGE=$(aws apprunner describe-service \
      --service-arn "$SERVICE_ARN" \
      --query 'Service.SourceConfiguration.ImageRepository.ImageIdentifier' \
      --output text)
    
    echo "Egress: $EGRESS"
    echo "Image: $IMAGE"
    echo ""
    
    if [ "$EGRESS" != "VPC" ]; then
      echo "❌ Egress is not VPC (got: $EGRESS)"
      exit 1
    fi
    
    # Test health
    echo "Testing health endpoint..."
    HEALTH=$(curl -s https://api.nerava.network/health)
    echo "Health: $HEALTH"
    echo ""
    
    # Test OTP
    echo "Testing OTP endpoint..."
    echo "Sending OTP request to +17133056318..."
    
    RESPONSE=$(curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
      -H "Content-Type: application/json" \
      -d '{"phone": "+17133056318"}' \
      --max-time 45 \
      -s \
      -w "\nHTTP_STATUS:%{http_code}\nTIME:%{time_total}" 2>&1)
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    TIME=$(echo "$RESPONSE" | grep "TIME" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS" | grep -v "TIME")
    
    echo "Response: $BODY"
    echo "HTTP Status: $HTTP_STATUS"
    echo "Time: ${TIME}s"
    echo ""
    
    if echo "$BODY" | grep -q "otp_sent"; then
      echo "✅✅✅ SUCCESS! OTP endpoint is working! ✅✅✅"
      echo ""
      echo "Check phone +17133056318 for SMS code"
      exit 0
    else
      echo "❌ OTP endpoint still not working"
      echo "Response: $BODY"
      exit 1
    fi
    
  elif [ "$STATUS" = "ROLLBACK_SUCCEEDED" ] || [ "$STATUS" = "FAILED" ]; then
    echo ""
    echo "❌ Deployment failed or rolled back"
    echo "Status: $STATUS"
    echo ""
    echo "Check logs:"
    echo "  aws logs tail /aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application --since 30m"
    exit 1
    
  else
    minutes=$((elapsed / 60))
    seconds=$((elapsed % 60))
    printf "\r[%02d:%02d] Status: %-15s (waiting...)" $minutes $seconds "$STATUS"
    sleep $CHECK_INTERVAL
    elapsed=$((elapsed + CHECK_INTERVAL))
  fi
done

echo ""
echo "❌ Timeout: Deployment took longer than $((MAX_WAIT / 60)) minutes"
exit 1




