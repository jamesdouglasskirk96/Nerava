#!/bin/bash
# Production Quality Gate Automated Checks
# Run this script to perform automated checks on the codebase

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=========================================="
echo "Production Quality Gate Automated Checks"
echo "=========================================="
echo ""

BACKEND_DIR="$REPO_ROOT/nerava-backend-v9"
ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}ERROR:${NC} $1"
    ((ERRORS++))
}

warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
    ((WARNINGS++))
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

# 1. Check for TODO/FIXME/XXX comments
echo "1. Scanning for TODO/FIXME/XXX comments..."
TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX" --include="*.py" --include="*.js" --include="*.ts" --include="*.tsx" "$BACKEND_DIR/app" "$REPO_ROOT/ui-mobile" 2>/dev/null | wc -l | tr -d ' ')
if [ "$TODO_COUNT" -gt 0 ]; then
    warning "Found $TODO_COUNT TODO/FIXME/XXX comments"
    echo "  Sample (first 10):"
    grep -r "TODO\|FIXME\|XXX" --include="*.py" --include="*.js" --include="*.ts" --include="*.tsx" "$BACKEND_DIR/app" "$REPO_ROOT/ui-mobile" 2>/dev/null | head -10 | sed 's/^/    /'
else
    success "No TODO/FIXME/XXX comments found"
fi
echo ""

# 2. Check for hardcoded secrets
echo "2. Scanning for potential hardcoded secrets..."
SECRET_PATTERNS=("password\s*=\s*['\"].*['\"]" "api[_-]?key\s*=\s*['\"].*['\"]" "secret\s*=\s*['\"].*['\"]" "token\s*=\s*['\"].*['\"]")
SECRET_FOUND=0
for pattern in "${SECRET_PATTERNS[@]}"; do
    COUNT=$(grep -riE "$pattern" --include="*.py" --include="*.js" --include="*.ts" "$BACKEND_DIR/app" "$REPO_ROOT/ui-mobile" 2>/dev/null | grep -v "dev-secret\|REPLACE_ME\|your_.*_here" | wc -l | tr -d ' ')
    if [ "$COUNT" -gt 0 ]; then
        warning "Potential hardcoded secrets found (pattern: $pattern): $COUNT"
        ((SECRET_FOUND++))
    fi
done
if [ "$SECRET_FOUND" -eq 0 ]; then
    success "No obvious hardcoded secrets found"
fi
echo ""

# 3. Check for dev-only bypasses
echo "3. Checking for dev-only bypasses..."
DEV_BYPASSES=("NERAVA_DEV_ALLOW_ANON_USER" "NERAVA_DEV_ALLOW_ANON_DRIVER" "DEMO_MODE" "DEV_WEBHOOK_BYPASS")
for bypass in "${DEV_BYPASSES[@]}"; do
    if grep -r "$bypass" --include="*.py" "$BACKEND_DIR/app" 2>/dev/null | grep -v "validate\|check\|False\|false" | grep -q "true\|True\|enabled"; then
        warning "Found potential dev bypass: $bypass"
    fi
done
success "Dev bypass check complete"
echo ""

# 4. Check for SQL injection risks
echo "4. Scanning for potential SQL injection risks..."
SQL_INJECTION_COUNT=$(grep -r "execute.*\+.*request\|execute.*\+.*query\|execute.*%s\|execute.*%d" --include="*.py" "$BACKEND_DIR/app" 2>/dev/null | wc -l | tr -d ' ')
if [ "$SQL_INJECTION_COUNT" -gt 0 ]; then
    error "Potential SQL injection risks found: $SQL_INJECTION_COUNT"
    echo "  Review these usages:"
    grep -r "execute.*\+.*request\|execute.*\+.*query\|execute.*%s\|execute.*%d" --include="*.py" "$BACKEND_DIR/app" 2>/dev/null | head -5 | sed 's/^/    /'
else
    success "No obvious SQL injection risks found"
fi
echo ""

