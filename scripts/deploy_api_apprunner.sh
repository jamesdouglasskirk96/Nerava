#!/bin/bash
# Deploy Nerava Backend to AWS App Runner
# This script builds the Docker image, pushes to ECR, and creates/updates the App Runner service
# with proper configuration for production deployment.

set -euo pipefail

# Configuration
export REGION="${AWS_REGION:-us-east-1}"
export AWS_ACCOUNT_ID="566287346479"
export ECR_REPO="${ECR_REPO:-nerava/backend}"
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
export ECR_IMAGE="${ECR_REGISTRY}/${ECR_REPO}:latest"
export SERVICE_NAME="${SERVICE_NAME:-nerava-api}"
export CUSTOM_DOMAIN="${CUSTOM_DOMAIN:-api.nerava.network}"
export ACM_CERT_ARN="${ACM_CERT_ARN:-arn:aws:acm:us-east-1:566287346479:certificate/9abd6168-db05-4455-b53b-0b3d397da70d}"
export ROUTE53_ZONE_ID="${ROUTE53_ZONE_ID:-Z03087823KHR6VJQ9AGZL}"

# API Base URL
export API_BASE_URL="https://${CUSTOM_DOMAIN}"
export PUBLIC_BASE_URL="${API_BASE_URL}"
export FRONTEND_URL="https://app.nerava.network"

echo "=========================================="
echo "Nerava Backend - App Runner Deployment"
echo "=========================================="
echo "Region: $REGION"
echo "ECR Image: $ECR_IMAGE"
echo "Service Name: $SERVICE_NAME"
echo "Custom Domain: $CUSTOM_DOMAIN"
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ ERROR: AWS CLI not found. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker not found. Please install it first."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ ERROR: jq not found. Please install it first."
    exit 1
fi

# Check for required environment variables
if [ -z "${DATABASE_URL:-}" ]; then
    echo "❌ ERROR: DATABASE_URL is required"
    echo "Example: DATABASE_URL=postgresql://user:password@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"
    exit 1
fi

# Load secrets from AWS Secrets Manager or environment
echo "=== Loading Secrets ==="
if [ -n "${JWT_SECRET_SECRET_NAME:-}" ]; then
    echo "Loading JWT_SECRET from Secrets Manager: $JWT_SECRET_SECRET_NAME"
    export JWT_SECRET=$(aws secretsmanager get-secret-value --secret-id "$JWT_SECRET_SECRET_NAME" --region "$REGION" --query SecretString --output text | jq -r '.JWT_SECRET // .')
else
    if [ -z "${JWT_SECRET:-}" ]; then
        echo "⚠️  WARNING: JWT_SECRET not set. Generating temporary secret..."
        export JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        echo "⚠️  IMPORTANT: Save this JWT_SECRET for production use!"
    fi
fi

if [ -n "${GOOGLE_PLACES_API_KEY_SECRET_NAME:-}" ]; then
    echo "Loading GOOGLE_PLACES_API_KEY from Secrets Manager: $GOOGLE_PLACES_API_KEY_SECRET_NAME"
    export GOOGLE_PLACES_API_KEY=$(aws secretsmanager get-secret-value --secret-id "$GOOGLE_PLACES_API_KEY_SECRET_NAME" --region "$REGION" --query SecretString --output text | jq -r '.GOOGLE_PLACES_API_KEY // .')
else
    if [ -z "${GOOGLE_PLACES_API_KEY:-}" ]; then
        echo "⚠️  WARNING: GOOGLE_PLACES_API_KEY not set"
    fi
fi

# Set production environment variables
export ENV="${ENV:-prod}"
export ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://app.nerava.network,https://merchant.nerava.network,https://admin.nerava.network,https://nerava.network,https://www.nerava.network}"

echo "✅ Secrets loaded"
echo ""

# Build Docker image
echo "=== Building Docker Image ==="
cd "$(dirname "$0")/../backend"

echo "Logging in to ECR..."
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY" || {
    echo "❌ ERROR: Failed to login to ECR"
    exit 1
}

echo "Building image: $ECR_IMAGE"
docker build -t "$ECR_REPO:latest" -f Dockerfile .

echo "Tagging image for ECR..."
docker tag "$ECR_REPO:latest" "$ECR_IMAGE"

echo "Pushing image to ECR..."
docker push "$ECR_IMAGE"

echo "✅ Image pushed successfully"
echo ""

# Check if service exists
echo "=== Checking App Runner Service ==="
SERVICE_ARN=$(aws apprunner list-services --region "$REGION" --query "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceArn" --output text) || SERVICE_ARN=""

