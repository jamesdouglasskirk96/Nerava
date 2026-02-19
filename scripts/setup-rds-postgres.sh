#!/bin/bash
# Setup RDS Postgres for Nerava Backend
# This script creates an RDS Postgres instance and configures it for App Runner

set -e

# Configuration (adjust as needed)
DB_INSTANCE_ID="${DB_INSTANCE_ID:-nerava-db}"
DB_NAME="${DB_NAME:-nerava}"
DB_USERNAME="${DB_USERNAME:-nerava_admin}"
DB_PASSWORD="${DB_PASSWORD:-}"  # Must be set
DB_INSTANCE_CLASS="${DB_INSTANCE_CLASS:-db.t3.micro}"
REGION="${AWS_REGION:-us-east-1}"
VPC_ID="${VPC_ID:-}"  # Optional: specify VPC ID

if [ -z "$DB_PASSWORD" ]; then
    echo "ERROR: DB_PASSWORD must be set"
    echo "Usage: DB_PASSWORD='your-password' ./scripts/setup-rds-postgres.sh"
    exit 1
fi

echo "=== Creating RDS Postgres Instance ==="
echo "Instance ID: $DB_INSTANCE_ID"
echo "Database: $DB_NAME"
echo "Username: $DB_USERNAME"
echo "Instance Class: $DB_INSTANCE_CLASS"
echo "Region: $REGION"
echo ""

# Generate a secure password if not provided
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    echo "Generated password: $DB_PASSWORD"
    echo "SAVE THIS PASSWORD - it won't be shown again!"
    echo ""
fi

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier "$DB_INSTANCE_ID" \
    --db-instance-class "$DB_INSTANCE_CLASS" \
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
    ${VPC_ID:+--db-subnet-group-name "$VPC_ID"} \
    --publicly-accessible \
    --no-multi-az

echo ""
echo "=== RDS Instance Creation Initiated ==="
echo "Instance ID: $DB_INSTANCE_ID"
echo "This will take 5-10 minutes to complete."
echo ""
echo "To check status:"
echo "  aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --region $REGION"
echo ""
echo "Once ready, get the endpoint:"
echo "  aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_ID --region $REGION --query 'DBInstances[0].Endpoint.Address' --output text"
echo ""
echo "DATABASE_URL format:"
echo "  postgresql+psycopg2://$DB_USERNAME:$DB_PASSWORD@<endpoint>:5432/$DB_NAME"
echo ""
echo "IMPORTANT: Update App Runner security group to allow inbound from App Runner VPC connector"