# 5. Check for missing error handling
echo "5. Checking for missing error handling..."
UNHANDLED_EXCEPTIONS=$(grep -r "except:" --include="*.py" "$BACKEND_DIR/app/routers" "$BACKEND_DIR/app/services" 2>/dev/null | grep -v "except Exception\|except HTTPException\|except ValueError" | wc -l | tr -d ' ')
if [ "$UNHANDLED_EXCEPTIONS" -gt 0 ]; then
    warning "Found $UNHANDLED_EXCEPTIONS bare except clauses"
else
    success "Error handling looks good"
fi
echo ""

# 6. Check for rate limiting on critical endpoints
echo "6. Checking rate limiting on critical endpoints..."
CRITICAL_ENDPOINTS=("auth" "checkout" "wallet" "redeem" "magic_link")
for endpoint in "${CRITICAL_ENDPOINTS[@]}"; do
    if ! grep -r "rate.*limit\|RateLimit" --include="*.py" -i "$BACKEND_DIR/app/routers" 2>/dev/null | grep -q "$endpoint"; then
        warning "Rate limiting not found for $endpoint endpoint"
    fi
done
success "Rate limiting check complete"
echo ""

# 7. Check for idempotency on wallet operations
echo "7. Checking idempotency on wallet operations..."
if grep -r "idempotenc\|idempotent" --include="*.py" -i "$BACKEND_DIR/app/routers/checkout.py" "$BACKEND_DIR/app/services/nova_service.py" 2>/dev/null | grep -q "."; then
    success "Idempotency checks found in wallet operations"
else
    warning "Idempotency checks may be missing in wallet operations"
fi
echo ""

# 8. Check for webhook signature verification
echo "8. Checking webhook signature verification..."
if grep -r "verify.*signature\|signature.*verify\|Webhook.*construct" --include="*.py" -i "$BACKEND_DIR/app/routers" 2>/dev/null | grep -q "."; then
    success "Webhook signature verification found"
else
    warning "Webhook signature verification may be missing"
fi
echo ""

# 9. Run unit tests if available
echo "9. Running unit tests..."
if [ -f "$BACKEND_DIR/pytest.ini" ] || [ -f "$BACKEND_DIR/pyproject.toml" ]; then
    if command -v pytest &> /dev/null; then
        cd "$BACKEND_DIR"
        if pytest tests/ -v --tb=short 2>&1 | head -50; then
            success "Unit tests passed"
        else
            error "Unit tests failed"
        fi
        cd "$REPO_ROOT"
    else
        warning "pytest not found, skipping unit tests"
    fi
else
    warning "No pytest configuration found"
fi
echo ""

# 10. Check for migration files
echo "10. Checking migration files..."
if [ -d "$BACKEND_DIR/alembic/versions" ]; then
    MIGRATION_COUNT=$(ls -1 "$BACKEND_DIR/alembic/versions"/*.py 2>/dev/null | wc -l | tr -d ' ')
    success "Found $MIGRATION_COUNT migration files"
else
    error "Migration directory not found"
fi
echo ""

# 11. Check for environment variable documentation
echo "11. Checking environment variable documentation..."
if [ -f "$REPO_ROOT/ENV.example" ]; then
    success "ENV.example found"
    ENV_VAR_COUNT=$(grep -c "^[A-Z_]*=" "$REPO_ROOT/ENV.example" 2>/dev/null || echo "0")
    echo "  Found $ENV_VAR_COUNT environment variables documented"
else
    warning "ENV.example not found"
fi
echo ""

# 12. Check for health check endpoints
echo "12. Checking health check endpoints..."
if grep -r "healthz\|readyz" --include="*.py" "$BACKEND_DIR/app" 2>/dev/null | grep -q "."; then
    success "Health check endpoints found"
else
    error "Health check endpoints not found"
fi
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
elif [ "$ERRORS" -eq 0 ]; then
    echo -e "${YELLOW}Checks passed with warnings${NC}"
    exit 0
else
    echo -e "${RED}Checks failed with errors${NC}"
    exit 1
fi

