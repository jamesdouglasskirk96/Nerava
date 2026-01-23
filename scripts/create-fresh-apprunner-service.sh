#!/bin/bash
# Create a fresh App Runner service to replace stuck deployment
# This script creates a new service, monitors it, updates DNS, and optionally cleans up the old service
#
# Usage:
#   ./scripts/create-fresh-apprunner-service.sh
#
# Environment Variables (optional, defaults provided):
#   DATABASE_URL - PostgreSQL connection string
#   JWT_SECRET - JWT signing secret
#   TOKEN_ENCRYPTION_KEY - Fernet encryption key
#   REDIS_URL - Redis connection string
#   ALLOWED_ORIGINS - Comma-separated list of allowed CORS origins
#   SKIP_DNS_UPDATE - Set to "true" to skip DNS update (default: false)
#   SKIP_CLEANUP - Set to "false" to enable old service deletion (default: true)
#   MAX_WAIT_MINUTES - Maximum wait time for service to be RUNNING (default: 20)
#   OLD_SERVICE_ARN - ARN of old service to delete (if SKIP_CLEANUP=false)
#
# Examples:
#   # Basic usage with defaults
#   ./scripts/create-fresh-apprunner-service.sh
#
#   # Skip DNS update (manual DNS management)
#   SKIP_DNS_UPDATE=true ./scripts/create-fresh-apprunner-service.sh
#
#   # Enable automatic cleanup of old service
#   SKIP_CLEANUP=false ./scripts/create-fresh-apprunner-service.sh
#
#   # Custom wait time
#   MAX_WAIT_MINUTES=30 ./scripts/create-fresh-apprunner-service.sh
#
# Prerequisites:
#   - AWS CLI configured with appropriate permissions
#   - jq installed
#   - curl installed
#   - App Runner ECR access role exists
#   - VPC connector exists and is active
#
set -euo pipefail

# Configuration
export REGION="us-east-1"
export ECR_IMAGE="${ECR_IMAGE:-566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v8-discovery-fixed}"
export SERVICE_NAME="nerava-backend-v2"
export VPC_CONNECTOR_ARN="arn:aws:apprunner:us-east-1:566287346479:vpcconnector/nerava-vpc-connector/1/b07c0001ddf341b8b426d7fa83d93ad8"
export ROUTE53_ZONE_ID="${ROUTE53_ZONE_ID:-Z03087823KHR6VJQ9AGZL}"
export OLD_SERVICE_ARN="${OLD_SERVICE_ARN:-arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/1be481f942fe45aa9b5b7f1b0d429933}"

# Environment variables (from user prompt)
export ENV="${ENV:-prod}"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava}"
export JWT_SECRET="${JWT_SECRET:-787044b63251814c8dd160437b395a77fa6e162bdc53e24320cd84d14fa5ed86}"
export TOKEN_ENCRYPTION_KEY="${TOKEN_ENCRYPTION_KEY:-s1V8FQAFl7IzLcNJuBXBjDLpCb3j_IrbDbLWVzufBm4=}"
export REDIS_URL="${REDIS_URL:-redis://nerava-redis.yagp9v.ng.0001.use1.cache.amazonaws.com:6379/0}"
export ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://nerava.network,https://www.nerava.network,https://app.nerava.network,http://app.nerava.network.s3-website-us-east-1.amazonaws.com}"
export SKIP_HTTPS_REDIRECT="${SKIP_HTTPS_REDIRECT:-true}"
export OTP_PROVIDER="${OTP_PROVIDER:-twilio}"
export TWILIO_ACCOUNT_SID="${TWILIO_ACCOUNT_SID:-YOUR_TWILIO_ACCOUNT_SID_HERE}"
export REGION_ENV="${REGION_ENV:-us-east-1}"

# Options
SKIP_DNS_UPDATE="${SKIP_DNS_UPDATE:-false}"
SKIP_CLEANUP="${SKIP_CLEANUP:-true}"
MAX_WAIT_MINUTES="${MAX_WAIT_MINUTES:-20}"

