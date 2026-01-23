#!/bin/bash
# AWS CloudWatch Alarms Creation Script for Nerava App Runner Service
# Creates alarms for service health, errors, latency, and critical log patterns
#
# Usage:
#   export AWS_REGION=us-east-1
#   export APP_RUNNER_SERVICE_ARN=arn:aws:apprunner:us-east-1:123456789012:service/nerava-api/abc123
#   export LOG_GROUP_NAME=/aws/apprunner/nerava-api/service/abc123
#   export SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:nerava-alerts
#   ./scripts/aws_create_alarms.sh
#
# Requirements:
#   - AWS CLI configured with appropriate permissions
#   - Environment variables set (see above)
#   - SNS topic created and subscribed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check required environment variables
if [ -z "$AWS_REGION" ]; then
    echo -e "${RED}ERROR:${NC} AWS_REGION environment variable is required"
    exit 1
fi

if [ -z "$APP_RUNNER_SERVICE_ARN" ]; then
    echo -e "${RED}ERROR:${NC} APP_RUNNER_SERVICE_ARN environment variable is required"
    exit 1
fi

if [ -z "$LOG_GROUP_NAME" ]; then
    echo -e "${RED}ERROR:${NC} LOG_GROUP_NAME environment variable is required"
    exit 1
fi

if [ -z "$SNS_TOPIC_ARN" ]; then
    echo -e "${RED}ERROR:${NC} SNS_TOPIC_ARN environment variable is required"
    exit 1
fi

echo "=========================================="
echo "Creating CloudWatch Alarms for Nerava"
echo "=========================================="
echo "Region: $AWS_REGION"
echo "Service ARN: $APP_RUNNER_SERVICE_ARN"
echo "Log Group: $LOG_GROUP_NAME"
echo "SNS Topic: $SNS_TOPIC_ARN"
echo ""

# Extract service name from ARN (for alarm names)
SERVICE_NAME=$(echo "$APP_RUNNER_SERVICE_ARN" | awk -F'/' '{print $NF}')
ALARM_PREFIX="nerava-${SERVICE_NAME}"

