#!/bin/bash
# Deployment Entrypoint Guard
# Prevents accidental deployment of legacy code paths (server/src/, server/main_simple.py)
#
# This script checks that deployment configurations only reference the correct entrypoint:
# - app.main_simple:app (correct)
# - NOT server/src/* (legacy, contains bypass logic)
# - NOT server/main_simple.py (legacy entrypoint)

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

BACKEND_DIR="$REPO_ROOT/nerava-backend-v9"
ERRORS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}ERROR:${NC} $1"
    ((ERRORS++))
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

echo "=========================================="
echo "Deployment Entrypoint Guard"
echo "=========================================="
echo ""

# Check Procfile
if [ -f "$BACKEND_DIR/Procfile" ]; then
    echo "Checking Procfile..."
    if grep -q "server/src\|server\.src\|server/main_simple" "$BACKEND_DIR/Procfile"; then
        error "Procfile references legacy code path (server/src/ or server/main_simple.py)"
        grep "server/src\|server\.src\|server/main_simple" "$BACKEND_DIR/Procfile" | sed 's/^/  /'
    elif grep -q "app\.main_simple:app\|app/main_simple" "$BACKEND_DIR/Procfile"; then
        success "Procfile uses correct entrypoint (app.main_simple:app)"
    else
        error "Procfile does not reference app.main_simple:app"
    fi
else
    error "Procfile not found"
fi
echo ""

# Check Dockerfile
if [ -f "$BACKEND_DIR/Dockerfile" ]; then
    echo "Checking Dockerfile..."
    if grep -q "server/src\|server\.src\|server/main_simple" "$BACKEND_DIR/Dockerfile"; then
        error "Dockerfile references legacy code path (server/src/ or server/main_simple.py)"
        grep "server/src\|server\.src\|server/main_simple" "$BACKEND_DIR/Dockerfile" | sed 's/^/  /'
    elif grep -q "app\.main_simple:app\|app/main_simple" "$BACKEND_DIR/Dockerfile"; then
        success "Dockerfile uses correct entrypoint (app.main_simple:app)"
    else
        warning "Dockerfile does not explicitly reference app.main_simple:app (may be set elsewhere)"
    fi
else
    warning "Dockerfile not found (may not be using Docker)"
fi
echo ""

# Check for imports of server/src in app/ directory
echo "Checking for imports of server/src in app/ directory..."
if grep -r "from server\|import server\|server/src\|server\.src" "$BACKEND_DIR/app" --include="*.py" 2>/dev/null | grep -v "__pycache__" | grep -v ".pyc"; then
    error "Found imports of server/src in app/ directory"
    grep -r "from server\|import server\|server/src\|server\.src" "$BACKEND_DIR/app" --include="*.py" 2>/dev/null | grep -v "__pycache__" | grep -v ".pyc" | sed 's/^/  /'
else
    success "No imports of server/src found in app/ directory"
fi
echo ""

# Check deployment scripts
echo "Checking deployment scripts..."
DEPLOYMENT_SCRIPTS=(
    "$REPO_ROOT/scripts/deploy.sh"
    "$REPO_ROOT/scripts/start.sh"
    "$BACKEND_DIR/scripts/start.sh"
    "$BACKEND_DIR/scripts/deploy.sh"
)

for script in "${DEPLOYMENT_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if grep -q "server/src\|server\.src\|server/main_simple" "$script"; then
            error "Deployment script $script references legacy code path"
            grep "server/src\|server\.src\|server/main_simple" "$script" | sed 's/^/  /'
        fi
    fi
done
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}All checks passed - no legacy code paths detected in deployment configs${NC}"
    exit 0
else
    echo -e "${RED}Found $ERRORS error(s) - legacy code paths detected in deployment configs${NC}"
    echo ""
    echo "CRITICAL: Legacy code (server/src/) contains dangerous bypass logic and must not be deployed."
    echo "Ensure all deployment configurations use app.main_simple:app as the entrypoint."
    exit 1
fi