echo "=========================================="
echo "Fresh App Runner Service Deployment"
echo "=========================================="
echo "Service Name: $SERVICE_NAME"
echo "Image: $ECR_IMAGE"
echo "Region: $REGION"
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ ERROR: AWS CLI not found"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ ERROR: jq not found"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "❌ ERROR: curl not found"
    exit 1
fi

# Verify required environment variables are set
if [ -z "$DATABASE_URL" ] || [ "$DATABASE_URL" = "postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava" ]; then
    echo "⚠️  Using default DATABASE_URL from prompt"
fi

# Step 1: Create service configuration
echo "=== Step 1: Creating Service Configuration ==="
cat > /tmp/apprunner-create-config.json <<EOF
{
  "ServiceName": "$SERVICE_NAME",
  "SourceConfiguration": {
    "ImageRepository": {
      "ImageIdentifier": "$ECR_IMAGE",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "ENV": "$ENV",
          "DATABASE_URL": "$DATABASE_URL",
          "JWT_SECRET": "$JWT_SECRET",
          "TOKEN_ENCRYPTION_KEY": "$TOKEN_ENCRYPTION_KEY",
          "REDIS_URL": "$REDIS_URL",
          "ALLOWED_ORIGINS": "$ALLOWED_ORIGINS",
          "SKIP_HTTPS_REDIRECT": "$SKIP_HTTPS_REDIRECT",
          "OTP_PROVIDER": "$OTP_PROVIDER",
          "TWILIO_ACCOUNT_SID": "$TWILIO_ACCOUNT_SID",
          "REGION": "$REGION_ENV"
        }
      }
    },
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
    },
    "AutoDeploymentsEnabled": false
  },
  "InstanceConfiguration": {
    "Cpu": "1024",
    "Memory": "4096"
  },
  "HealthCheckConfiguration": {
    "Protocol": "HTTP",
    "Path": "/healthz",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  },
  "NetworkConfiguration": {
    "EgressConfiguration": {
      "EgressType": "VPC",
      "VpcConnectorArn": "$VPC_CONNECTOR_ARN"
    },
    "IngressConfiguration": {
      "IsPubliclyAccessible": true
    }
  }
}
EOF

echo "✅ Configuration file created at /tmp/apprunner-create-config.json"
echo ""

# Step 2: Create the service
echo "=== Step 2: Creating App Runner Service ==="
CREATE_RESPONSE=$(aws apprunner create-service \
    --region "$REGION" \
    --cli-input-json file:///tmp/apprunner-create-config.json \
    --output json)

SERVICE_ARN=$(echo "$CREATE_RESPONSE" | jq -r '.Service.ServiceArn')
SERVICE_URL=$(echo "$CREATE_RESPONSE" | jq -r '.Service.ServiceUrl')
SERVICE_STATUS=$(echo "$CREATE_RESPONSE" | jq -r '.Service.Status')

echo "✅ Service creation initiated"
echo "Service ARN: $SERVICE_ARN"
echo "Service URL: $SERVICE_URL"
echo "Initial Status: $SERVICE_STATUS"
echo ""

# Step 3: Monitor service status
echo "=== Step 3: Monitoring Service Status ==="
echo "Waiting for service to reach RUNNING status (max ${MAX_WAIT_MINUTES} minutes)..."
echo ""

START_TIME=$(date +%s)
MAX_WAIT_SECONDS=$((MAX_WAIT_MINUTES * 60))
CHECK_INTERVAL=30

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED -gt $MAX_WAIT_SECONDS ]; then
        echo "❌ Timeout: Service did not reach RUNNING status within ${MAX_WAIT_MINUTES} minutes"
        echo "Current status:"
        aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --query 'Service.Status' --output text
        echo ""
        echo "Check logs: aws logs tail /aws/apprunner/$SERVICE_NAME/service --follow --region $REGION"
        exit 1
    fi
    
    STATUS=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --query 'Service.Status' --output text)
    echo "[$(date +%H:%M:%S)] Status: $STATUS (elapsed: ${ELAPSED}s)"
    
    if [ "$STATUS" = "RUNNING" ]; then
        echo "✅ Service is RUNNING!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ] || [ "$STATUS" = "DELETE_FAILED" ] || [ "$STATUS" = "UPDATE_FAILED" ]; then
        echo "❌ Service creation failed with status: $STATUS"
        echo "Check CloudWatch logs for details:"
        echo "  aws logs tail /aws/apprunner/$SERVICE_NAME/service --since 30m --region $REGION"
        exit 1
    fi
    
    sleep $CHECK_INTERVAL
