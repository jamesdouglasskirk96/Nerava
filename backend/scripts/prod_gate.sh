#!/bin/bash
# Nerava Production Quality Gate Verification Script
# Checks P0 items before production launch

set -e

echo "================================================"
echo "Nerava Production Quality Gate Verification"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

# Get App Runner service URL from environment or prompt
if [ -z "$NERAVA_BACKEND_URL" ]; then
    echo "Enter App Runner service URL (e.g., https://xxx.awsapprunner.com):"
    read NERAVA_BACKEND_URL
fi

echo ""
echo "Testing: $NERAVA_BACKEND_URL"
echo ""

# P0-1: Health Check (implies JWT_SECRET is valid if app started)
echo "Checking P0-1: Application Health..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$NERAVA_BACKEND_URL/healthz" 2>/dev/null || echo "000")
if [ "$HEALTH" == "200" ]; then
    echo -e "${GREEN}[PASS]${NC} /healthz returns 200"
    ((PASS++))
else
    echo -e "${RED}[FAIL]${NC} /healthz returns $HEALTH (expected 200)"
    ((FAIL++))
fi

# P0-2: Readiness Check (DB + Redis)
echo "Checking P0-2: Readiness Probe..."
READY=$(curl -s -o /dev/null -w "%{http_code}" "$NERAVA_BACKEND_URL/readyz" 2>/dev/null || echo "000")
if [ "$READY" == "200" ]; then
    READY_BODY=$(curl -s "$NERAVA_BACKEND_URL/readyz" 2>/dev/null)
    echo -e "${GREEN}[PASS]${NC} /readyz returns 200"
    echo "       Response: $READY_BODY"
    ((PASS++))
else
    echo -e "${RED}[FAIL]${NC} /readyz returns $READY (expected 200)"
    ((FAIL++))
fi

# P0-5: Demo Mode Check
echo "Checking P0-5: Demo Mode Disabled..."
DEMO_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$NERAVA_BACKEND_URL/v1/auth/dev_login" \
    -H "Content-Type: application/json" \
    -d '{}' 2>/dev/null || echo "000")
if [ "$DEMO_STATUS" == "401" ] || [ "$DEMO_STATUS" == "404" ] || [ "$DEMO_STATUS" == "422" ]; then
    echo -e "${GREEN}[PASS]${NC} Dev login rejected (status $DEMO_STATUS)"
    ((PASS++))
elif [ "$DEMO_STATUS" == "200" ]; then
    echo -e "${RED}[FAIL]${NC} Dev login succeeded - DEMO_MODE may be enabled!"
    ((FAIL++))
else
    echo -e "${YELLOW}[WARN]${NC} Dev login returned $DEMO_STATUS (expected 401/404)"
    ((WARN++))
fi

# Check API version endpoint
echo "Checking API availability..."
META=$(curl -s -o /dev/null -w "%{http_code}" "$NERAVA_BACKEND_URL/v1/meta" 2>/dev/null || echo "000")
if [ "$META" == "200" ]; then
    META_BODY=$(curl -s "$NERAVA_BACKEND_URL/v1/meta" 2>/dev/null)
    echo -e "${GREEN}[PASS]${NC} /v1/meta returns 200"
    echo "       Response: $META_BODY"
    ((PASS++))
else
    echo -e "${YELLOW}[WARN]${NC} /v1/meta returns $META"
    ((WARN++))
fi

# Rate limiting check
echo "Checking rate limiting..."
for i in {1..5}; do
    curl -s -o /dev/null "$NERAVA_BACKEND_URL/healthz" 2>/dev/null
done
RATE_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$NERAVA_BACKEND_URL/healthz" 2>/dev/null || echo "000")
if [ "$RATE_CHECK" == "200" ]; then
    echo -e "${GREEN}[PASS]${NC} Rate limiting not triggered on health check (good)"
    ((PASS++))
else
    echo -e "${YELLOW}[WARN]${NC} Unexpected response after multiple requests: $RATE_CHECK"
    ((WARN++))
fi

echo ""
echo "================================================"
echo "AWS Configuration Checks (requires AWS CLI)"
echo "================================================"
echo ""

# Check if AWS CLI is available
if command -v aws &> /dev/null; then
    echo "Checking CloudWatch Alarms..."
    ALARMS=$(aws cloudwatch describe-alarms --alarm-name-prefix nerava --query 'MetricAlarms[].AlarmName' --output text 2>/dev/null || echo "")
    if [ -n "$ALARMS" ]; then
        echo -e "${GREEN}[PASS]${NC} Found CloudWatch alarms: $ALARMS"
        ((PASS++))
    else
        echo -e "${RED}[FAIL]${NC} No CloudWatch alarms found with prefix 'nerava'"
        echo "       Create alarms for: healthcheck, high-error-rate, high-latency"
        ((FAIL++))
    fi
else
    echo -e "${YELLOW}[SKIP]${NC} AWS CLI not available - skipping AWS checks"
    ((WARN++))
fi

echo ""
echo "================================================"
echo "Summary"
echo "================================================"
echo ""
echo -e "${GREEN}PASSED:${NC} $PASS"
echo -e "${RED}FAILED:${NC} $FAIL"
echo -e "${YELLOW}WARNINGS:${NC} $WARN"
echo ""

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}PRODUCTION GATE: BLOCKED${NC}"
    echo "Fix the failed items before launching to production."
    exit 1
elif [ $WARN -gt 0 ]; then
    echo -e "${YELLOW}PRODUCTION GATE: CONDITIONALLY PASSED${NC}"
    echo "Review warnings before launching to production."
    exit 0
else
    echo -e "${GREEN}PRODUCTION GATE: PASSED${NC}"
    echo "All checks passed. Ready for production!"
    exit 0
fi
