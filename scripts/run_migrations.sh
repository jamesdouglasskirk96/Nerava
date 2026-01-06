#!/bin/bash
# Run Alembic migrations in ECS one-shot task

set -e

# Configuration
CLUSTER_NAME="${ECS_CLUSTER_NAME:-nerava-cluster}"
TASK_DEFINITION="${ECS_TASK_DEFINITION:-nerava-backend}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running database migrations...${NC}"

# Get subnet IDs and security group
echo "Fetching network configuration..."
SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=tag:Name,Values=nerava-private-subnet-*" \
  --query 'Subnets[*].SubnetId' \
  --output text \
  --region $AWS_REGION | tr '\t' ',')

SECURITY_GROUP=$(aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=nerava-ecs-tasks-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text \
  --region $AWS_REGION)

if [ -z "$SUBNET_IDS" ] || [ -z "$SECURITY_GROUP" ]; then
  echo -e "${RED}Error: Could not find network configuration${NC}"
  exit 1
fi

echo "Subnets: $SUBNET_IDS"
echo "Security Group: $SECURITY_GROUP"

# Run migration task
echo "Starting migration task..."
TASK_ARN=$(aws ecs run-task \
  --cluster $CLUSTER_NAME \
  --task-definition $TASK_DEFINITION \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP],assignPublicIp=DISABLED}" \
  --overrides '{
    "containerOverrides": [{
      "name": "backend",
      "command": ["python", "-m", "alembic", "upgrade", "head"]
    }]
  }' \
  --query 'tasks[0].taskArn' \
  --output text \
  --region $AWS_REGION)

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" == "None" ]; then
  echo -e "${RED}Error: Failed to start migration task${NC}"
  exit 1
fi

echo "Task ARN: $TASK_ARN"
echo "Waiting for migration to complete..."

# Wait for task to complete
aws ecs wait tasks-stopped \
  --cluster $CLUSTER_NAME \
  --tasks $TASK_ARN \
  --region $AWS_REGION

# Check exit code
EXIT_CODE=$(aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $TASK_ARN \
  --query 'tasks[0].containers[0].exitCode' \
  --output text \
  --region $AWS_REGION)

# Get logs
echo -e "\n${YELLOW}Migration logs:${NC}"
aws logs get-log-events \
  --log-group-name "/ecs/nerava-backend" \
  --log-stream-name "ecs/backend/$TASK_ARN" \
  --region $AWS_REGION \
  --query 'events[*].message' \
  --output text 2>/dev/null || echo "Could not retrieve logs"

if [ "$EXIT_CODE" == "0" ]; then
  echo -e "\n${GREEN}✓ Migrations completed successfully${NC}"
  exit 0
else
  echo -e "\n${RED}✗ Migration failed with exit code: $EXIT_CODE${NC}"
  exit 1
fi

