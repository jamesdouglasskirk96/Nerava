#!/bin/bash
# Production smoke tests for Nerava deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-https://nerava.network}"
API_URL="${API_URL:-https://api.nerava.network}"
DRIVER_URL="${DRIVER_URL:-https://app.nerava.network}"
MERCHANT_URL="${MERCHANT_URL:-https://merchant.nerava.network}"
ADMIN_URL="${ADMIN_URL:-https://admin.nerava.network}"
LANDING_URL="${LANDING_URL:-https://www.nerava.network}"

PASSED=0
FAILED=0

# Test function
test_endpoint() {
  local name=$1
  local url=$2
  local expected_status=${3:-200}
  
  echo -n "Testing $name... "
  
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
  
  if [ "$HTTP_CODE" == "$expected_status" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $HTTP_CODE)"
    ((PASSED++))
    return 0
  else
    echo -e "${RED}✗ FAIL${NC} (HTTP $HTTP_CODE, expected $expected_status)"
    ((FAILED++))
    return 1
  fi
}

echo -e "${YELLOW}Running smoke tests for Nerava production deployment...${NC}\n"

# Test API health endpoint
test_endpoint "API Health" "$API_URL/health" 200

# Test API healthz endpoint (alternative)
test_endpoint "API Healthz" "$API_URL/healthz" 200

# Test driver app
test_endpoint "Driver App" "$DRIVER_URL" 200

# Test merchant app
test_endpoint "Merchant App" "$MERCHANT_URL" 200

# Test admin app
test_endpoint "Admin App" "$ADMIN_URL" 200

# Test landing page (www)
test_endpoint "Landing Page (www)" "$LANDING_URL" 200

# Test landing page (apex)
test_endpoint "Landing Page (apex)" "$BASE_URL" 200

# Summary
echo -e "\n${YELLOW}Test Summary:${NC}"
echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
  echo -e "\n${GREEN}✓ All smoke tests passed!${NC}"
  exit 0
else
  echo -e "\n${RED}✗ Some smoke tests failed${NC}"
  exit 1
fi

