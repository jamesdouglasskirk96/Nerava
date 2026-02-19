#!/bin/bash
# Kill processes on ports 8001 and 5173

echo "🛑 Killing processes on ports 8001 and 5173..."

# Kill port 8001
if lsof -ti:8001 > /dev/null 2>&1; then
    echo "  Killing process on port 8001..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null
    sleep 1
    echo "  ✅ Port 8001 freed"
else
    echo "  ℹ️  Port 8001 is already free"
fi

# Kill port 5173
if lsof -ti:5173 > /dev/null 2>&1; then
    echo "  Killing process on port 5173..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null
    sleep 1
    echo "  ✅ Port 5173 freed"
else
    echo "  ℹ️  Port 5173 is already free"
fi

# Kill any remaining processes
pkill -f "uvicorn app.main" 2>/dev/null && echo "  ✅ Killed uvicorn processes" || true
pkill -f "vite" 2>/dev/null && echo "  ✅ Killed vite processes" || true

echo ""
echo "✅ All ports cleared. You can now start the servers."






