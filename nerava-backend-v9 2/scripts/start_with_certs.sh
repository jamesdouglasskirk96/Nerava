#!/bin/bash
# Start server with certificates from Nerava directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
NERAVA_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
cd "$BACKEND_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔐 Starting server with Apple Wallet signing${NC}"
echo ""

# Certificate paths
WWDR_PATH="$NERAVA_DIR/wallet-pass/wwdr.pem"
CERT_PATH="$NERAVA_DIR/pass.cer"
KEY_PATH="$NERAVA_DIR/nerava.key"

# Check if files exist
if [ ! -f "$WWDR_PATH" ]; then
    echo -e "${RED}❌ WWDR certificate not found: $WWDR_PATH${NC}"
    exit 1
fi

if [ ! -f "$CERT_PATH" ]; then
    echo -e "${RED}❌ Certificate not found: $CERT_PATH${NC}"
    exit 1
fi

if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}❌ Key not found: $KEY_PATH${NC}"
    exit 1
fi

# Convert certificate if needed (check if it's DER format)
if file "$CERT_PATH" | grep -q "DER"; then
    echo -e "${YELLOW}Converting certificate from DER to PEM...${NC}"
    CERT_PEM="$BACKEND_DIR/certs/pass.pem"
    mkdir -p "$BACKEND_DIR/certs"
    openssl x509 -inform DER -in "$CERT_PATH" -out "$CERT_PEM" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Could not convert, trying PEM format...${NC}"
        CERT_PEM="$CERT_PATH"
    }
else
    CERT_PEM="$CERT_PATH"
fi

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); tunnels = data.get('tunnels', []); https_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None); print(https_tunnel['public_url'] if https_tunnel else '')" 2>/dev/null || echo "")

# Set environment variables
export APPLE_WALLET_SIGNING_ENABLED=true
export APPLE_WALLET_WWDR_CERT_PATH="$WWDR_PATH"
export APPLE_WALLET_CERT_PATH="$CERT_PEM"
export APPLE_WALLET_KEY_PATH="$KEY_PATH"
export APPLE_WALLET_PASS_TYPE_ID="pass.com.nerava.wallet"
export APPLE_WALLET_TEAM_ID="XQV9A76Z96"

if [ -n "$NGROK_URL" ]; then
    export PUBLIC_BASE_URL="$NGROK_URL"
    echo -e "${GREEN}✅ ngrok URL: $NGROK_URL${NC}"
else
    export PUBLIC_BASE_URL="http://localhost:8000"
    echo -e "${YELLOW}⚠️  ngrok not running${NC}"
fi

echo ""
echo -e "${GREEN}📋 Configuration:${NC}"
echo "   WWDR: $WWDR_PATH"
echo "   Cert: $CERT_PEM"
echo "   Key: $KEY_PATH"
echo "   Team ID: XQV9A76Z96"
echo "   Pass Type ID: pass.com.nerava.wallet"
echo ""

# Kill existing server
pkill -9 -f "uvicorn.*main_simple" 2>/dev/null || true
sleep 1

echo -e "${GREEN}🚀 Starting server...${NC}"
echo ""

# Start server
exec python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload

