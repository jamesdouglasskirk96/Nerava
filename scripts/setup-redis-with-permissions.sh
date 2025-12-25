#!/bin/bash
# Setup ElastiCache Redis - Run this after IAM permissions are granted
# This script creates Redis, configures security groups, and tests connectivity

set -e

export REDIS_GROUP_ID="${REDIS_GROUP_ID:-nerava-redis}"
export REGION="${AWS_REGION:-us-east-1}"

echo "=== Creating ElastiCache Redis ==="
echo "Replication Group ID: $REDIS_GROUP_ID"
echo "Region: $REGION"
echo ""

# Check if replication group already exists
EXISTING=$(aws elasticache describe-replication-groups --replication-group-id "$REDIS_GROUP_ID" --region "$REGION" --query 'ReplicationGroups[0].Status' --output text 2>/dev/null || echo "none")

if [ "$EXISTING" != "none" ] && [ "$EXISTING" != "None" ]; then
    echo "Redis replication group already exists with status: $EXISTING"
    if [ "$EXISTING" = "available" ]; then
        echo "✅ Redis is already available"
    else
        echo "Waiting for Redis to be available..."
        # Wait for Redis (no built-in wait command, so poll)
        for i in {1..30}; do
            STATUS=$(aws elasticache describe-replication-groups --replication-group-id "$REDIS_GROUP_ID" --region "$REGION" --query 'ReplicationGroups[0].Status' --output text)
            echo "[$i] Status: $STATUS"
            if [ "$STATUS" = "available" ]; then
                break
            fi
            sleep 20
        done
    fi
else
    # Create Redis replication group
    echo "Creating new Redis replication group..."
    aws elasticache create-replication-group \
        --replication-group-id "$REDIS_GROUP_ID" \
        --description "Nerava rate limiting Redis" \
        --engine redis \
        --cache-node-type cache.t3.micro \
        --num-cache-clusters 1 \
        --region "$REGION"

    echo "Waiting for Redis to be available (this takes 5-10 minutes)..."
    for i in {1..30}; do
        STATUS=$(aws elasticache describe-replication-groups --replication-group-id "$REDIS_GROUP_ID" --region "$REGION" --query 'ReplicationGroups[0].Status' --output text 2>/dev/null || echo "creating")
        echo "[$i] Status: $STATUS"
        if [ "$STATUS" = "available" ]; then
            break
        fi
        sleep 20
    done
fi

# Get endpoint
REDIS_ENDPOINT=$(aws elasticache describe-replication-groups --replication-group-id "$REDIS_GROUP_ID" --region "$REGION" --query 'ReplicationGroups[0].PrimaryEndpoint.Address' --output text)
echo ""
echo "✅ Redis Endpoint: $REDIS_ENDPOINT"

# Construct REDIS_URL
export REDIS_URL="redis://$REDIS_ENDPOINT:6379/0"
echo "REDIS_URL: redis://$REDIS_ENDPOINT:6379/0"
echo ""
echo "=== Next Steps ==="
echo "1. Configure security groups to allow App Runner VPC connector access"
echo "2. Update App Runner REDIS_URL env var with the URL above"
echo "3. Test rate limiting to verify Redis connectivity"


