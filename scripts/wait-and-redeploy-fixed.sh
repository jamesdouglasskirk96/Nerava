#!/bin/bash
# Wait for stuck services to become deletable, then recreate with fixed image
set -euo pipefail

REGION="us-east-1"
FIXED_IMAGE="566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v8-discovery-fixed"

echo "=== Monitoring Stuck Services ==="
echo "Waiting for services to become deletable..."
echo ""

# Function to check and delete services
check_and_delete_services() {
    SERVICES=$(aws apprunner list-services --region "$REGION" --query 'ServiceSummaryList[?contains(ServiceName, `nerava`)].{ARN:ServiceArn,Name:ServiceName,Status:Status}' --output json)
    
    echo "$SERVICES" | jq -r '.[] | "\(.Name) - \(.Status)"'
    echo ""
    
    # Check each service
    echo "$SERVICES" | jq -r '.[] | "\(.ARN)|\(.Status)"' | while IFS='|' read -r ARN STATUS; do
        if [ "$STATUS" != "OPERATION_IN_PROGRESS" ] && [ "$STATUS" != "RUNNING" ]; then
            echo "Deleting service: $ARN (Status: $STATUS)"
            aws apprunner delete-service --service-arn "$ARN" --region "$REGION" --output json 2>&1 | head -3 || echo "Failed to delete (may already be deleted)"
        elif [ "$STATUS" = "RUNNING" ]; then
            echo "Service $ARN is RUNNING - checking if it's working..."
            SERVICE_URL=$(aws apprunner describe-service --service-arn "$ARN" --region "$REGION" --query 'Service.ServiceUrl' --output text)
            if curl -sf "https://$SERVICE_URL/healthz" > /dev/null 2>&1; then
                echo "✅ Service is working! URL: https://$SERVICE_URL"
            else
                echo "⚠️  Service is RUNNING but health check fails - will delete and recreate"
                aws apprunner delete-service --service-arn "$ARN" --region "$REGION" --output json 2>&1 | head -3 || true
            fi
        else
            echo "Service $ARN still in progress (Status: $STATUS)"
        fi
    done
}

# Monitor loop
MAX_WAIT=30  # 30 checks = 15 minutes
CHECK_COUNT=0

while [ $CHECK_COUNT -lt $MAX_WAIT ]; do
    CHECK_COUNT=$((CHECK_COUNT + 1))
    echo "[$(date +%H:%M:%S)] Check $CHECK_COUNT/$MAX_WAIT"
    
    check_and_delete_services
    
    # Count remaining services
    REMAINING=$(aws apprunner list-services --region "$REGION" --query 'ServiceSummaryList[?contains(ServiceName, `nerava`)].ServiceArn' --output json | jq 'length')
    
    if [ "$REMAINING" = "0" ]; then
        echo ""
        echo "✅ All services deleted. Ready to create new service with fixed image!"
        echo ""
        echo "Run deployment script:"
        echo "  ./scripts/create-fresh-apprunner-service.sh"
        echo ""
        echo "Or create manually with fixed image: $FIXED_IMAGE"
        exit 0
    fi
    
    echo "Remaining services: $REMAINING"
    echo "Waiting 30 seconds..."
    echo ""
    sleep 30
done

echo ""
echo "⚠️  Timeout reached. Some services may still be stuck."
echo "Check manually:"
echo "  aws apprunner list-services --region $REGION --query 'ServiceSummaryList[?contains(ServiceName, \`nerava\`)].{Name:ServiceName,Status:Status}' --output table"


