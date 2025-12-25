#!/bin/bash
# Admin Console Smoke Test
# Tests key admin endpoints against a configured BASE_URL
# Usage: BASE_URL=http://localhost:8001 ADMIN_TOKEN=<jwt_token> ./scripts/admin_smoke_test.sh

set -e

BASE_URL="${BASE_URL:-http://localhost:8001}"
ADMIN_TOKEN="${ADMIN_TOKEN:-}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

error() {
    echo -e "${RED}✗ ERROR:${NC} $1"
    ((ERRORS++))
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
    ((WARNINGS++))
}

echo "=========================================="
echo "Admin Console Smoke Test"
echo "=========================================="
echo "BASE_URL: $BASE_URL"
echo ""

# Test 1: Health check
echo "1. Testing /healthz endpoint..."
if curl -s -f -o /dev/null -w "%{http_code}" "$BASE_URL/healthz" | grep -q "200"; then
    success "Health check passed"
else
    error "Health check failed (expected 200)"
fi

# Test 2: Readiness check
echo "2. Testing /readyz endpoint..."
READYZ_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/readyz")
READYZ_CODE=$(echo "$READYZ_RESPONSE" | tail -n1)
READYZ_BODY=$(echo "$READYZ_RESPONSE" | head -n-1)

if [ "$READYZ_CODE" = "200" ]; then
    success "Readiness check passed"
    # Check if response is valid JSON
    if echo "$READYZ_BODY" | jq . > /dev/null 2>&1; then
        success "Readiness response is valid JSON"
        # Check for required fields
        if echo "$READYZ_BODY" | jq -e '.ready' > /dev/null 2>&1; then
            success "Readiness response includes 'ready' field"
        else
            warning "Readiness response missing 'ready' field"
        fi
        if echo "$READYZ_BODY" | jq -e '.checks' > /dev/null 2>&1; then
            success "Readiness response includes 'checks' field"
        else
            warning "Readiness response missing 'checks' field"
        fi
    else
        warning "Readiness response is not valid JSON"
    fi
else
    error "Readiness check failed (expected 200, got $READYZ_CODE)"
    echo "Response: $READYZ_BODY"
fi

# Test 3: Admin auth (if token provided)
if [ -n "$ADMIN_TOKEN" ]; then
    echo "3. Testing admin authentication..."
    AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/admin/overview" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    AUTH_CODE=$(echo "$AUTH_RESPONSE" | tail -n1)
    
    if [ "$AUTH_CODE" = "200" ]; then
        success "Admin authentication passed"
    elif [ "$AUTH_CODE" = "401" ]; then
        error "Admin authentication failed (401 Unauthorized - invalid token)"
    elif [ "$AUTH_CODE" = "403" ]; then
        error "Admin authentication failed (403 Forbidden - user is not admin)"
    else
        error "Admin authentication failed (unexpected status: $AUTH_CODE)"
    fi
else
    warning "ADMIN_TOKEN not set, skipping admin auth test"
    echo "  Set ADMIN_TOKEN env var to test admin endpoints"
fi

# Test 4: Admin overview (if token provided)
if [ -n "$ADMIN_TOKEN" ]; then
    echo "4. Testing /v1/admin/overview endpoint..."
    OVERVIEW_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/admin/overview" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    OVERVIEW_CODE=$(echo "$OVERVIEW_RESPONSE" | tail -n1)
    OVERVIEW_BODY=$(echo "$OVERVIEW_RESPONSE" | head -n-1)
    
    if [ "$OVERVIEW_CODE" = "200" ]; then
        success "Admin overview endpoint accessible"
        # Check if response is valid JSON
        if echo "$OVERVIEW_BODY" | jq . > /dev/null 2>&1; then
            success "Admin overview response is valid JSON"
        else
            warning "Admin overview response is not valid JSON"
        fi
    else
        error "Admin overview endpoint failed (expected 200, got $OVERVIEW_CODE)"
    fi
fi

# Test 5: Users search (if token provided)
if [ -n "$ADMIN_TOKEN" ]; then
    echo "5. Testing /v1/admin/users?query=test endpoint..."
    USERS_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/admin/users?query=test" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    USERS_CODE=$(echo "$USERS_RESPONSE" | tail -n1)
    USERS_BODY=$(echo "$USERS_RESPONSE" | head -n-1)
    
    if [ "$USERS_CODE" = "200" ]; then
        success "Users search endpoint accessible"
        # Check if response is valid JSON (array)
        if echo "$USERS_BODY" | jq . > /dev/null 2>&1; then
            success "Users search response is valid JSON"
        else
            warning "Users search response is not valid JSON"
        fi
    else
        error "Users search endpoint failed (expected 200, got $USERS_CODE)"
    fi
fi

# Test 6: Merchants search (if token provided)
if [ -n "$ADMIN_TOKEN" ]; then
    echo "6. Testing /v1/admin/merchants?query=test endpoint..."
    MERCHANTS_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/admin/merchants?query=test" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    MERCHANTS_CODE=$(echo "$MERCHANTS_RESPONSE" | tail -n1)
    MERCHANTS_BODY=$(echo "$MERCHANTS_RESPONSE" | head -n-1)
    
    if [ "$MERCHANTS_CODE" = "200" ]; then
        success "Merchants search endpoint accessible"
        # Check if response is valid JSON
        if echo "$MERCHANTS_BODY" | jq . > /dev/null 2>&1; then
            success "Merchants search response is valid JSON"
            # Check for merchants array
            if echo "$MERCHANTS_BODY" | jq -e '.merchants' > /dev/null 2>&1; then
                success "Merchants search response includes 'merchants' field"
            else
                warning "Merchants search response missing 'merchants' field"
            fi
        else
            warning "Merchants search response is not valid JSON"
        fi
    else
        error "Merchants search endpoint failed (expected 200, got $MERCHANTS_CODE)"
    fi
fi

# Test 7: Admin health endpoint (if token provided)
if [ -n "$ADMIN_TOKEN" ]; then
    echo "7. Testing /v1/admin/health endpoint..."
    HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/admin/health" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    HEALTH_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
    HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)
    
    if [ "$HEALTH_CODE" = "200" ]; then
        success "Admin health endpoint accessible"
        # Check if response is valid JSON
        if echo "$HEALTH_BODY" | jq . > /dev/null 2>&1; then
            success "Admin health response is valid JSON"
            # Check for required fields
            if echo "$HEALTH_BODY" | jq -e '.ready' > /dev/null 2>&1; then
                success "Admin health response includes 'ready' field"
            else
                warning "Admin health response missing 'ready' field"
            fi
            if echo "$HEALTH_BODY" | jq -e '.checks' > /dev/null 2>&1; then
                success "Admin health response includes 'checks' field"
            else
                warning "Admin health response missing 'checks' field"
            fi
        else
            warning "Admin health response is not valid JSON"
        fi
    else
        error "Admin health endpoint failed (expected 200, got $HEALTH_CODE)"
    fi
fi

# Test 8: Test without token (should fail)
echo "8. Testing admin endpoint without token (should fail)..."
NO_TOKEN_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/v1/admin/overview")
NO_TOKEN_CODE=$(echo "$NO_TOKEN_RESPONSE" | tail -n1)

if [ "$NO_TOKEN_CODE" = "401" ] || [ "$NO_TOKEN_CODE" = "403" ]; then
    success "Admin endpoint correctly rejects requests without token (got $NO_TOKEN_CODE)"
else
    error "Admin endpoint should reject requests without token (expected 401/403, got $NO_TOKEN_CODE)"
fi

# Summary
echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Smoke tests failed with $ERRORS error(s)${NC}"
    exit 1
fi