if [ -z "$SERVICE_ARN" ]; then
    echo "Service '$SERVICE_NAME' not found. Creating new service..."
    
    # Create App Runner service configuration
    cat > /tmp/apprunner-create-config.json <<EOF
{
  "ServiceName": "$SERVICE_NAME",
  "SourceConfiguration": {
    "ImageRepository": {
      "ImageIdentifier": "$ECR_IMAGE",
      "ImageConfiguration": {
        "Port": "8001",
        "RuntimeEnvironmentVariables": {
          "ENV": "$ENV",
          "PORT": "8001",
          "PYTHONPATH": "/app",
          "PYTHONUNBUFFERED": "1",
          "REGION": "$REGION",
          "DATABASE_URL": "$DATABASE_URL",
          "JWT_SECRET": "$JWT_SECRET",
          "ALLOWED_ORIGINS": "$ALLOWED_ORIGINS",
          "PUBLIC_BASE_URL": "$PUBLIC_BASE_URL",
          "FRONTEND_URL": "$FRONTEND_URL",
          "API_BASE_URL": "$API_BASE_URL"
        }
      },
      "ImageRepositoryType": "ECR"
    },
    "AutoDeploymentsEnabled": false
  },
  "InstanceConfiguration": {
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  },
  "HealthCheckConfiguration": {
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }
}
EOF

    # Add optional environment variables
    if [ -n "${GOOGLE_PLACES_API_KEY:-}" ]; then
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.GOOGLE_PLACES_API_KEY = "'"$GOOGLE_PLACES_API_KEY"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
    fi

    if [ -n "${REDIS_URL:-}" ]; then
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.REDIS_URL = "'"$REDIS_URL"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
    fi

    if [ -n "${TOKEN_ENCRYPTION_KEY:-}" ]; then
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.TOKEN_ENCRYPTION_KEY = "'"$TOKEN_ENCRYPTION_KEY"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
    fi

    if [ -n "${SENTRY_DSN:-}" ]; then
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.SENTRY_DSN = "'"$SENTRY_DSN"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.SENTRY_ENVIRONMENT = "'"${SENTRY_ENVIRONMENT:-prod}"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.SENTRY_ENABLED = "true"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
    fi

    if [ -n "${SENDGRID_API_KEY:-}" ]; then
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.SENDGRID_API_KEY = "'"$SENDGRID_API_KEY"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.EMAIL_PROVIDER = "'"${EMAIL_PROVIDER:-sendgrid}"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.EMAIL_FROM = "'"${EMAIL_FROM:-noreply@nerava.network}"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
    fi

    if [ -n "${POSTHOG_API_KEY:-}" ]; then
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.POSTHOG_API_KEY = "'"$POSTHOG_API_KEY"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.POSTHOG_HOST = "'"${POSTHOG_HOST:-https://app.posthog.com}"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.ANALYTICS_ENABLED = "'"${ANALYTICS_ENABLED:-true}"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
    fi

    if [ -n "${HUBSPOT_PRIVATE_APP_TOKEN:-}" ]; then
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.HUBSPOT_PRIVATE_APP_TOKEN = "'"$HUBSPOT_PRIVATE_APP_TOKEN"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.HUBSPOT_PORTAL_ID = "'"${HUBSPOT_PORTAL_ID:-}"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.HUBSPOT_ENABLED = "'"${HUBSPOT_ENABLED:-true}"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
        jq '.SourceConfiguration.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.HUBSPOT_SEND_LIVE = "'"${HUBSPOT_SEND_LIVE:-true}"'"' /tmp/apprunner-create-config.json > /tmp/apprunner-create-config-tmp.json
        mv /tmp/apprunner-create-config-tmp.json /tmp/apprunner-create-config.json
    fi

    # Create service
    CREATE_RESPONSE=$(aws apprunner create-service \
        --region "$REGION" \
        --cli-input-json file:///tmp/apprunner-create-config.json \
        --output json)
    
    SERVICE_ARN=$(echo "$CREATE_RESPONSE" | jq -r '.Service.ServiceArn')
    SERVICE_URL=$(echo "$CREATE_RESPONSE" | jq -r '.Service.ServiceUrl')
    
    echo "✅ Service created: $SERVICE_NAME"
    echo "Service ARN: $SERVICE_ARN"
    echo "Service URL: $SERVICE_URL"
    
