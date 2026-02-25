#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Nerava Production Monitoring Setup
# Creates SNS topic, CloudWatch alarms, and log-based metric filters
# using AWS CLI. Run once to bootstrap; safe to re-run (creates or updates).
#
# Prerequisites: AWS CLI configured with us-east-1 credentials
# Usage: ./infra/setup_monitoring.sh [--email you@example.com]
# ============================================================================

REGION="us-east-1"
SNS_TOPIC_NAME="nerava-prod-alerts"
APP_RUNNER_LOG_GROUP="/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application"
RDS_INSTANCE_ID="nerava-db"
APP_RUNNER_SERVICE_NAME="nerava-backend"

# Parse args
ALERT_EMAIL=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --email) ALERT_EMAIL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "========================================"
echo "  Nerava Production Monitoring Setup"
echo "========================================"
echo "  Region: $REGION"
echo ""

# ── 1. SNS Topic ────────────────────────────────────────────────────

echo "[1/4] Creating SNS topic: $SNS_TOPIC_NAME"
TOPIC_ARN=$(aws sns create-topic \
  --name "$SNS_TOPIC_NAME" \
  --region "$REGION" \
  --query 'TopicArn' --output text)
echo "  Topic ARN: $TOPIC_ARN"

if [[ -n "$ALERT_EMAIL" ]]; then
  echo "  Subscribing $ALERT_EMAIL (confirm via email)"
  aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol email \
    --notification-endpoint "$ALERT_EMAIL" \
    --region "$REGION" > /dev/null
fi

# ── 2. App Runner / RDS CloudWatch Alarms ───────────────────────────

echo ""
echo "[2/4] Creating CloudWatch metric alarms"

# Helper: create or update a metric alarm
put_alarm() {
  local name="$1" namespace="$2" metric="$3" stat="$4" threshold="$5" \
        comparison="$6" period="$7" eval_periods="$8" description="$9"
  local dimensions="${10:-}"

  local dim_args=()
  if [[ -n "$dimensions" ]]; then
    dim_args=(--dimensions "$dimensions")
  fi

  aws cloudwatch put-metric-alarm \
    --alarm-name "$name" \
    --alarm-description "$description" \
    --namespace "$namespace" \
    --metric-name "$metric" \
    --statistic "$stat" \
    --threshold "$threshold" \
    --comparison-operator "$comparison" \
    --period "$period" \
    --evaluation-periods "$eval_periods" \
    --alarm-actions "$TOPIC_ARN" \
    --ok-actions "$TOPIC_ARN" \
    --treat-missing-data notBreaching \
    --region "$REGION" \
    "${dim_args[@]}" 2>/dev/null

  echo "  Created: $name"
}

# High 5xx rate (App Runner)
put_alarm "nerava-high-5xx-rate" \
  "AWS/AppRunner" "5xxCount" "Sum" 10 \
  "GreaterThanThreshold" 300 2 \
  "Nerava: >10 5xx errors in 5 min for 2 consecutive periods" \
  "Name=ServiceName,Value=$APP_RUNNER_SERVICE_NAME"

# High latency p99 (App Runner — use Average as proxy since p99 requires extended stats)
put_alarm "nerava-high-latency" \
  "AWS/AppRunner" "RequestLatency" "Average" 5000 \
  "GreaterThanThreshold" 300 2 \
  "Nerava: avg request latency >5s for 2 consecutive periods" \
  "Name=ServiceName,Value=$APP_RUNNER_SERVICE_NAME"

# No traffic (App Runner)
put_alarm "nerava-no-traffic" \
  "AWS/AppRunner" "RequestCount" "Sum" 0 \
  "LessThanOrEqualToThreshold" 300 2 \
  "Nerava: zero requests for 10 min (possible outage)" \
  "Name=ServiceName,Value=$APP_RUNNER_SERVICE_NAME"

