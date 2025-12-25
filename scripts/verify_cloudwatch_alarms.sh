#!/bin/bash
# CloudWatch Alarms Verification Script
# Verifies that alarms created by aws_create_alarms.sh are properly configured
#
# Usage:
#   export AWS_REGION=us-east-1
#   export APP_RUNNER_SERVICE_ARN=arn:aws:apprunner:us-east-1:123456789012:service/nerava-api/abc123
#   ./scripts/verify_cloudwatch_alarms.sh
#
# Or verify all nerava alarms:
#   export AWS_REGION=us-east-1
#   ./scripts/verify_cloudwatch_alarms.sh
#
# Requirements:
#   - AWS CLI configured with appropriate permissions
#   - jq (for JSON parsing)
#   - Environment variable AWS_REGION set

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check required environment variables
if [ -z "${AWS_REGION:-}" ]; then
    echo -e "${RED}ERROR:${NC} AWS_REGION environment variable is required"
    exit 1
fi

# Determine alarm prefix
ALARM_PREFIX="nerava-"
if [ -n "${APP_RUNNER_SERVICE_ARN:-}" ]; then
    SERVICE_NAME=$(echo "$APP_RUNNER_SERVICE_ARN" | awk -F'/' '{print $NF}')
    ALARM_PREFIX="nerava-${SERVICE_NAME}-"
fi

echo "=========================================="
echo "CloudWatch Alarms Verification"
echo "=========================================="
echo "Region: $AWS_REGION"
echo "Alarm Prefix: $ALARM_PREFIX"
echo ""

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${RED}ERROR:${NC} jq is required but not installed"
    echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR:${NC} AWS CLI is required but not installed"
    exit 1
fi

# Fetch alarms with the prefix
echo "Fetching alarms..."
ALARMS_JSON=$(aws cloudwatch describe-alarms \
    --region "$AWS_REGION" \
    --alarm-name-prefix "$ALARM_PREFIX" \
    --output json 2>&1) || {
    echo -e "${RED}ERROR:${NC} Failed to fetch alarms"
    echo "$ALARMS_JSON"
    exit 1
}

ALARM_COUNT=$(echo "$ALARMS_JSON" | jq '.MetricAlarms | length')

