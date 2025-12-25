#!/bin/bash
# Complete AWS Deployment Script
# Run this after granting necessary IAM permissions and verifying AWS account for CloudFront

set -e

echo "=== Completing AWS Deployment ==="
echo ""

# Load environment variables
# Update these if service was recreated
export APP_RUNNER_SERVICE_ARN="${APP_RUNNER_SERVICE_ARN:-arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/6c9c71e0ed4b40f1826e9b69dc55763d}"
export APP_RUNNER_URL="${APP_RUNNER_URL:-https://nbfmpiie6x.us-east-1.awsapprunner.com}"
export S3_BUCKET="nerava-frontend-1766451028"
export REGION="us-east-1"

# Load secrets
if [ -f /tmp/secrets.sh ]; then
    source /tmp/secrets.sh
    echo "✅ Secrets loaded"
else
    echo "❌ ERROR: /tmp/secrets.sh not found. Run Phase 2 first."
    exit 1
fi

# Phase 3: RDS Postgres
echo ""
echo "=== Phase 3: Creating RDS Postgres ==="
if [ -f /tmp/db-password.txt ]; then
    export DB_PASSWORD=$(cat /tmp/db-password.txt)
    ./scripts/setup-rds-with-permissions.sh
    
    echo "Waiting for RDS to be available..."
    aws rds wait db-instance-available --db-instance-identifier nerava-db --region "$REGION"
    
    RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier nerava-db --region "$REGION" --query 'DBInstances[0].Endpoint.Address' --output text)
    echo "✅ RDS Endpoint: $RDS_ENDPOINT"
    
    # Construct DATABASE_URL
    DB_USERNAME="nerava_admin"
    DB_NAME="nerava"
    export DATABASE_URL="postgresql+psycopg2://$DB_USERNAME:$DB_PASSWORD@$RDS_ENDPOINT:5432/$DB_NAME"
    echo "DATABASE_URL constructed"
else
    echo "❌ ERROR: /tmp/db-password.txt not found"
    exit 1
fi

# Phase 4: ElastiCache Redis
echo ""
echo "=== Phase 4: Creating ElastiCache Redis ==="
./scripts/setup-redis-with-permissions.sh

# Phase 6: CloudFront
echo ""
echo "=== Phase 6: Creating CloudFront Distribution ==="
S3_BUCKET="$S3_BUCKET" ./scripts/create-cloudfront.sh

echo "Waiting for CloudFront to deploy..."
sleep 60

CLOUDFRONT_DOMAIN=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='Nerava Frontend'].DomainName" --output text)
echo "✅ CloudFront Domain: $CLOUDFRONT_DOMAIN"

# Update frontend with App Runner URL
echo ""
echo "=== Updating Frontend API Base URL ==="
cd ui-mobile
# Add meta tag if not present
if ! grep -q "nerava-api-base" index.html; then
    sed -i.bak 's|<head>|<head>\n  <meta name="nerava-api-base" content="'$APP_RUNNER_URL'">|' index.html
    echo "✅ Added API base meta tag to index.html"
fi
cd ..

# Redeploy frontend
S3_BUCKET="$S3_BUCKET" ./scripts/deploy-frontend-s3.sh

# Invalidate CloudFront cache
DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='Nerava Frontend'].Id" --output text)
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" --region "$REGION"
echo "✅ CloudFront cache invalidated"

# Phase 2 & 7: Update App Runner with all env vars
echo ""
echo "=== Phase 2 & 7: Updating App Runner Environment Variables ==="
cat > /tmp/apprunner-final-config.json <<EOF
{
  "ImageRepository": {
    "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest",
    "ImageConfiguration": {
      "RuntimeEnvironmentVariables": {
        "ENV": "prod",
        "DATABASE_URL": "$DATABASE_URL",
        "JWT_SECRET": "$JWT_SECRET",
        "TOKEN_ENCRYPTION_KEY": "$TOKEN_ENCRYPTION_KEY",
        "REDIS_URL": "$REDIS_URL",
        "ALLOWED_ORIGINS": "https://$CLOUDFRONT_DOMAIN",
        "PUBLIC_BASE_URL": "$APP_RUNNER_URL",
        "FRONTEND_URL": "https://$CLOUDFRONT_DOMAIN",
        "PORT": "8000",
        "PYTHONPATH": "/app",
        "REGION": "us-east-1"
      },
      "Port": "8000"
    },
    "ImageRepositoryType": "ECR"
  },
  "AutoDeploymentsEnabled": true,
  "AuthenticationConfiguration": {
    "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
  }
}
EOF

aws apprunner update-service \
    --service-arn "$APP_RUNNER_SERVICE_ARN" \
    --region "$REGION" \
    --source-configuration file:///tmp/apprunner-final-config.json \
    --health-check-configuration '{"Protocol":"HTTP","Path":"/healthz","Interval":10,"Timeout":5,"HealthyThreshold":1,"UnhealthyThreshold":5}'

echo "✅ App Runner update initiated"
echo "Waiting for service to be running..."
aws apprunner wait service-running --service-arn "$APP_RUNNER_SERVICE_ARN" --region "$REGION"

# Phase 8: Smoke Tests
echo ""
echo "=== Phase 8: Running Smoke Tests ==="
echo "Testing /healthz endpoint..."
curl -i "$APP_RUNNER_URL/healthz" | head -5

echo ""
echo "Testing /openapi.json endpoint..."
curl -i "$APP_RUNNER_URL/openapi.json" | head -5

echo ""
echo "=== Deployment Complete ==="
echo "Backend URL: $APP_RUNNER_URL"
echo "Frontend URL: https://$CLOUDFRONT_DOMAIN"
echo "RDS Endpoint: $RDS_ENDPOINT"
echo "Redis Endpoint: $REDIS_ENDPOINT"

