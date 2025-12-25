#!/bin/bash
# Phase 0: AWS Discovery Script
# Run this to collect current AWS state before making changes

set -e

echo "=== AWS App Runner + CloudFront Deployment Discovery ==="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if required environment variables are set
if [ -z "$APP_RUNNER_SERVICE_ARN" ]; then
    echo "WARNING: APP_RUNNER_SERVICE_ARN is not set."
    echo "Please set it: export APP_RUNNER_SERVICE_ARN='arn:aws:apprunner:...'"
    echo ""
fi

if [ -z "$APP_RUNNER_URL" ]; then
    echo "WARNING: APP_RUNNER_URL is not set."
    echo "Please set it: export APP_RUNNER_URL='https://...'"
    echo ""
fi

echo "=== 1. AWS Identity ==="
aws sts get-caller-identity
echo ""

if [ -n "$APP_RUNNER_SERVICE_ARN" ]; then
    echo "=== 2. App Runner Service Configuration ==="
    aws apprunner describe-service --service-arn "$APP_RUNNER_SERVICE_ARN" --region us-east-1
    echo ""
    
    echo "=== 3. App Runner Recent Operations ==="
    aws apprunner list-operations --service-arn "$APP_RUNNER_SERVICE_ARN" --region us-east-1 --max-results 20
    echo ""
fi

if [ -n "$APP_RUNNER_URL" ]; then
    echo "=== 4. Backend Health Check Tests ==="
    echo "Testing root endpoint:"
    curl -i "$APP_RUNNER_URL/" || echo "Failed"
    echo ""
    
    echo "Testing /healthz endpoint:"
    curl -i "$APP_RUNNER_URL/healthz" || echo "Failed"
    echo ""
    
    echo "Testing /docs endpoint:"
    curl -i "$APP_RUNNER_URL/docs" || echo "Failed"
    echo ""
fi

echo "=== 5. S3 Buckets (checking for ui-mobile bucket) ==="
aws s3 ls | grep -i "ui-mobile\|nerava\|frontend" || echo "No matching buckets found"
echo ""

echo "=== 6. CloudFront Distributions ==="
aws cloudfront list-distributions --query "DistributionList.Items[*].[Id,DomainName,Status,Origins.Items[0].DomainName]" --output table || echo "Failed to list distributions"
echo ""

echo "=== Discovery Complete ==="
echo "Review the output above and ensure:"
echo "1. App Runner service exists and is configured"
echo "2. Health check endpoint /healthz returns 200"
echo "3. S3 bucket for frontend exists"
echo "4. CloudFront distribution status (if exists)"