else
    echo "Service '$SERVICE_NAME' exists. Updating..."
    SERVICE_URL=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --query 'Service.ServiceUrl' --output text)
    
    # Create update configuration
    cat > /tmp/apprunner-update-config.json <<EOF
{
  "ImageRepository": {
    "ImageIdentifier": "$ECR_IMAGE",
    "ImageConfiguration": {
      "Port": "8001",
      "RuntimeEnvironmentVariables": {
        "ENV": "$ENV",
        "PORT": "8001",
        "PYTHONPATH": "/app",
        "PYTHONUNBUFFERED": "1",
        "REGION": "$REGION",
        "DATABASE_URL": "$DATABASE_URL",
        "JWT_SECRET": "$JWT_SECRET",
        "ALLOWED_ORIGINS": "$ALLOWED_ORIGINS",
        "PUBLIC_BASE_URL": "$PUBLIC_BASE_URL",
        "FRONTEND_URL": "$FRONTEND_URL",
        "API_BASE_URL": "$API_BASE_URL"
      }
    },
    "ImageRepositoryType": "ECR"
  },
  "AutoDeploymentsEnabled": false
}
EOF

    # Add optional environment variables
    if [ -n "${GOOGLE_PLACES_API_KEY:-}" ]; then
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.GOOGLE_PLACES_API_KEY = "'"$GOOGLE_PLACES_API_KEY"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
    fi

    if [ -n "${REDIS_URL:-}" ]; then
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.REDIS_URL = "'"$REDIS_URL"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
    fi

    if [ -n "${TOKEN_ENCRYPTION_KEY:-}" ]; then
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.TOKEN_ENCRYPTION_KEY = "'"$TOKEN_ENCRYPTION_KEY"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
    fi

    if [ -n "${SENTRY_DSN:-}" ]; then
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.SENTRY_DSN = "'"$SENTRY_DSN"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.SENTRY_ENVIRONMENT = "'"${SENTRY_ENVIRONMENT:-prod}"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.SENTRY_ENABLED = "true"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
    fi

    if [ -n "${SENDGRID_API_KEY:-}" ]; then
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.SENDGRID_API_KEY = "'"$SENDGRID_API_KEY"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.EMAIL_PROVIDER = "'"${EMAIL_PROVIDER:-sendgrid}"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.EMAIL_FROM = "'"${EMAIL_FROM:-noreply@nerava.network}"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
    fi

    if [ -n "${POSTHOG_API_KEY:-}" ]; then
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.POSTHOG_API_KEY = "'"$POSTHOG_API_KEY"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.POSTHOG_HOST = "'"${POSTHOG_HOST:-https://app.posthog.com}"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.ANALYTICS_ENABLED = "'"${ANALYTICS_ENABLED:-true}"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
    fi

    if [ -n "${HUBSPOT_PRIVATE_APP_TOKEN:-}" ]; then
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.HUBSPOT_PRIVATE_APP_TOKEN = "'"$HUBSPOT_PRIVATE_APP_TOKEN"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.HUBSPOT_PORTAL_ID = "'"${HUBSPOT_PORTAL_ID:-}"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.HUBSPOT_ENABLED = "'"${HUBSPOT_ENABLED:-true}"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
        jq '.ImageRepository.ImageConfiguration.RuntimeEnvironmentVariables.HUBSPOT_SEND_LIVE = "'"${HUBSPOT_SEND_LIVE:-true}"'"' /tmp/apprunner-update-config.json > /tmp/apprunner-update-config-tmp.json
        mv /tmp/apprunner-update-config-tmp.json /tmp/apprunner-update-config.json
    fi

    # Update service
    aws apprunner update-service \
        --service-arn "$SERVICE_ARN" \
        --region "$REGION" \
        --source-configuration file:///tmp/apprunner-update-config.json \
        --health-check-configuration '{"Protocol":"HTTP","Path":"/health","Interval":10,"Timeout":5,"HealthyThreshold":1,"UnhealthyThreshold":5}' \
        --output json > /tmp/apprunner-update-response.json
    
    echo "✅ Service update initiated"
fi

echo ""
echo "=== Waiting for Service to be Running ==="
echo "This may take 5-10 minutes..."
aws apprunner wait service-running --service-arn "$SERVICE_ARN" --region "$REGION" || {
    echo ""
    echo "⚠️  Service did not reach RUNNING status"
    echo "Checking status..."
    aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --output json | jq -r '{Status: .Service.Status, StatusMessage: .Service.StatusMessage}'
    echo ""
    echo "Check CloudWatch logs for details:"
    echo "aws logs tail /aws/apprunner/$SERVICE_NAME/service --follow --region $REGION"
    exit 1
}

echo "✅ Service is RUNNING"
echo ""

# Configure custom domain
echo "=== Configuring Custom Domain ==="
DOMAIN_ASSOCIATION=$(aws apprunner list-custom-domains --service-arn "$SERVICE_ARN" --region "$REGION" --query "CustomDomains[?Domain=='$CUSTOM_DOMAIN']" --output json) || DOMAIN_ASSOCIATION="[]"