done

echo ""

# Step 4: Verify health check
echo "=== Step 4: Verifying Health Check ==="
FULL_URL="https://$SERVICE_URL"
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Testing health endpoint: $FULL_URL/healthz (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
    
    if HTTP_CODE=$(curl -s -o /tmp/healthz-response.json -w "%{http_code}" "$FULL_URL/healthz"); then
        if [ "$HTTP_CODE" = "200" ]; then
            echo "✅ Health check passed!"
            echo "Response:"
            cat /tmp/healthz-response.json | jq . 2>/dev/null || cat /tmp/healthz-response.json
            echo ""
            break
        else
            echo "⚠️  Health check returned HTTP $HTTP_CODE"
            cat /tmp/healthz-response.json 2>/dev/null || echo ""
        fi
    else
        echo "⚠️  Health check request failed"
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo "Retrying in 10 seconds..."
        sleep 10
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Health check failed after $MAX_RETRIES attempts"
    echo "Service may still be starting. Check logs:"
    echo "  aws logs tail /aws/apprunner/$SERVICE_NAME/service --follow --region $REGION"
    exit 1
fi

# Step 5: Test discovery endpoint
echo "=== Step 5: Testing Discovery Endpoint ==="
DISCOVERY_URL="$FULL_URL/v1/chargers/discovery?lat=30.27&lng=-97.74"
echo "Testing: $DISCOVERY_URL"

if DISCOVERY_RESPONSE=$(curl -s -w "\n%{http_code}" "$DISCOVERY_URL"); then
    HTTP_CODE=$(echo "$DISCOVERY_RESPONSE" | tail -n1)
    BODY=$(echo "$DISCOVERY_RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Discovery endpoint working!"
        echo "Response preview (first 200 chars):"
        echo "$BODY" | head -c 200
        echo ""
    else
        echo "⚠️  Discovery endpoint returned HTTP $HTTP_CODE"
        echo "Response: $BODY"
    fi
else
    echo "⚠️  Discovery endpoint test failed (may be expected if endpoint requires auth)"
fi

echo ""

# Step 6: Check CloudWatch logs
echo "=== Step 6: Checking CloudWatch Logs ==="
echo "Fetching recent logs..."
LOG_GROUP="/aws/apprunner/$SERVICE_NAME/service"
if aws logs describe-log-streams --log-group-name "$LOG_GROUP" --region "$REGION" --order-by LastEventTime --descending --max-items 1 --output json 2>/dev/null | jq -r '.logStreams[0].logStreamName' > /tmp/log-stream.txt 2>/dev/null; then
    LOG_STREAM=$(cat /tmp/log-stream.txt)
    if [ -n "$LOG_STREAM" ] && [ "$LOG_STREAM" != "null" ]; then
        echo "✅ Found log stream: $LOG_STREAM"
        echo "Recent log entries:"
        aws logs get-log-events \
            --log-group-name "$LOG_GROUP" \
            --log-stream-name "$LOG_STREAM" \
            --region "$REGION" \
            --limit 20 \
            --output json 2>/dev/null | jq -r '.events[] | .message' | tail -10 || echo "Could not fetch logs"
    else
        echo "⚠️  No log streams found yet (logs may appear shortly)"
    fi
else
    echo "⚠️  Could not access log group (may not exist yet)"
fi

echo ""

# Step 7: Update Route53 DNS
if [ "$SKIP_DNS_UPDATE" = "false" ]; then
    echo "=== Step 7: Updating Route53 DNS ==="
    echo "Updating api.nerava.network CNAME to point to: $SERVICE_URL"
    
    cat > /tmp/route53-change.json <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.nerava.network",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{"Value": "$SERVICE_URL"}]
    }
  }]
}
EOF
    
    CHANGE_RESPONSE=$(aws route53 change-resource-record-sets \
        --hosted-zone-id "$ROUTE53_ZONE_ID" \
        --change-batch file:///tmp/route53-change.json \
        --region "$REGION" \
        --output json)
    
    CHANGE_ID=$(echo "$CHANGE_RESPONSE" | jq -r '.ChangeInfo.Id')
    echo "✅ DNS update initiated. Change ID: $CHANGE_ID"
    echo "DNS propagation may take a few minutes..."
    echo ""
