#!/bin/bash
# Validate Nerava Production Deployment
# This script performs comprehensive validation of all endpoints and services

set -euo pipefail

# Configuration
export API_BASE_URL="${API_BASE_URL:-https://api.nerava.network}"
export LANDING_URL="${LANDING_URL:-https://nerava.network}"
export DRIVER_URL="${DRIVER_URL:-https://app.nerava.network}"
export MERCHANT_URL="${MERCHANT_URL:-https://merchant.nerava.network}"
export ADMIN_URL="${ADMIN_URL:-https://admin.nerava.network}"
export PHOTOS_URL="${PHOTOS_URL:-https://photos.nerava.network}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNED=0

# Function to print test result
print_result() {
    local status=$1
    local message=$2
    
    case $status in
        PASS)
            echo -e "${GREEN}✅ PASS${NC}: $message"
            ((TESTS_PASSED++))
            ;;
        FAIL)
            echo -e "${RED}❌ FAIL${NC}: $message"
            ((TESTS_FAILED++))
            ;;
        WARN)
            echo -e "${YELLOW}⚠️  WARN${NC}: $message"
            ((TESTS_WARNED++))
            ;;
    esac
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local description=${3:-"$url"}
    local method=${4:-GET}
    local data=${5:-}
    
    if [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            HTTP_CODE=$(curl -s -o /tmp/curl_response.json -w "%{http_code}" \
                -X POST \
                -H "Content-Type: application/json" \
                -d "$data" \
                --max-time 10 \
                "$url" 2>/dev/null || echo "000")
        else
            HTTP_CODE=$(curl -s -o /tmp/curl_response.json -w "%{http_code}" \
                -X POST \
                --max-time 10 \
                "$url" 2>/dev/null || echo "000")
        fi
    else
        HTTP_CODE=$(curl -s -o /tmp/curl_response.json -w "%{http_code}" \
            --max-time 10 \
            "$url" 2>/dev/null || echo "000")
    fi
    
    if [ "$HTTP_CODE" = "$expected_status" ]; then
        print_result "PASS" "$description (HTTP $HTTP_CODE)"
        return 0
    else
        print_result "FAIL" "$description (Expected HTTP $expected_status, got $HTTP_CODE)"
        if [ -f /tmp/curl_response.json ]; then
            echo "  Response: $(head -c 200 /tmp/curl_response.json)"
        fi
        return 1
    fi
}

# Function to test DNS resolution
test_dns() {
    local domain=$1
    local description=${2:-"DNS resolution for $domain"}
    
    if command -v dig &> /dev/null; then
        if dig +short "$domain" | grep -q .; then
            print_result "PASS" "$description"
            return 0
        else
            print_result "FAIL" "$description (No DNS records found)"
            return 1
        fi
    elif command -v nslookup &> /dev/null; then
        if nslookup "$domain" &>/dev/null; then
            print_result "PASS" "$description"
            return 0
        else
            print_result "FAIL" "$description (DNS lookup failed)"
            return 1
        fi
    else
        print_result "WARN" "$description (dig/nslookup not available, skipping)"
        return 0
    fi
}

# Function to test SSL certificate
test_ssl() {
    local domain=$1
    local description=${2:-"SSL certificate for $domain"}
    
    if echo | openssl s_client -connect "$domain:443" -servername "$domain" 2>/dev/null | grep -q "Verify return code: 0"; then
        print_result "PASS" "$description"
        return 0
    else
        print_result "WARN" "$description (SSL check failed or openssl not available)"
        return 0
    fi
}

echo "=========================================="
echo "Nerava Deployment Validation"
echo "=========================================="
echo ""
echo "Testing endpoints:"
echo "  API: $API_BASE_URL"
echo "  Landing: $LANDING_URL"
echo "  Driver: $DRIVER_URL"
echo "  Merchant: $MERCHANT_URL"
echo "  Admin: $ADMIN_URL"
echo "  Photos: $PHOTOS_URL"
echo ""

# Check prerequisites
if ! command -v curl &> /dev/null; then
    echo "❌ ERROR: curl not found"
    exit 1
fi

# API Tests
echo "=== API Backend Tests ==="

# Test DNS
test_dns "api.nerava.network" "API DNS resolution"

# Test SSL
test_ssl "api.nerava.network" "API SSL certificate"

# Test health endpoint
test_endpoint "$API_BASE_URL/health" "200" "API health check"

# Test healthz endpoint
test_endpoint "$API_BASE_URL/healthz" "200" "API healthz check"