# Function to create or update alarm (idempotent)
create_alarm() {
    local alarm_name=$1
    local alarm_description=$2
    local metric_name=$3
    local namespace=$4
    local statistic=$5
    local threshold=$6
    local comparison=$7
    local period=$8
    local evaluation_periods=$9
    
    echo -n "Creating alarm: $alarm_name... "
    
    aws cloudwatch put-metric-alarm \
        --region "$AWS_REGION" \
        --alarm-name "$alarm_name" \
        --alarm-description "$alarm_description" \
        --metric-name "$metric_name" \
        --namespace "$namespace" \
        --statistic "$statistic" \
        --period "$period" \
        --evaluation-periods "$evaluation_periods" \
        --threshold "$threshold" \
        --comparison-operator "$comparison" \
        --alarm-actions "$SNS_TOPIC_ARN" \
        --treat-missing-data breaching \
        --output text > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Function to create log metric filter
create_log_metric_filter() {
    local filter_name=$1
    local pattern=$2
    local metric_name=$3
    local metric_value=$4
    
    echo -n "Creating log metric filter: $filter_name... "
    
    # Check if filter already exists
    if aws logs describe-metric-filters \
        --region "$AWS_REGION" \
        --log-group-name "$LOG_GROUP_NAME" \
        --filter-name-prefix "$filter_name" \
        --output text 2>/dev/null | grep -q "$filter_name"; then
        echo -e "${YELLOW}exists${NC} (skipping)"
        return 0
    fi
    
    aws logs put-metric-filter \
        --region "$AWS_REGION" \
        --log-group-name "$LOG_GROUP_NAME" \
        --filter-name "$filter_name" \
        --filter-pattern "$pattern" \
        --metric-transformations \
            metricName="$metric_name" \
            metricNamespace="Nerava/Logs" \
            metricValue="$metric_value" \
        --output text > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 1. App Runner 5xx Error Rate Alarm (via log metric filter)
echo "Creating log metric filters..."
create_log_metric_filter \
    "${ALARM_PREFIX}-5xx-errors" \
    "[timestamp, request_id, level=ERROR, ...]" \
    "AppRunner5xxErrors" \
    "1"

# Create alarm for 5xx errors
create_alarm \
    "${ALARM_PREFIX}-high-5xx-error-rate" \
    "Alert when 5xx error rate exceeds 5 errors per minute" \
    "AppRunner5xxErrors" \
    "Nerava/Logs" \
    "Sum" \
    "5" \
    "GreaterThanThreshold" \
    "60" \
    "1"

# 2. Health Check Failures (via log metric filter)
create_log_metric_filter \
    "${ALARM_PREFIX}-health-check-failures" \
    "[timestamp, request_id, ...\"healthz\"..., status=5*]" \
    "HealthCheckFailures" \
    "1"

create_alarm \
    "${ALARM_PREFIX}-health-check-failing" \
    "Alert when health check failures occur" \
    "HealthCheckFailures" \
    "Nerava/Logs" \
    "Sum" \
    "1" \
    "GreaterThanThreshold" \
    "60" \
    "1"

# 3. Startup Validation Failures
create_log_metric_filter \
    "${ALARM_PREFIX}-startup-validation-failed" \
    "[timestamp, ...\"STARTUP_VALIDATION_FAILED\"...]" \
    "StartupValidationFailed" \
    "1"

create_alarm \
    "${ALARM_PREFIX}-startup-validation-failed" \
    "Alert when startup validation fails" \
    "StartupValidationFailed" \
    "Nerava/Logs" \
    "Sum" \
    "1" \
    "GreaterThanThreshold" \
    "60" \
    "1"

# 4. Database Connection Failures
create_log_metric_filter \
    "${ALARM_PREFIX}-db-connection-failed" \
    "[timestamp, ...\"Database connection failed\"...]" \
    "DatabaseConnectionFailed" \
    "1"

create_alarm \
    "${ALARM_PREFIX}-db-connection-failed" \
    "Alert when database connection failures occur" \
    "DatabaseConnectionFailed" \
    "Nerava/Logs" \
    "Sum" \
    "1" \
    "GreaterThanThreshold" \
    "300" \
    "1"

# 5. Redis Connection Failures
create_log_metric_filter \
    "${ALARM_PREFIX}-redis-connection-failed" \
    "[timestamp, ...\"Redis connection failed\"...]" \
    "RedisConnectionFailed" \
    "1"

create_alarm \
    "${ALARM_PREFIX}-redis-connection-failed" \
    "Alert when Redis connection failures occur" \
    "RedisConnectionFailed" \
    "Nerava/Logs" \
    "Sum" \
    "1" \
    "GreaterThanThreshold" \
    "300" \
    "1"

# 6. Python Tracebacks (Unhandled Exceptions)
create_log_metric_filter \
    "${ALARM_PREFIX}-tracebacks" \
    "[timestamp, ...\"Traceback\"...]" \
    "PythonTracebacks" \
    "1"

create_alarm \
    "${ALARM_PREFIX}-high-traceback-rate" \
    "Alert when unhandled exceptions (tracebacks) exceed 10 per hour" \
    "PythonTracebacks" \
    "Nerava/Logs" \
    "Sum" \
    "10" \
    "GreaterThanThreshold" \
    "3600" \
    "1"

# 7. Rate Limit Exceeded
create_log_metric_filter \
    "${ALARM_PREFIX}-rate-limit-exceeded" \
    "[timestamp, ...\"Rate limit exceeded\"...]" \
    "RateLimitExceeded" \
    "1"

create_alarm \
    "${ALARM_PREFIX}-high-rate-limit-rate" \
    "Alert when rate limit exceeded events exceed 100 per hour" \
    "RateLimitExceeded" \
    "Nerava/Logs" \
    "Sum" \
    "100" \
    "GreaterThanThreshold" \
    "3600" \
    "1"

# Note: Latency alarm requires App Runner service metrics
# App Runner doesn't expose p95 latency directly, so we'll use a synthetic canary approach
# See docs/OPS_ALARMS_RUNBOOK.md for instructions on setting up CloudWatch Synthetics

echo ""
echo "=========================================="
echo "Alarm Creation Complete"
echo "=========================================="
echo ""
echo "To verify alarms were created:"
echo "  aws cloudwatch describe-alarms --region $AWS_REGION --alarm-name-prefix $ALARM_PREFIX"
echo ""
echo "To test an alarm (staging only):"
echo "  See docs/OPS_ALARMS_RUNBOOK.md for test procedures"
echo ""


