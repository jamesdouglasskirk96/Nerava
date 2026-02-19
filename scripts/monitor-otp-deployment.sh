#!/bin/bash
# Monitor App Runner deployment and test OTP endpoint automatically

SERVICE_ARN="arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3"
MAX_WAIT_MINUTES=20
CHECK_INTERVAL=60  # Check every 60 seconds

echo "Monitoring App Runner deployment..."
echo "Service ARN: $SERVICE_ARN"
echo "Max wait: $MAX_WAIT_MINUTES minutes"
echo ""

elapsed=0
while [ $elapsed -lt $((MAX_WAIT_MINUTES * 60)) ]; do
  STATUS=$(aws apprunner list-operations \
    --service-arn "$SERVICE_ARN" \
    --query 'OperationSummaryList[0].Status' \
    --output text 2>/dev/null)
  
  if [ "$STATUS" = "SUCCEEDED" ]; then
    echo "✅ Deployment completed successfully!"
    echo ""
    
    # Verify egress configuration
    echo "Verifying egress configuration..."
    EGRESS=$(aws apprunner describe-service \
      --service-arn "$SERVICE_ARN" \
      --query 'Service.NetworkConfiguration.EgressConfiguration.EgressType' \
      --output text)
    
    if [ "$EGRESS" = "DEFAULT" ]; then
      echo "✅ Egress is DEFAULT"
    else
      echo "❌ Egress is $EGRESS (expected DEFAULT)"
    fi
    
    echo ""
    echo "Testing OTP endpoint..."
    
    # Test OTP endpoint
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
    
    if echo "$BODY" | grep -q "otp_sent"; then
      echo ""
      echo "✅✅✅ OTP ENDPOINT WORKING! ✅✅✅"
      echo "Check phone +17133056318 for SMS code"
      exit 0
    else
      echo ""
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
    echo "[$minutes min] Status: $STATUS (still in progress...)"
    sleep $CHECK_INTERVAL
    elapsed=$((elapsed + CHECK_INTERVAL))
  fi
done

echo "❌ Timeout: Deployment took longer than $MAX_WAIT_MINUTES minutes"
exit 1