# RDS High CPU
put_alarm "nerava-rds-high-cpu" \
  "AWS/RDS" "CPUUtilization" "Average" 80 \
  "GreaterThanThreshold" 300 2 \
  "Nerava RDS: CPU >80% for 10 min" \
  "Name=DBInstanceIdentifier,Value=$RDS_INSTANCE_ID"

# RDS Low Storage (<2 GB = 2147483648 bytes)
put_alarm "nerava-rds-low-storage" \
  "AWS/RDS" "FreeStorageSpace" "Minimum" 2147483648 \
  "LessThanThreshold" 300 1 \
  "Nerava RDS: free storage <2 GB" \
  "Name=DBInstanceIdentifier,Value=$RDS_INSTANCE_ID"

# RDS High Connections
put_alarm "nerava-rds-high-connections" \
  "AWS/RDS" "DatabaseConnections" "Average" 80 \
  "GreaterThanThreshold" 300 2 \
  "Nerava RDS: >80 active connections for 10 min" \
  "Name=DBInstanceIdentifier,Value=$RDS_INSTANCE_ID"

# ── 3. Log-based Metric Filters ────────────────────────────────────

echo ""
echo "[3/4] Creating log-based metric filters and alarms"

# Helper: create metric filter + alarm
put_log_alarm() {
  local filter_name="$1" pattern="$2" metric_name="$3" \
        threshold="$4" description="$5"

  aws logs put-metric-filter \
    --log-group-name "$APP_RUNNER_LOG_GROUP" \
    --filter-name "$filter_name" \
    --filter-pattern "$pattern" \
    --metric-transformations \
      "metricName=$metric_name,metricNamespace=Nerava/Application,metricValue=1,defaultValue=0" \
    --region "$REGION" 2>/dev/null

  aws cloudwatch put-metric-alarm \
    --alarm-name "nerava-log-$metric_name" \
    --alarm-description "$description" \
    --namespace "Nerava/Application" \
    --metric-name "$metric_name" \
    --statistic "Sum" \
    --threshold "$threshold" \
    --comparison-operator "GreaterThanThreshold" \
    --period 300 \
    --evaluation-periods 1 \
    --alarm-actions "$TOPIC_ARN" \
    --ok-actions "$TOPIC_ARN" \
    --treat-missing-data notBreaching \
    --region "$REGION" 2>/dev/null

  echo "  Created filter+alarm: $filter_name (threshold: >$threshold in 5min)"
}

# Unhandled exceptions
put_log_alarm "nerava-unhandled-exceptions" \
  "\"Traceback\"" \
  "UnhandledExceptions" \
  10 "Nerava: >10 unhandled exceptions in 5 min"

# Auth failures (brute force detection)
put_log_alarm "nerava-auth-failures" \
  "\"401\" \"Unauthorized\"" \
  "AuthFailures" \
  50 "Nerava: >50 auth failures in 5 min (possible brute force)"

# Database errors
put_log_alarm "nerava-database-errors" \
  "?\"OperationalError\" ?\"connection refused\" ?\"connection reset\"" \
  "DatabaseErrors" \
  5 "Nerava: >5 database errors in 5 min"

# ERROR-level log entries
put_log_alarm "nerava-error-logs" \
  "\"[ERROR]\"" \
  "ErrorLogs" \
  10 "Nerava: >10 ERROR-level logs in 5 min"

# ── 4. Summary ──────────────────────────────────────────────────────

echo ""
echo "[4/4] Setup complete!"
echo ""
echo "  SNS Topic: $TOPIC_ARN"
echo "  Alarms created: 10 (6 metric + 4 log-based)"
echo ""
echo "  Next steps:"
echo "  1. Confirm the SNS email subscription (check your inbox)"
echo "  2. Verify alarms: aws cloudwatch describe-alarms --alarm-name-prefix nerava- --region $REGION --query 'MetricAlarms[*].[AlarmName,StateValue]' --output table"
echo "  3. (Optional) Add Slack via Lambda subscriber to $TOPIC_ARN"
echo ""
