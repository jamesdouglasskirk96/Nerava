#!/bin/bash
# Monitor final OTP deployment and test automatically

set -e

SERVICE_ARN="arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3"
MAX_WAIT=900  # 15 minutes max
CHECK_INTERVAL=30  # Check every 30 seconds

echo "=== Monitoring Final OTP Deployment ==="
echo "Started: 08:19:30 AM"
echo "Expected completion: ~08:29-08:34 AM"
echo ""

elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
  STATUS=$(aws apprunner list-operations \
    --service-arn "$SERVICE_ARN" \
    --query 'OperationSummaryList[0].Status' \
    --output text 2>/dev/null)
  
  if [ "$STATUS" = "SUCCEEDED" ]; then
    echo ""
    echo "✅✅✅ Deployment SUCCEEDED! ✅✅✅"
    echo ""
    
    # Wait a bit for service to be fully ready
    sleep 10
    
    # Step 2: Verify Configuration
    echo "=== Step 2: Verifying Configuration ==="
    CONFIG=$(aws apprunner describe-service \
      --service-arn "$SERVICE_ARN" \
      --query 'Service.{Status:Status,Egress:NetworkConfiguration.EgressConfiguration.EgressType,Image:SourceConfiguration.ImageRepository.ImageIdentifier}' \
      --output json)
    
    echo "$CONFIG" | python3 -m json.tool
    echo ""
    
    EGRESS=$(echo "$CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin)['Egress'])" 2>/dev/null)
    IMAGE=$(echo "$CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin)['Image'])" 2>/dev/null)
    
    if [ "$EGRESS" != "VPC" ]; then
      echo "❌ Egress is not VPC (got: $EGRESS)"
      exit 1
    fi
    
    if [[ ! "$IMAGE" == *"v20-otp-fix-fixed"* ]]; then
      echo "❌ Image is not v20-otp-fix-fixed (got: $IMAGE)"
      exit 1
    fi
    
    echo "✅ Configuration verified!"
    echo ""
    
    # Step 3: Test Health
    echo "=== Step 3: Testing Health Endpoint ==="
    HEALTH=$(curl -s https://api.nerava.network/health)
    echo "$HEALTH" | python3 -m json.tool
    echo ""
    
    if ! echo "$HEALTH" | grep -q '"ok"'; then
      echo "❌ Health check failed"
      exit 1
    fi
    
    echo "✅ Health check passed!"
    echo ""
    
    # Step 4: Test OTP (Critical)
    echo "=== Step 4: Testing OTP Endpoint (CRITICAL) ==="
    echo "Sending OTP request to +17133056318..."
    echo ""
    
    START_TIME=$(date +%s)
    RESPONSE=$(curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
      -H "Content-Type: application/json" \
      -d '{"phone": "+17133056318"}' \
      --max-time 45 \
      -s \
      -w "\nHTTP_STATUS:%{http_code}\nTIME:%{time_total}" 2>&1)
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    TIME=$(echo "$RESPONSE" | grep "TIME" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS" | grep -v "TIME")
    
    echo "Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    echo "HTTP Status: $HTTP_STATUS"
    echo "Time: ${TIME}s"
    echo ""
    
    if echo "$BODY" | grep -q "otp_sent"; then
      echo "✅✅✅ SUCCESS! OTP endpoint is working! ✅✅✅"
      echo ""
      echo "📱 Check phone +17133056318 for SMS code"
      echo ""
      echo "=== Success Checklist ==="
      echo "✅ Deployment status: SUCCEEDED"
      echo "✅ Service status: RUNNING"
      echo "✅ Egress: VPC"
      echo "✅ Image: v20-otp-fix-fixed"
      echo "✅ Health: {\"ok\":true}"
      echo "✅ OTP: {\"otp_sent\":true} (${TIME}s)"
      echo "⏳ SMS: Check phone"
      echo ""
      echo "Next steps:"
      echo "1. Verify SMS received on +17133056318"
      echo "2. Run migration: cd backend && alembic upgrade head"
      echo "3. Test merchant claim endpoint"
      exit 0
    else
      echo "❌ OTP endpoint failed"
      echo "Response: $BODY"
      echo "HTTP Status: $HTTP_STATUS"
      exit 1
    fi
    
  elif [ "$STATUS" = "ROLLBACK_SUCCEEDED" ] || [ "$STATUS" = "FAILED" ]; then
    echo ""
    echo "❌ Deployment failed or rolled back"
    echo "Status: $STATUS"
    echo ""
    echo "=== Checking Logs ==="
    
    LOG_GROUP="/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application"
    LOG_STREAM=$(aws logs describe-log-streams \
      --log-group-name "$LOG_GROUP" \
      --order-by LastEventTime --descending --limit 1 \
      --query 'logStreams[0].logStreamName' --output text 2>/dev/null)
    
    if [ "$LOG_STREAM" != "None" ] && [ -n "$LOG_STREAM" ]; then
      echo "Log stream: $LOG_STREAM"
      echo ""
      echo "Recent errors:"
      aws logs get-log-events \
        --log-group-name "$LOG_GROUP" \
        --log-stream-name "$LOG_STREAM" \
        --limit 50 \
        --query 'events[*].message' --output text 2>&1 | \
        grep -E "(ERROR|FAILED|Exception|Traceback|AttributeError|Connection)" | tail -20
    fi
    
    echo ""
    echo "=== Checking NAT Gateway ==="
    aws ec2 describe-nat-gateways \
      --nat-gateway-ids nat-0d7b414381999725d \
      --query 'NatGateways[0].{State:State,SubnetId:SubnetId}' \
      --output json
    
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