if [ "$DOMAIN_ASSOCIATION" = "[]" ]; then
    echo "Associating custom domain: $CUSTOM_DOMAIN"
    
    ASSOCIATE_RESPONSE=$(aws apprunner associate-custom-domain \
        --service-arn "$SERVICE_ARN" \
        --domain-name "$CUSTOM_DOMAIN" \
        --enable-www-subdomain false \
        --region "$REGION" \
        --output json)
    
    DOMAIN_STATUS=$(echo "$ASSOCIATE_RESPONSE" | jq -r '.CustomDomain.Status')
    DOMAIN_CNAME=$(echo "$ASSOCIATE_RESPONSE" | jq -r '.CustomDomain.CertificateValidationRecords[0].Name // ""')
    DOMAIN_CNAME_VALUE=$(echo "$ASSOCIATE_RESPONSE" | jq -r '.CustomDomain.CertificateValidationRecords[0].Value // ""')
    
    echo "✅ Custom domain association initiated"
    echo "Domain Status: $DOMAIN_STATUS"
    
    if [ -n "$DOMAIN_CNAME" ] && [ -n "$DOMAIN_CNAME_VALUE" ]; then
        echo ""
        echo "=== Creating Route53 CNAME Record ==="
        echo "CNAME Name: $DOMAIN_CNAME"
        echo "CNAME Value: $DOMAIN_CNAME_VALUE"
        
        # Create Route53 record
        aws route53 change-resource-record-sets \
            --hosted-zone-id "$ROUTE53_ZONE_ID" \
            --change-batch "{
                \"Changes\": [{
                    \"Action\": \"UPSERT\",
                    \"ResourceRecordSet\": {
                        \"Name\": \"$DOMAIN_CNAME\",
                        \"Type\": \"CNAME\",
                        \"TTL\": 300,
                        \"ResourceRecords\": [{\"Value\": \"$DOMAIN_CNAME_VALUE\"}]
                    }
                }]
            }" \
            --output json > /tmp/route53-change.json
        
        CHANGE_ID=$(cat /tmp/route53-change.json | jq -r '.ChangeInfo.Id')
        echo "✅ Route53 record created. Change ID: $CHANGE_ID"
        echo "Waiting for DNS propagation (this may take a few minutes)..."
        
        aws route53 wait resource-record-sets-changed --id "$CHANGE_ID" || true
    fi
    
    # Wait for domain to be active
    echo "Waiting for domain to become active..."
    for i in {1..30}; do
        DOMAIN_STATUS=$(aws apprunner describe-custom-domains --service-arn "$SERVICE_ARN" --region "$REGION" --query "CustomDomains[?Domain=='$CUSTOM_DOMAIN'].Status" --output text)
        if [ "$DOMAIN_STATUS" = "ACTIVE" ]; then
            echo "✅ Custom domain is ACTIVE"
            break
        fi
        echo "Domain status: $DOMAIN_STATUS (attempt $i/30)"
        sleep 10
    done
    
else
    echo "Custom domain already associated: $CUSTOM_DOMAIN"
    DOMAIN_STATUS=$(aws apprunner describe-custom-domains --service-arn "$SERVICE_ARN" --region "$REGION" --query "CustomDomains[?Domain=='$CUSTOM_DOMAIN'].Status" --output text)
    echo "Domain Status: $DOMAIN_STATUS"
fi

echo ""

# Test health endpoint
echo "=== Testing Health Endpoint ==="
sleep 5

# Try custom domain first, fallback to service URL
HEALTH_URL="$API_BASE_URL/health"
if ! curl -f -s "$HEALTH_URL" > /dev/null 2>&1; then
    HEALTH_URL="$SERVICE_URL/health"
fi

if curl -f -s "$HEALTH_URL" > /dev/null; then
    echo "✅ Health check passed: $HEALTH_URL"
    curl -s "$HEALTH_URL" | jq . || curl -s "$HEALTH_URL"
else
    echo "⚠️  Health check failed. Service may still be starting."
    echo "Try again in a few minutes: curl $HEALTH_URL"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete"
echo "=========================================="
echo "Service ARN: $SERVICE_ARN"
echo "Service URL: $SERVICE_URL"
echo "Custom Domain: $CUSTOM_DOMAIN"
echo "API Base URL: $API_BASE_URL"
echo ""
echo "Health Check: $API_BASE_URL/health"
echo ""
echo "Next Steps:"
echo "1. Verify DNS propagation: dig $CUSTOM_DOMAIN"
echo "2. Check CloudWatch logs: aws logs tail /aws/apprunner/$SERVICE_NAME/service --follow --region $REGION"
echo "3. Monitor service: aws apprunner describe-service --service-arn $SERVICE_ARN --region $REGION"
echo "4. Test API: curl $API_BASE_URL/health"

