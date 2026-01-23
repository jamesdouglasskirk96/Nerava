#!/bin/bash
# Smoke test script for Docker Compose deployment
# Validates all health endpoints are accessible

set -e

BASE_URL="http://localhost"
MAX_WAIT=60
WAIT_INTERVAL=2

echo "🔍 Waiting for services to be healthy (max ${MAX_WAIT}s)..."

# Wait for services to be ready
elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
    if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
        echo "✅ Proxy is ready"
        break
    fi
    echo "⏳ Waiting for services... (${elapsed}s/${MAX_WAIT}s)"
    sleep $WAIT_INTERVAL
    elapsed=$((elapsed + WAIT_INTERVAL))
done

if [ $elapsed -ge $MAX_WAIT ]; then
    echo "❌ Timeout waiting for services to be ready"
    exit 1
fi

echo ""
echo "🧪 Running health checks..."
echo ""

# Test endpoints
ENDPOINTS=(
    "${BASE_URL}/health:Proxy"
    "${BASE_URL}/api/health:Backend"
    "${BASE_URL}/landing/health:Landing"
    "${BASE_URL}/app/health:Driver"
    "${BASE_URL}/merchant/health:Merchant"
    "${BASE_URL}/admin/health:Admin"
)

FAILED=0

for endpoint_info in "${ENDPOINTS[@]}"; do
    IFS=':' read -r endpoint name <<< "$endpoint_info"
    if curl -sf "$endpoint" > /dev/null 2>&1; then
        echo "✅ $name: $endpoint"
    else
        echo "❌ $name: $endpoint (FAILED)"
        FAILED=1
    fi
done

echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All health checks passed!"
    exit 0
else
    echo "💥 Some health checks failed"
    exit 1
fi