if [ "$ALARM_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}WARNING:${NC} No alarms found with prefix '$ALARM_PREFIX'"
    echo ""
    echo "Expected alarms:"
    echo "  - ${ALARM_PREFIX}high-5xx-error-rate"
    echo "  - ${ALARM_PREFIX}health-check-failing"
    echo "  - ${ALARM_PREFIX}startup-validation-failed"
    echo "  - ${ALARM_PREFIX}db-connection-failed"
    echo "  - ${ALARM_PREFIX}redis-connection-failed"
    echo "  - ${ALARM_PREFIX}high-traceback-rate"
    echo "  - ${ALARM_PREFIX}high-rate-limit-rate"
    echo ""
    echo "Create alarms with: ./scripts/aws_create_alarms.sh"
    exit 1
fi

echo "Found $ALARM_COUNT alarm(s)"
echo ""

# Track issues
ISSUES=()
FAILED_COUNT=0
NO_SNS_ALARMS=()
ALARM_STATE_ALARMS=()

# Print table header
printf "%-50s %-30s %-12s %-50s\n" "AlarmName" "Metric" "State" "SNS Target"
printf "%-50s %-30s %-12s %-50s\n" "$(printf '%*s' 50 '' | tr ' ' '-')" "$(printf '%*s' 30 '' | tr ' ' '-')" "$(printf '%*s' 12 '' | tr ' ' '-')" "$(printf '%*s' 50 '' | tr ' ' '-')"

# Process each alarm (using process substitution to avoid subshell)
while IFS= read -r alarm; do
    ALARM_NAME=$(echo "$alarm" | jq -r '.AlarmName')
    METRIC_NAME=$(echo "$alarm" | jq -r '.MetricName // "N/A"')
    STATE=$(echo "$alarm" | jq -r '.StateValue')
    
    # Get SNS actions (alarm actions)
    SNS_ACTIONS=$(echo "$alarm" | jq -r '.AlarmActions[]? // empty')
    SNS_COUNT=$(echo "$SNS_ACTIONS" | grep -c . || echo "0")
    
    # Extract SNS topic name from ARN (first one if multiple)
    FIRST_SNS_ARN=$(echo "$SNS_ACTIONS" | head -n1)
    if [ -n "$FIRST_SNS_ARN" ]; then
        # Extract topic name from ARN format: arn:aws:sns:region:account:topic-name
        SNS_TARGET=$(echo "$FIRST_SNS_ARN" | awk -F':' '{print $6}')
        # If multiple SNS actions, show count
        SNS_ACTION_COUNT=$(echo "$SNS_ACTIONS" | wc -l | tr -d ' ')
        if [ "$SNS_ACTION_COUNT" -gt 1 ]; then
            SNS_TARGET="${SNS_TARGET} (+$((SNS_ACTION_COUNT - 1)) more)"
        fi
    else
        SNS_TARGET="[NO SNS TARGET]"
    fi
    
    # Determine color for state
    STATE_COLOR=""
    STATE_ICON=""
    if [ "$STATE" = "OK" ]; then
        STATE_COLOR="$GREEN"
        STATE_ICON="✓"
    elif [ "$STATE" = "ALARM" ]; then
        STATE_COLOR="$RED"
        STATE_ICON="✗"
        ALARM_STATE_ALARMS+=("$ALARM_NAME")
    else
        STATE_COLOR="$YELLOW"
        STATE_ICON="?"
    fi
    
    # Print table row
    printf "%-50s %-30s ${STATE_COLOR}%-12s${NC} %-50s\n" \
        "$ALARM_NAME" \
        "$METRIC_NAME" \
        "${STATE_ICON} $STATE" \
        "$SNS_TARGET"
    
    # Check for issues
    if [ "$SNS_COUNT" -eq 0 ]; then
        ISSUES+=("Alarm '$ALARM_NAME' has no SNS action configured")
        NO_SNS_ALARMS+=("$ALARM_NAME")
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    # Note: We don't fail on ALARM state automatically because alarms might be legitimately firing
    # But we'll note it in the summary
done < <(echo "$ALARMS_JSON" | jq -c '.MetricAlarms[]')

echo ""

# Get alarm states summary
ALARM_STATES=$(echo "$ALARMS_JSON" | jq -r '.MetricAlarms[].StateValue' | sort | uniq -c)
OK_COUNT=$(echo "$ALARMS_JSON" | jq '[.MetricAlarms[] | select(.StateValue == "OK")] | length')
ALARM_COUNT=$(echo "$ALARMS_JSON" | jq '[.MetricAlarms[] | select(.StateValue == "ALARM")] | length')
INSUFFICIENT_COUNT=$(echo "$ALARMS_JSON" | jq '[.MetricAlarms[] | select(.StateValue == "INSUFFICIENT_DATA")] | length')

# Print summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo ""
echo "Total alarms: $ALARM_COUNT"
echo -e "${GREEN}OK:${NC} $OK_COUNT"
if [ "$ALARM_COUNT" -gt 0 ]; then
    echo -e "${RED}ALARM:${NC} $ALARM_COUNT"
fi
if [ "$INSUFFICIENT_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}INSUFFICIENT_DATA:${NC} $INSUFFICIENT_COUNT"
fi
echo ""

# Check for alarms in ALARM state
if [ "$ALARM_COUNT" -gt 0 ]; then
    echo -e "${RED}ERROR:${NC} $ALARM_COUNT alarm(s) are in ALARM state:"
    echo "$ALARMS_JSON" | jq -r '.MetricAlarms[] | select(.StateValue == "ALARM") | "  - \(.AlarmName): \(.StateReason)"'
    echo ""
    FAILED_COUNT=$((FAILED_COUNT + ALARM_COUNT))
fi

# Check for alarms with no SNS actions
if [ ${#NO_SNS_ALARMS[@]} -gt 0 ]; then
    echo -e "${RED}ERROR:${NC} Alarms without SNS actions:"
    for alarm_name in "${NO_SNS_ALARMS[@]}"; do
        echo "  - $alarm_name"
    done
    echo ""
fi

# Print remediation steps if issues found
if [ ${#ISSUES[@]} -gt 0 ] || [ ${#NO_SNS_ALARMS[@]} -gt 0 ] || [ "$ALARM_COUNT" -gt 0 ]; then
    echo "=========================================="
    echo "Remediation Steps"
    echo "=========================================="
    echo ""
    
    if [ ${#NO_SNS_ALARMS[@]} -gt 0 ]; then
        echo "1. Add SNS actions to alarms without notifications:"
        echo ""
        for alarm_name in "${NO_SNS_ALARMS[@]}"; do
            echo "   aws cloudwatch put-metric-alarm \\"
            echo "     --region $AWS_REGION \\"
            echo "     --alarm-name \"$alarm_name\" \\"
            echo "     --alarm-actions \"arn:aws:sns:$AWS_REGION:ACCOUNT_ID:nerava-alerts\" \\"
            echo "     --no-cli-pager"
            echo ""
        done
        echo "   Replace ACCOUNT_ID with your AWS account ID"
        echo "   Replace 'nerava-alerts' with your SNS topic name if different"
        echo ""
        echo "   Or re-run aws_create_alarms.sh to recreate alarms with SNS actions"
        echo ""
    fi
    
    if [ "$ALARM_COUNT" -gt 0 ]; then
        echo "$([ ${#NO_SNS_ALARMS[@]} -gt 0 ] && echo "2" || echo "1"). Investigate alarms in ALARM state:"
        echo "   - Review CloudWatch metrics dashboard:"
        echo "     aws cloudwatch get-metric-statistics --region $AWS_REGION --namespace <namespace> --metric-name <metric>"
        echo "   - Check application logs for errors"
        echo "   - Verify alarm thresholds are appropriate"
        echo "   - If this is a false positive, adjust alarm thresholds or fix underlying issues"
        echo "   - If this is expected (e.g., during maintenance), acknowledge the alarm"
        echo ""
    fi
    
    if [ ${#NO_SNS_ALARMS[@]} -gt 0 ] && [ "$ALARM_COUNT" -gt 0 ]; then
        STEP_NUM=3
    elif [ ${#NO_SNS_ALARMS[@]} -gt 0 ] || [ "$ALARM_COUNT" -gt 0 ]; then
        STEP_NUM=2
    else
        STEP_NUM=1
    fi
    echo "$STEP_NUM. Re-run this script to verify fixes:"
    echo "   ./scripts/verify_cloudwatch_alarms.sh"
    echo ""
    
    exit 1
fi

# All checks passed
echo -e "${GREEN}✓ All alarms are properly configured${NC}"
echo ""
echo "All alarms have:"
echo "  ✓ SNS action configured"
echo "  ✓ State is OK or INSUFFICIENT_DATA (expected for new alarms)"
echo ""
exit 0