else
    echo "=== Step 7: DNS Update (Skipped) ==="
    echo "To update DNS manually, run:"
    echo "  aws route53 change-resource-record-sets \\"
    echo "    --hosted-zone-id $ROUTE53_ZONE_ID \\"
    echo "    --change-batch '{\"Changes\":[{\"Action\":\"UPSERT\",\"ResourceRecordSet\":{\"Name\":\"api.nerava.network\",\"Type\":\"CNAME\",\"TTL\":300,\"ResourceRecords\":[{\"Value\":\"$SERVICE_URL\"}]}}]}'"
    echo ""
fi

# Step 8: Optional cleanup of old service
if [ "$SKIP_CLEANUP" = "false" ]; then
    echo "=== Step 8: Cleaning Up Old Service ==="
    echo "Deleting old service: $OLD_SERVICE_ARN"
    
    OLD_STATUS=$(aws apprunner describe-service --service-arn "$OLD_SERVICE_ARN" --region "$REGION" --query 'Service.Status' --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$OLD_STATUS" = "NOT_FOUND" ]; then
        echo "⚠️  Old service not found (may already be deleted)"
    else
        echo "Old service status: $OLD_STATUS"
        echo "Deleting..."
        
        aws apprunner delete-service \
            --service-arn "$OLD_SERVICE_ARN" \
            --region "$REGION" \
            --output json > /tmp/delete-response.json
        
        echo "✅ Deletion initiated"
        echo "Waiting for deletion to complete..."
        
        aws apprunner wait service-deleted \
            --service-arn "$OLD_SERVICE_ARN" \
            --region "$REGION" \
            --max-attempts 60 \
            --delay 30 || {
            echo "⚠️  Deletion may still be in progress"
        }
        
        echo "✅ Old service deleted"
    fi
    echo ""
else
    echo "=== Step 8: Cleanup (Skipped) ==="
    echo "To delete old service manually, run:"
    echo "  aws apprunner delete-service --service-arn \"$OLD_SERVICE_ARN\" --region $REGION"
    echo ""
fi

# Summary
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo "✅ Service Name: $SERVICE_NAME"
echo "✅ Service ARN: $SERVICE_ARN"
echo "✅ Service URL: https://$SERVICE_URL"
echo "✅ Health Check: $FULL_URL/healthz"
echo ""

if [ "$SKIP_DNS_UPDATE" = "false" ]; then
    echo "✅ DNS Updated: api.nerava.network -> $SERVICE_URL"
else
    echo "⚠️  DNS Update: Manual update required"
fi

echo ""
echo "Next Steps:"
echo "1. Monitor service: aws apprunner describe-service --service-arn \"$SERVICE_ARN\" --region $REGION"
echo "2. Check logs: aws logs tail /aws/apprunner/$SERVICE_NAME/service --follow --region $REGION"
echo "3. Test endpoints:"
echo "   - Health: curl $FULL_URL/healthz"
echo "   - Discovery: curl \"$FULL_URL/v1/chargers/discovery?lat=30.27&lng=-97.74\""
echo ""

if [ "$SKIP_CLEANUP" = "true" ]; then
    echo "⚠️  Old service still exists. Delete it after verifying new service works:"
    echo "   aws apprunner delete-service --service-arn \"$OLD_SERVICE_ARN\" --region $REGION"
    echo ""
fi

echo "✅ Deployment complete!"

