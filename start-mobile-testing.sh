#!/bin/bash

echo "🚀 Starting Nerava Mobile Testing Environment"
echo "============================================="

# Get local IP
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "192.168.1.70")
PORT=5173
URL="http://$IP:$PORT"

echo "📱 Local IP: $IP"
echo "🌐 URL: $URL"
echo ""

# Start UI server in background
echo "Starting UI server on port $PORT..."
npx http-server ./ui-mobile -p $PORT -a 0.0.0.0 &
UI_PID=$!

# Start backend server in background
echo "Starting backend server on port 8001..."
cd nerava-backend-v9/server
python -m uvicorn main_simple:app --port 8001 --host 0.0.0.0 &
BACKEND_PID=$!
cd ../..

# Wait a moment for servers to start
sleep 3

# Show QR code
echo ""
echo "📱 Scan this QR code on your phone:"
echo "====================================="
cd ui-mobile
node show-mobile-access.js $PORT
cd ..

echo ""
echo "✅ Both servers are running!"
echo "   UI: http://$IP:$PORT"
echo "   API: http://$IP:8001"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $UI_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
