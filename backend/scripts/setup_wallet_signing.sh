#!/bin/bash
# Setup Apple Wallet signing configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CERTS_DIR="$BACKEND_DIR/certs"
cd "$BACKEND_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔐 Apple Wallet Signing Setup${NC}"
echo ""

# Create certs directory
mkdir -p "$CERTS_DIR"

# Download WWDR certificate
WWDR_URL="https://www.apple.com/certificateauthority/AppleWWDRCAG4.cer"
WWDR_PATH="$CERTS_DIR/wwdr.pem"

echo -e "${GREEN}📥 Downloading WWDR certificate...${NC}"
if [ ! -f "$WWDR_PATH" ]; then
    curl -s "$WWDR_URL" -o "$CERTS_DIR/wwdr.cer" || {
        echo -e "${RED}❌ Failed to download WWDR certificate${NC}"
        echo "Please download manually from: https://www.apple.com/certificateauthority/"
        echo "Save as: $WWDR_PATH"
        exit 1
    }
    
    # Convert .cer to .pem
    openssl x509 -inform DER -in "$CERTS_DIR/wwdr.cer" -out "$WWDR_PATH" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Could not convert WWDR cert, using .cer file${NC}"
        WWDR_PATH="$CERTS_DIR/wwdr.cer"
    }
    echo -e "${GREEN}✅ WWDR certificate saved to: $WWDR_PATH${NC}"
else
    echo -e "${GREEN}✅ WWDR certificate already exists: $WWDR_PATH${NC}"
fi

echo ""

# Check for existing certificates
echo -e "${YELLOW}📋 Certificate Configuration:${NC}"
echo ""

# Check for P12 file
P12_FOUND=$(find ~/Downloads ~/Desktop -name "*.p12" -type f 2>/dev/null | head -1)
if [ -n "$P12_FOUND" ]; then
    echo -e "${GREEN}✅ Found P12 certificate: $P12_FOUND${NC}"
    P12_PATH="$P12_FOUND"
else
    echo -e "${YELLOW}⚠️  No P12 certificate found${NC}"
    P12_PATH=""
fi

# Check for PEM cert/key
CERT_FOUND=$(find ~/Downloads ~/Desktop -name "*.pem" -type f 2>/dev/null | grep -i cert | head -1)
KEY_FOUND=$(find ~/Downloads ~/Desktop -name "*.pem" -type f 2>/dev/null | grep -i key | head -1)

if [ -n "$CERT_FOUND" ] && [ -n "$KEY_FOUND" ]; then
    echo -e "${GREEN}✅ Found PEM certificate: $CERT_FOUND${NC}"
    echo -e "${GREEN}✅ Found PEM key: $KEY_FOUND${NC}"
    CERT_PATH="$CERT_FOUND"
    KEY_PATH="$KEY_FOUND"
else
    echo -e "${YELLOW}⚠️  No PEM certificate/key found${NC}"
    CERT_PATH=""
    KEY_PATH=""
fi

echo ""

# Prompt for configuration
if [ -z "$P12_PATH" ] && [ -z "$CERT_PATH" ]; then
    echo -e "${RED}❌ No signing certificates found!${NC}"
    echo ""
    echo "To enable signing, you need:"
    echo "1. Apple Developer Pass Type ID certificate (.p12 or .pem + .key)"
    echo "2. Download from: https://developer.apple.com/account/resources/identifiers/list/passTypeId"
    echo ""
    echo "For now, signing will remain disabled."
    echo "Set these environment variables when you have certificates:"
    echo "  export APPLE_WALLET_SIGNING_ENABLED=true"
    echo "  export APPLE_WALLET_CERT_P12_PATH=/path/to/cert.p12"
    echo "  export APPLE_WALLET_WWDR_CERT_PATH=$WWDR_PATH"
    echo "  export APPLE_WALLET_PASS_TYPE_ID=pass.com.nerava.wallet"
    echo "  export APPLE_WALLET_TEAM_ID=YOUR_TEAM_ID"
    exit 0
fi

# Generate environment setup
ENV_SETUP="$CERTS_DIR/env_setup.sh"
cat > "$ENV_SETUP" << EOF
# Apple Wallet Signing Configuration
# Source this file before starting the server: source certs/env_setup.sh

export APPLE_WALLET_SIGNING_ENABLED=true
export APPLE_WALLET_WWDR_CERT_PATH="$WWDR_PATH"
EOF

if [ -n "$P12_PATH" ]; then
    echo "export APPLE_WALLET_CERT_P12_PATH=\"$P12_PATH\"" >> "$ENV_SETUP"
    echo "export APPLE_WALLET_CERT_P12_PASSWORD=\"\"" >> "$ENV_SETUP"
    echo -e "${GREEN}✅ Using P12 certificate: $P12_PATH${NC}"
elif [ -n "$CERT_PATH" ] && [ -n "$KEY_PATH" ]; then
    echo "export APPLE_WALLET_CERT_PATH=\"$CERT_PATH\"" >> "$ENV_SETUP"
    echo "export APPLE_WALLET_KEY_PATH=\"$KEY_PATH\"" >> "$ENV_SETUP"
    echo "export APPLE_WALLET_KEY_PASSWORD=\"\"" >> "$ENV_SETUP"
    echo -e "${GREEN}✅ Using PEM certificate: $CERT_PATH${NC}"
    echo -e "${GREEN}✅ Using PEM key: $KEY_PATH${NC}"
fi

echo "" >> "$ENV_SETUP"
echo "# Required Apple Developer settings" >> "$ENV_SETUP"
echo "export APPLE_WALLET_PASS_TYPE_ID=\"pass.com.nerava.wallet\"" >> "$ENV_SETUP"
echo "export APPLE_WALLET_TEAM_ID=\"YOUR_TEAM_ID\"" >> "$ENV_SETUP"

chmod +x "$ENV_SETUP"

echo ""
echo -e "${GREEN}✅ Configuration file created: $ENV_SETUP${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Edit $ENV_SETUP and set:${NC}"
echo -e "${YELLOW}   - APPLE_WALLET_PASS_TYPE_ID (your Pass Type ID)${NC}"
echo -e "${YELLOW}   - APPLE_WALLET_TEAM_ID (your Apple Developer Team ID)${NC}"
echo -e "${YELLOW}   - APPLE_WALLET_CERT_P12_PASSWORD (if your P12 is password-protected)${NC}"
echo ""
echo -e "${GREEN}To enable signing, run:${NC}"
echo -e "${GREEN}  source $ENV_SETUP${NC}"
echo -e "${GREEN}  # Then restart your server${NC}"

