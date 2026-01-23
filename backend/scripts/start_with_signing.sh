#!/bin/bash
# Start server with Apple Wallet signing enabled (if certificates are available)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting server with Apple Wallet signing${NC}"
echo ""

# Check for WWDR certificate
WWDR_PATH=""
if [ -f "certs/wwdr.pem" ]; then
    WWDR_PATH="certs/wwdr.pem"
elif [ -f "certs/wwdr.cer" ]; then
    WWDR_PATH="certs/wwdr.cer"
fi

if [ -z "$WWDR_PATH" ]; then
    echo -e "${YELLOW}⚠️  WWDR certificate not found. Downloading...${NC}"
    python3 scripts/download_wwdr.py || {
        echo -e "${RED}❌ Failed to download WWDR certificate${NC}"
        echo "Please download manually and place in certs/ directory"
        exit 1
    }
    WWDR_PATH="certs/wwdr.pem"
    [ ! -f "$WWDR_PATH" ] && WWDR_PATH="certs/wwdr.cer"
fi

# Set environment variables
export APPLE_WALLET_SIGNING_ENABLED=true
export APPLE_WALLET_WWDR_CERT_PATH="$BACKEND_DIR/$WWDR_PATH"

# Check for signing certificates
P12_FOUND=$(find ~/Downloads ~/Desktop -maxdepth 2 -name "*.p12" -type f 2>/dev/null | head -1)
CERT_FOUND=$(find ~/Downloads ~/Desktop -maxdepth 2 -name "*.pem" -type f 2>/dev/null | grep -i cert | head -1)
KEY_FOUND=$(find ~/Downloads ~/Desktop -maxdepth 2 -name "*.pem" -type f 2>/dev/null | grep -i key | head -1)

if [ -n "$P12_FOUND" ]; then
    export APPLE_WALLET_CERT_P12_PATH="$P12_FOUND"
    echo -e "${GREEN}✅ Using P12 certificate: $P12_FOUND${NC}"
elif [ -n "$CERT_FOUND" ] && [ -n "$KEY_FOUND" ]; then
    export APPLE_WALLET_CERT_PATH="$CERT_FOUND"
    export APPLE_WALLET_KEY_PATH="$KEY_FOUND"
    echo -e "${GREEN}✅ Using PEM certificate: $CERT_FOUND${NC}"
    echo -e "${GREEN}✅ Using PEM key: $KEY_FOUND${NC}"
else
    echo -e "${YELLOW}⚠️  No signing certificate found${NC}"
    echo -e "${YELLOW}   Signing will fail, but endpoint will be accessible${NC}"
fi

# Set defaults (user should override these)
export APPLE_WALLET_PASS_TYPE_ID="${APPLE_WALLET_PASS_TYPE_ID:-pass.com.nerava.wallet}"
export APPLE_WALLET_TEAM_ID="${APPLE_WALLET_TEAM_ID:-}"

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); tunnels = data.get('tunnels', []); https_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None); print(https_tunnel['public_url'] if https_tunnel else '')" 2>/dev/null || echo "")

if [ -n "$NGROK_URL" ]; then
    export PUBLIC_BASE_URL="$NGROK_URL"
    echo -e "${GREEN}✅ ngrok URL: $NGROK_URL${NC}"
else
    export PUBLIC_BASE_URL="http://localhost:8000"
    echo -e "${YELLOW}⚠️  ngrok not running, using localhost${NC}"
fi

echo ""
echo -e "${GREEN}Starting server...${NC}"
echo ""

# Start server
exec python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload

