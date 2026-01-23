#!/bin/bash
# Start server with Apple Wallet signing using certificates from Nerava directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
NERAVA_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
cd "$BACKEND_DIR"

# Kill existing server
pkill -9 -f "uvicorn.*main_simple" 2>/dev/null || true
sleep 2

# Convert certificate if needed
if [ -f "$NERAVA_DIR/pass.cer" ]; then
    # Check if it's DER format
    if ! head -1 "$NERAVA_DIR/pass.cer" | grep -q "BEGIN CERTIFICATE"; then
        echo "Converting certificate from DER to PEM..."
        openssl x509 -inform DER -in "$NERAVA_DIR/pass.cer" -out /tmp/pass.pem 2>/dev/null || {
            echo "Warning: Could not convert certificate, using original"
            CERT_PATH="$NERAVA_DIR/pass.cer"
        }
        CERT_PATH="/tmp/pass.pem"
    else
        CERT_PATH="$NERAVA_DIR/pass.cer"
    fi
else
    echo "Error: Certificate not found at $NERAVA_DIR/pass.cer"
    exit 1
fi

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); tunnels = data.get('tunnels', []); https_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None); print(https_tunnel['public_url'] if https_tunnel else '')" 2>/dev/null || echo "")

# Set environment variables
export APPLE_WALLET_SIGNING_ENABLED=true
export APPLE_WALLET_WWDR_CERT_PATH="$NERAVA_DIR/wallet-pass/wwdr.pem"
export APPLE_WALLET_CERT_PATH="$CERT_PATH"
export APPLE_WALLET_KEY_PATH="$NERAVA_DIR/nerava.key"
export APPLE_WALLET_PASS_TYPE_ID="pass.com.nerava.prototype"
export APPLE_WALLET_TEAM_ID="XQV9A76Z96"

if [ -n "$NGROK_URL" ]; then
    export PUBLIC_BASE_URL="$NGROK_URL"
else
    export PUBLIC_BASE_URL="http://localhost:8000"
fi

# Verify files exist
if [ ! -f "$APPLE_WALLET_WWDR_CERT_PATH" ]; then
    echo "Error: WWDR certificate not found: $APPLE_WALLET_WWDR_CERT_PATH"
    exit 1
fi

if [ ! -f "$APPLE_WALLET_CERT_PATH" ]; then
    echo "Error: Certificate not found: $APPLE_WALLET_CERT_PATH"
    exit 1
fi

if [ ! -f "$APPLE_WALLET_KEY_PATH" ]; then
    echo "Error: Key not found: $APPLE_WALLET_KEY_PATH"
    exit 1
fi

echo "✅ Configuration:"
echo "   APPLE_WALLET_SIGNING_ENABLED=$APPLE_WALLET_SIGNING_ENABLED"
echo "   APPLE_WALLET_WWDR_CERT_PATH=$APPLE_WALLET_WWDR_CERT_PATH"
echo "   APPLE_WALLET_CERT_PATH=$APPLE_WALLET_CERT_PATH"
echo "   APPLE_WALLET_KEY_PATH=$APPLE_WALLET_KEY_PATH"
echo "   PUBLIC_BASE_URL=$PUBLIC_BASE_URL"
echo ""
echo "🚀 Starting server..."

# Start server
exec python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload

