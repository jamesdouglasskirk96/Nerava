#!/bin/bash
# Monitor deployment after NAT Gateway setup

SERVICE_ARN="arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3"
MAX_WAIT=900  # 15 minutes
CHECK_INTERVAL=30

echo "=== Monitoring Deployment with NAT Gateway ==="
echo ""

elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
  STATUS=$(aws apprunner list-operations \
    --service-arn "$SERVICE_ARN" \
    --query 'OperationSummaryList[0].Status' \
    --output text 2>/dev/null)
  
  if [ "$STATUS" = "SUCCEEDED" ]; then
    echo "✅ Deployment succeeded!"
    echo ""
    
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
      echo "✅✅✅ SUCCESS! OTP endpoint is working with NAT Gateway! ✅✅✅"
      echo ""
      echo "Check phone +17133056318 for SMS code"
      exit 0
    else
      echo "❌ OTP endpoint still not working"
      echo "Response: $BODY"
      exit 1
    fi
    
  elif [ "$STATUS" = "ROLLBACK_SUCCEEDED" ] || [ "$STATUS" = "FAILED" ]; then
    echo "❌ Deployment failed or rolled back"
    echo "Status: $STATUS"
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

