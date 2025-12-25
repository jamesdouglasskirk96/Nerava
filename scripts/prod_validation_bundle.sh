#!/bin/bash
# Production Validation Bundle
# Orchestrates all pre-launch validation checks for production deployment
#
# Usage:
#   export NERAVA_BACKEND_URL="https://your-backend-url.com"
#   export BASE_URL="https://your-backend-url.com"  # Can be same as NERAVA_BACKEND_URL
#   export ADMIN_TOKEN="your-jwt-token-here"
#   ./scripts/prod_validation_bundle.sh
#
# Requirements:
#   - NERAVA_BACKEND_URL: Backend API URL for production gate checks
#   - BASE_URL: Base URL for admin smoke tests (typically same as NERAVA_BACKEND_URL)
#   - ADMIN_TOKEN: JWT token for admin endpoint authentication
#
# Exit Codes:
#   0 - All checks passed
#   1 - One or more checks failed
#
# This script runs:
#   1. pytest -q (unit and integration tests)
#   2. prod_gate.sh (production quality gate checks)
#   3. admin_smoke_test.sh (admin console smoke tests)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Track results
RESULTS=()
TOTAL_CHECKS=0
FAILED_CHECKS=0

# Function to redact secrets from output
redact_secrets() {
    local input="$1"
    # Redact JWT tokens (Bearer tokens)
    input=$(echo "$input" | sed -E 's/(Bearer[[:space:]]+)[^[:space:]]+/Bearer [REDACTED]/g')
    # Redact ADMIN_TOKEN values
    input=$(echo "$input" | sed -E 's/(ADMIN_TOKEN=)[^[:space:]]+/\1[REDACTED]/g')
    # Redact tokens in URLs
    input=$(echo "$input" | sed -E 's/(token=)[^&[:space:]]+/\1[REDACTED]/g')
    # Redact API keys
    input=$(echo "$input" | sed -E 's/(api[_-]?key=)[^&[:space:]]+/\1[REDACTED]/gi')
    # Redact passwords in URLs
    input=$(echo "$input" | sed -E 's/(password=)[^&[:space:]]+/\1[REDACTED]/g')
    # Redact access tokens
    input=$(echo "$input" | sed -E 's/("access_token":\s*")[^"]+/\1[REDACTED]/g')
    echo "$input"
}

# Function to run a check and capture results
run_check() {
    local check_name="$1"
    local check_command="$2"
    local check_dir="${3:-$REPO_ROOT}"
    
    echo ""
    echo "=========================================="
    echo "Running: $check_name"
    echo "=========================================="
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    # Capture output and exit code
    # Use a subshell with set +e to capture errors without exiting
    local output
    local exit_code
    
    set +e
    output=$(cd "$check_dir" && eval "$check_command" 2>&1)
    exit_code=$?
    set -e
    
    # Redact secrets from output before displaying
    local redacted_output
    redacted_output=$(redact_secrets "$output")
    
    # Display redacted output
    echo "$redacted_output"
    
    # Record result
    if [ $exit_code -eq 0 ]; then
        RESULTS+=("PASS:$check_name")
        echo ""
        echo -e "${GREEN}✓ PASS${NC}: $check_name"
        return 0
    else
        RESULTS+=("FAIL:$check_name")
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        echo ""
        echo -e "${RED}✗ FAIL${NC}: $check_name (exit code: $exit_code)"
        return $exit_code
    fi
}

# Validate required environment variables
echo "=========================================="
echo "Production Validation Bundle"
echo "=========================================="
echo ""

MISSING_VARS=()

if [ -z "${NERAVA_BACKEND_URL:-}" ]; then
    MISSING_VARS+=("NERAVA_BACKEND_URL")
fi

if [ -z "${BASE_URL:-}" ]; then
    MISSING_VARS+=("BASE_URL")
fi

if [ -z "${ADMIN_TOKEN:-}" ]; then
    MISSING_VARS+=("ADMIN_TOKEN")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}ERROR:${NC} Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Usage:"
    echo "  export NERAVA_BACKEND_URL=\"https://your-backend-url.com\""
    echo "  export BASE_URL=\"https://your-backend-url.com\""
    echo "  export ADMIN_TOKEN=\"your-jwt-token-here\""
    echo "  ./scripts/prod_validation_bundle.sh"
    exit 1
fi

echo "Environment variables configured:"
echo "  NERAVA_BACKEND_URL: ${NERAVA_BACKEND_URL}"
echo "  BASE_URL: ${BASE_URL}"
echo "  ADMIN_TOKEN: [REDACTED]"
echo ""

# Check 1: Run pytest
if ! run_check "pytest -q" "pytest -q" "$REPO_ROOT/nerava-backend-v9"; then
    echo ""
    echo -e "${RED}=========================================="
    echo "VALIDATION FAILED: pytest failed"
    echo "==========================================${NC}"
    exit 1
fi

# Check 2: Run prod_gate.sh
if ! run_check "prod_gate.sh" "NERAVA_BACKEND_URL=\"$NERAVA_BACKEND_URL\" \"$REPO_ROOT/nerava-backend-v9/scripts/prod_gate.sh\"" "$REPO_ROOT"; then
    echo ""
    echo -e "${RED}=========================================="
    echo "VALIDATION FAILED: prod_gate.sh failed"
    echo "==========================================${NC}"
    exit 1
fi

# Check 3: Run admin_smoke_test.sh
if ! run_check "admin_smoke_test.sh" "BASE_URL=\"$BASE_URL\" ADMIN_TOKEN=\"$ADMIN_TOKEN\" \"$REPO_ROOT/scripts/admin_smoke_test.sh\"" "$REPO_ROOT"; then
    echo ""
    echo -e "${RED}=========================================="
    echo "VALIDATION FAILED: admin_smoke_test.sh failed"
    echo "==========================================${NC}"
    exit 1
fi

# Print summary
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo ""

for result in "${RESULTS[@]}"; do
    status="${result%%:*}"
    name="${result#*:}"
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $name"
    else
        echo -e "${RED}✗ FAIL${NC}: $name"
    fi
done

echo ""
echo "Total checks: $TOTAL_CHECKS"
echo "Passed: $((TOTAL_CHECKS - FAILED_CHECKS))"
echo "Failed: $FAILED_CHECKS"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "ALL CHECKS PASSED"
    echo "Production validation complete"
    echo "==========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}=========================================="
    echo "VALIDATION FAILED"
    echo "$FAILED_CHECKS check(s) failed"
    echo "==========================================${NC}"
    exit 1
fi