# Test readyz endpoint
test_endpoint "$API_BASE_URL/readyz" "200" "API readiness check"

# Test cluster endpoint
test_endpoint "$API_BASE_URL/v1/pilot/party/cluster" "200" "API cluster endpoint"

# Test OTP start endpoint
OTP_PAYLOAD='{"phone_number":"+15551234567"}'
test_endpoint "$API_BASE_URL/v1/auth/otp/start" "200" "API OTP start endpoint" "POST" "$OTP_PAYLOAD"

# Test CORS headers
echo ""
echo "Testing CORS headers..."
CORS_HEADER=$(curl -s -I -H "Origin: https://app.nerava.network" \
    -H "Access-Control-Request-Method: POST" \
    -X OPTIONS \
    "$API_BASE_URL/v1/auth/otp/start" 2>/dev/null | grep -i "access-control-allow-origin" || echo "")
if echo "$CORS_HEADER" | grep -q "app.nerava.network"; then
    print_result "PASS" "CORS headers configured correctly"
else
    print_result "WARN" "CORS headers may not be configured correctly"
fi

echo ""

# Frontend Tests
echo "=== Frontend Tests ==="

# Landing Page
echo "Testing Landing Page..."
test_dns "nerava.network" "Landing DNS resolution"
test_ssl "nerava.network" "Landing SSL certificate"
test_endpoint "$LANDING_URL" "200" "Landing page loads"

# Driver App
echo ""
echo "Testing Driver App..."
test_dns "app.nerava.network" "Driver DNS resolution"
test_ssl "app.nerava.network" "Driver SSL certificate"
test_endpoint "$DRIVER_URL" "200" "Driver app loads"

# Check if driver app can call API
echo "  Testing API connectivity from driver app..."
DRIVER_HTML=$(curl -s "$DRIVER_URL" 2>/dev/null || echo "")
if echo "$DRIVER_HTML" | grep -q "api.nerava.network" || echo "$DRIVER_HTML" | grep -q "$API_BASE_URL"; then
    print_result "PASS" "Driver app configured with API URL"
else
    print_result "WARN" "Driver app may not be configured with correct API URL"
fi

# Merchant Portal
echo ""
echo "Testing Merchant Portal..."
test_dns "merchant.nerava.network" "Merchant DNS resolution"
test_ssl "merchant.nerava.network" "Merchant SSL certificate"
test_endpoint "$MERCHANT_URL" "200" "Merchant portal loads"

# Admin Portal
echo ""
echo "Testing Admin Portal..."
test_dns "admin.nerava.network" "Admin DNS resolution"
test_ssl "admin.nerava.network" "Admin SSL certificate"
test_endpoint "$ADMIN_URL" "200" "Admin portal loads"

echo ""

# Photos Tests
echo "=== Merchant Photos Tests ==="
test_dns "photos.nerava.network" "Photos DNS resolution"
test_ssl "photos.nerava.network" "Photos SSL certificate"

# Test a sample photo URL (if photos were uploaded)
PHOTO_TEST_URL="$PHOTOS_URL/asadas_grill/asadas_grill_01.jpg"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$PHOTO_TEST_URL" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    print_result "PASS" "Sample photo loads: $PHOTO_TEST_URL"
elif [ "$HTTP_CODE" = "404" ]; then
    print_result "WARN" "Sample photo not found (may not be uploaded yet): $PHOTO_TEST_URL"
else
    print_result "WARN" "Photos endpoint returned HTTP $HTTP_CODE"
fi

echo ""

# Summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${YELLOW}Warnings: $TESTS_WARNED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All critical tests passed!${NC}"
    echo ""
    echo "Deployment appears to be working correctly."
    echo ""
    echo "Manual verification checklist:"
    echo "1. Open $LANDING_URL in a browser - should load landing page"
    echo "2. Open $DRIVER_URL in a browser - should load driver app"
    echo "3. In driver app, verify API calls work (check browser console)"
    echo "4. Test OTP flow: enter phone number and verify OTP is sent"
    echo "5. Open $MERCHANT_URL - should load merchant portal"
    echo "6. Open $ADMIN_URL - should load admin portal"
    echo "7. Verify merchant photos load: $PHOTOS_URL/asadas_grill/asadas_grill_01.jpg"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review the errors above.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check DNS propagation: dig api.nerava.network"
    echo "2. Check CloudFront distributions: aws cloudfront list-distributions"
    echo "3. Check App Runner service: aws apprunner describe-service --service-arn <arn>"
    echo "4. Check CloudWatch logs for errors"
    exit 1
fi





