#!/bin/bash
# Stop local development servers for Nerava

set -e

echo "🛑 Stopping Nerava development servers..."

echo "  Stopping backend (port 8001)..."
lsof -ti:8001 | xargs kill -9 2>/dev/null && echo "    ✓ Backend stopped" || echo "    ℹ️  No process on port 8001"

echo "  Stopping driver app (port 5173)..."
lsof -ti:5173 | xargs kill -9 2>/dev/null && echo "    ✓ Driver app stopped" || echo "    ℹ️  No process on port 5173"

echo "  Stopping any remaining uvicorn processes..."
pkill -f "uvicorn app.main" 2>/dev/null && echo "    ✓ Uvicorn processes stopped" || echo "    ℹ️  No uvicorn processes found"

echo "  Stopping any remaining vite processes..."
pkill -f "vite" 2>/dev/null && echo "    ✓ Vite processes stopped" || echo "    ℹ️  No vite processes found"

sleep 1
echo ""
echo "✅ All servers stopped"






