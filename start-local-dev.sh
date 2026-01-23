#!/bin/bash
# Start local development servers for Nerava
# This script starts the backend and driver app

set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🛑 Stopping any existing processes..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || echo "  ✓ Port 8001 is free"
lsof -ti:5173 | xargs kill -9 2>/dev/null || echo "  ✓ Port 5173 is free"
pkill -f "uvicorn app.main" 2>/dev/null || echo "  ✓ No uvicorn processes"
pkill -f "vite" 2>/dev/null || echo "  ✓ No vite processes"
sleep 2

echo ""
echo "🚀 Starting Backend Server (port 8001)..."
cd "$BASE_DIR/backend"
python3 -m uvicorn app.main:app --reload --port 8001 > /tmp/nerava-backend.log 2>&1 &
BACKEND_PID=$!
echo "  ✓ Backend started (PID: $BACKEND_PID)"
echo "  📝 Logs: tail -f /tmp/nerava-backend.log"

echo ""
echo "⏳ Waiting for backend to start..."
sleep 5

echo ""
echo "🧪 Testing backend health..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "  ✅ Backend is healthy"
else
    echo "  ⚠️  Backend may still be starting..."
fi

echo ""
echo "🧪 Testing primary merchant endpoint..."
curl -s "http://localhost:8001/v1/drivers/merchants/open?charger_id=canyon_ridge_tesla&state=pre-charge" \
  -H "Content-Type: application/json" 2>&1 | python3 -m json.tool 2>/dev/null || echo "  ⚠️  Endpoint may require authentication"

echo ""
echo "🚀 Starting Driver App (port 5173)..."
cd "$BASE_DIR"

if [ -f "apps/driver/package.json" ]; then
    cd apps/driver
    echo "  📁 Using: $(pwd)"
    npm run dev > /tmp/nerava-driver.log 2>&1 &
    DRIVER_PID=$!
    echo "  ✓ Driver app started (PID: $DRIVER_PID)"
    echo "  📝 Logs: tail -f /tmp/nerava-driver.log"
else
    echo "  ⚠️  Driver app not found at: $BASE_DIR/apps/driver"
    echo "  Please start manually: cd apps/driver && npm run dev"
    DRIVER_PID=""
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Access URLs:"
echo "  - Backend API: http://localhost:8001"
echo "  - Backend Health: http://localhost:8001/health"
echo "  - API Docs: http://localhost:8001/docs"
echo "  - Driver App: http://localhost:5173"
echo "  - Pre-Charge Screen: http://localhost:5173/pre-charging"
echo "  - Charging Screen: http://localhost:5173/wyc"
echo ""
if [ -n "$DRIVER_PID" ]; then
    echo "🛑 To stop servers:"
    echo "  kill $BACKEND_PID $DRIVER_PID"
    echo "  # Or: ./stop-local-dev.sh"
else
    echo "🛑 To stop backend:"
    echo "  kill $BACKEND_PID"
    echo "  # Or: ./stop-local-dev.sh"
fi
echo ""
echo "📊 View logs:"
echo "  tail -f /tmp/nerava-backend.log"
if [ -n "$DRIVER_PID" ]; then
    echo "  tail -f /tmp/nerava-driver.log"
fi
