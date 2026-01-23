#!/bin/bash
# Test Apple Wallet pass endpoint (for quick testing without iPhone)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🧪 Testing Apple Wallet Pass Endpoint${NC}"
echo ""

# Get ngrok URL if available
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$NGROK_URL" ]; then
    BASE_URL="http://localhost:8000"
    echo -e "${YELLOW}⚠️  ngrok not detected, using localhost${NC}"
else
    BASE_URL="$NGROK_URL"
    echo -e "${GREEN}✅ Using ngrok URL: ${NGROK_URL}${NC}"
fi

echo ""
echo -e "${YELLOW}Note: This endpoint requires authentication.${NC}"
echo -e "${YELLOW}You'll need to provide a valid auth token.${NC}"
echo ""

# Check if token is provided
if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${YELLOW}Set AUTH_TOKEN environment variable to test:${NC}"
    echo -e "${YELLOW}  export AUTH_TOKEN='your-token-here'${NC}"
    echo -e "${YELLOW}  $0${NC}"
    echo ""
    echo -e "${YELLOW}Or test the endpoint manually:${NC}"
    echo -e "${GREEN}  curl -X POST ${BASE_URL}/v1/wallet/pass/apple/create \\${NC}"
    echo -e "${GREEN}    -H \"Authorization: Bearer YOUR_TOKEN\" \\${NC}"
    echo -e "${GREEN}    --output test.pkpass${NC}"
    echo ""
    exit 0
fi

# Test endpoint
echo -e "${GREEN}📦 Requesting pkpass...${NC}"
OUTPUT_FILE="test.pkpass"

HTTP_CODE=$(curl -s -o "$OUTPUT_FILE" -w "%{http_code}" \
    -X POST "${BASE_URL}/v1/wallet/pass/apple/create" \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -H "Content-Type: application/json")

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Success! pkpass saved to ${OUTPUT_FILE}${NC}"
    echo ""
    
    # Check file type
    FILE_TYPE=$(file -b "$OUTPUT_FILE")
    echo -e "${GREEN}File type: ${FILE_TYPE}${NC}"
    
    # Check if it's a ZIP
    if [[ "$FILE_TYPE" == *"Zip"* ]] || [[ "$FILE_TYPE" == *"ZIP"* ]]; then
        echo -e "${GREEN}✅ Valid ZIP file${NC}"
        
        # List contents
        echo ""
        echo -e "${GREEN}📋 Contents:${NC}"
        unzip -l "$OUTPUT_FILE" | head -20
        
        # Check for signature
        if unzip -l "$OUTPUT_FILE" | grep -q "signature"; then
            echo ""
            echo -e "${GREEN}✅ Signature file found${NC}"
            
            # Extract and validate signature
            echo ""
            echo -e "${GREEN}🔐 Validating signature...${NC}"
            unzip -p "$OUTPUT_FILE" signature > /tmp/signature.der 2>/dev/null
            
            if command -v openssl &> /dev/null; then
                openssl pkcs7 -inform DER -in /tmp/signature.der -print_certs -text 2>/dev/null | head -30 || echo -e "${YELLOW}⚠️  Could not parse signature (may be unsigned)${NC}"
                rm -f /tmp/signature.der
            else
                echo -e "${YELLOW}⚠️  OpenSSL not available for signature validation${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  No signature file (unsigned pass)${NC}"
        fi
    else
        echo -e "${RED}❌ Not a valid ZIP file${NC}"
        echo "Response:"
        head -20 "$OUTPUT_FILE"
    fi
else
    echo -e "${RED}❌ Request failed with HTTP ${HTTP_CODE}${NC}"
    echo ""
    echo "Response:"
    cat "$OUTPUT_FILE"
    rm -f "$OUTPUT_FILE"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Test complete!${NC}"
echo -e "${GREEN}📱 To test on iPhone, open Safari and navigate to:${NC}"
if [ -n "$NGROK_URL" ]; then
    echo -e "${GREEN}   ${NGROK_URL}/v1/wallet/pass/apple/create${NC}"
else
    echo -e "${YELLOW}   (Start ngrok first, then use the ngrok HTTPS URL)${NC}"
fi

