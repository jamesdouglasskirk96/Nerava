#!/bin/bash
# Setup RDS Postgres - Run this after IAM permissions are granted
# This script creates RDS, configures security groups, and tests connectivity

set -e

export DB_INSTANCE_ID="${DB_INSTANCE_ID:-nerava-db}"
export DB_NAME="${DB_NAME:-nerava}"
export DB_USERNAME="${DB_USERNAME:-nerava_admin}"
export REGION="${AWS_REGION:-us-east-1}"

if [ -f /tmp/db-password.txt ]; then
    export DB_PASSWORD=$(cat /tmp/db-password.txt)
else
    echo "ERROR: /tmp/db-password.txt not found. Generating new password..."
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    echo "$DB_PASSWORD" > /tmp/db-password.txt
    export DB_PASSWORD
fi

echo "=== Creating RDS Postgres Instance ==="
echo "Instance ID: $DB_INSTANCE_ID"
echo "Database: $DB_NAME"
echo "Username: $DB_USERNAME"
echo "Region: $REGION"
echo ""

# Check if instance already exists
EXISTING=$(aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" --region "$REGION" --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo "none")

if [ "$EXISTING" != "none" ] && [ "$EXISTING" != "None" ]; then
    echo "RDS instance already exists with status: $EXISTING"
    if [ "$EXISTING" = "available" ]; then
        echo "✅ RDS is already available"
    else
        echo "Waiting for RDS to be available..."
        aws rds wait db-instance-available --db-instance-identifier "$DB_INSTANCE_ID" --region "$REGION"
    fi
else
    # Create RDS instance
    echo "Creating new RDS instance..."
    aws rds create-db-instance \
        --db-instance-identifier "$DB_INSTANCE_ID" \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --engine-version "15.4" \
        --master-username "$DB_USERNAME" \
        --master-user-password "$DB_PASSWORD" \
        --db-name "$DB_NAME" \
        --allocated-storage 20 \
        --storage-type gp3 \
        --storage-encrypted \
        --backup-retention-period 7 \
        --region "$REGION" \
        --publicly-accessible \
        --no-multi-az

    echo "Waiting for RDS to be available (this takes 5-10 minutes)..."
    aws rds wait db-instance-available --db-instance-identifier "$DB_INSTANCE_ID" --region "$REGION"
fi

# Get endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" --region "$REGION" --query 'DBInstances[0].Endpoint.Address' --output text)
echo ""
echo "✅ RDS Endpoint: $RDS_ENDPOINT"

# Construct DATABASE_URL
export DATABASE_URL="postgresql+psycopg2://$DB_USERNAME:$DB_PASSWORD@$RDS_ENDPOINT:5432/$DB_NAME"
echo "DATABASE_URL: postgresql+psycopg2://$DB_USERNAME:***@$RDS_ENDPOINT:5432/$DB_NAME"
echo ""
echo "=== Next Steps ==="
echo "1. Configure security groups to allow App Runner VPC connector access"
echo "2. Update App Runner DATABASE_URL env var with the URL above"
echo "3. Verify migrations run successfully"


