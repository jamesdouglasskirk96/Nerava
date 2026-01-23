#!/bin/bash
# Start backend server with ngrok tunnel for Apple Wallet testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Nerava Backend with ngrok for Apple Wallet Testing${NC}"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok is not installed${NC}"
    echo "Install with: brew install ngrok"
    echo "Or download from: https://ngrok.com/download"
    exit 1
fi

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use${NC}"
    echo "Please stop the process using port 8000 or use a different port"
    exit 1
fi

# Start ngrok in background
echo -e "${GREEN}📡 Starting ngrok tunnel on port 8000...${NC}"
ngrok http 8000 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}❌ Failed to get ngrok URL${NC}"
    echo "Check ngrok status: curl http://localhost:4040/api/tunnels"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ ngrok tunnel active: ${NGROK_URL}${NC}"
echo ""

# Set PUBLIC_BASE_URL
export PUBLIC_BASE_URL="$NGROK_URL"
echo -e "${GREEN}🔧 Set PUBLIC_BASE_URL=${NGROK_URL}${NC}"
echo ""

# Check for required Apple Wallet environment variables
echo -e "${YELLOW}📋 Checking Apple Wallet configuration...${NC}"

MISSING_VARS=()

if [ -z "$APPLE_WALLET_SIGNING_ENABLED" ] || [ "$APPLE_WALLET_SIGNING_ENABLED" != "true" ]; then
    echo -e "${YELLOW}  ⚠️  APPLE_WALLET_SIGNING_ENABLED is not set to 'true'${NC}"
    echo -e "${YELLOW}     Pass generation will be unsigned (for testing only)${NC}"
fi

if [ -z "$APPLE_WALLET_WWDR_CERT_PATH" ]; then
    MISSING_VARS+=("APPLE_WALLET_WWDR_CERT_PATH")
fi

if [ -z "$APPLE_WALLET_CERT_P12_PATH" ] && [ -z "$APPLE_WALLET_CERT_PATH" ]; then
    MISSING_VARS+=("APPLE_WALLET_CERT_P12_PATH or APPLE_WALLET_CERT_PATH + APPLE_WALLET_KEY_PATH")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${YELLOW}  ⚠️  Missing environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "${YELLOW}     - $var${NC}"
    done
    echo ""
    echo -e "${YELLOW}  For unsigned testing, this is OK.${NC}"
    echo -e "${YELLOW}  For signed passes, set these variables before running.${NC}"
    echo ""
fi

# Display iPhone Safari URL
echo -e "${GREEN}📱 iPhone Safari URL:${NC}"
echo -e "${GREEN}   ${NGROK_URL}/v1/wallet/pass/apple/create${NC}"
echo ""
echo -e "${YELLOW}⚠️  Note: You'll need to authenticate first.${NC}"
echo -e "${YELLOW}   Options:${NC}"
echo -e "${YELLOW}   1. Use a test endpoint that doesn't require auth${NC}"
echo -e "${YELLOW}   2. Log in via web first, then use the pass endpoint${NC}"
echo -e "${YELLOW}   3. Use a magic link/login flow${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down...${NC}"
    kill $NGROK_PID 2>/dev/null || true
    kill $SERVER_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "${GREEN}🚀 Starting backend server...${NC}"
echo ""

cd "$BACKEND_DIR"
python -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

echo -e "${GREEN}✅ Backend server started (PID: $SERVER_PID)${NC}"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo -e "${GREEN}Backend URL:    http://localhost:8000${NC}"
echo -e "${GREEN}ngrok URL:      ${NGROK_URL}${NC}"
echo -e "${GREEN}Public Base:    ${PUBLIC_BASE_URL}${NC}"
echo ""
echo -e "${GREEN}📱 Test on iPhone Safari:${NC}"
echo -e "${GREEN}   ${NGROK_URL}/v1/wallet/pass/apple/create${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop both ngrok and the server${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Wait for server to be ready
sleep 2

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${RED}❌ Server failed to start${NC}"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

# Wait for both processes
wait $SERVER_PID $NGROK_PID

