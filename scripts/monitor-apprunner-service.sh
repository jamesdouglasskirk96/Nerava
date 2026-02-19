#!/bin/bash
# Monitor App Runner service status and test endpoints
set -euo pipefail

SERVICE_ARN="${1:-arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend-v2/bc7e4d4c2f344e8c8af23cbc66ebc926}"
REGION="${REGION:-us-east-1}"

echo "Monitoring service: $SERVICE_ARN"
echo ""

# Get service URL
SERVICE_URL=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --query 'Service.ServiceUrl' --output text)
echo "Service URL: https://$SERVICE_URL"
echo ""

# Monitor status
echo "=== Status Check ==="
STATUS=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --query 'Service.Status' --output text)
echo "Status: $STATUS"
echo ""

if [ "$STATUS" = "RUNNING" ]; then
    echo "✅ Service is RUNNING!"
    echo ""
    
    # Test health endpoint
    echo "=== Testing Health Endpoint ==="
    HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "https://$SERVICE_URL/healthz")
    HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
    BODY=$(echo "$HEALTH_RESPONSE" | grep -v "HTTP_CODE")
    
    echo "HTTP Code: $HTTP_CODE"
    echo "Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    
    # Test discovery endpoint
    echo "=== Testing Discovery Endpoint ==="
    DISCOVERY_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "https://$SERVICE_URL/v1/chargers/discovery?lat=30.27&lng=-97.74")
    HTTP_CODE=$(echo "$DISCOVERY_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
    BODY=$(echo "$DISCOVERY_RESPONSE" | grep -v "HTTP_CODE")
    
    echo "HTTP Code: $HTTP_CODE"
    echo "Response (first 500 chars):"
    echo "$BODY" | head -c 500
    echo ""
    if [ "$HTTP_CODE" = "200" ]; then
        echo ""
        echo "Full response:"
        echo "$BODY" | python3 -m json.tool 2>/dev/null | head -50 || echo "$BODY" | head -50
    fi
    echo ""
    
    # Check logs
    echo "=== Recent Application Logs ==="
    SERVICE_ID=$(echo "$SERVICE_ARN" | awk -F'/' '{print $NF}')
    LOG_GROUP="/aws/apprunner/nerava-backend-v2/$SERVICE_ID/service"
    
    # Find instance log streams (not events or deployment)
    INSTANCE_STREAMS=$(aws logs describe-log-streams --log-group-name "$LOG_GROUP" --region "$REGION" --order-by LastEventTime --descending --max-items 10 --output json 2>/dev/null | jq -r '.logStreams[] | select(.logStreamName | startswith("instance") or startswith("application")) | .logStreamName' | head -1)
    
    if [ -n "$INSTANCE_STREAMS" ]; then
        for stream in $INSTANCE_STREAMS; do
            echo "Stream: $stream"
            aws logs get-log-events --log-group-name "$LOG_GROUP" --log-stream-name "$stream" --region "$REGION" --limit 20 --output json 2>/dev/null | jq -r '.events[]?.message' | tail -10
            echo ""
        done
    else
        echo "No instance log streams found yet"
    fi
    
elif [ "$STATUS" = "CREATE_FAILED" ]; then
    echo "❌ Service creation failed"
    echo "Check logs for details:"
    echo "  aws logs tail /aws/apprunner/nerava-backend-v2/*/service --follow --region $REGION"
else
    echo "⏳ Service is still provisioning (Status: $STATUS)"
    echo ""
    echo "Recent deployment logs:"
    SERVICE_ID=$(echo "$SERVICE_ARN" | awk -F'/' '{print $NF}')
    LOG_GROUP="/aws/apprunner/nerava-backend-v2/$SERVICE_ID/service"
    aws logs get-log-events --log-group-name "$LOG_GROUP" --log-stream-name "events" --region "$REGION" --limit 10 --output json 2>/dev/null | jq -r '.events[]?.message' | tail -5
fi





