#!/bin/bash
# Apple Wallet Pass Builder
# Generates a signed .pkpass file from pass.json and assets

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

WALLET_PASS_DIR="$SCRIPT_DIR"
BUILD_DIR="$WALLET_PASS_DIR/build"
DIST_DIR="$WALLET_PASS_DIR/dist"
ASSETS_DIR="$WALLET_PASS_DIR/assets"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
    exit 1
}

info() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Validate required files exist
info "Validating required files..."

if [[ ! -f "./nerava.key" ]]; then
    error "Missing ./nerava.key - private key file required for signing"
fi

if [[ ! -f "./pass.cer" ]]; then
    error "Missing ./pass.cer - certificate file required for signing"
fi

if [[ ! -f "$ASSETS_DIR/logo.png" ]]; then
    error "Missing $ASSETS_DIR/logo.png - logo image required"
fi

if [[ ! -f "$ASSETS_DIR/icon.png" ]]; then
    error "Missing $ASSETS_DIR/icon.png - icon image required"
fi

if [[ ! -f "$WALLET_PASS_DIR/pass.json" ]]; then
    error "Missing $WALLET_PASS_DIR/pass.json - pass definition required"
fi

info "All required files found"

# Clean and create directories
info "Preparing build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"

# Copy files to build directory
info "Copying pass files..."
cp "$WALLET_PASS_DIR/pass.json" "$BUILD_DIR/"
cp "$ASSETS_DIR/logo.png" "$BUILD_DIR/"
cp "$ASSETS_DIR/icon.png" "$BUILD_DIR/"

# Generate retina (@2x) image variants using sips
info "Generating retina image variants..."
if ! command -v sips &> /dev/null; then
    error "sips command not found. sips is required to generate retina images. Install Xcode Command Line Tools: xcode-select --install"
fi

cd "$BUILD_DIR"
# Generate icon@2x.png (58x58 = 2x of 29x29)
sips -z 58 58 icon.png --out icon@2x.png || error "Failed to generate icon@2x.png"

# Generate logo@2x.png (640x220 = 2x of 320x110, or detect original size)
# Get original logo dimensions
LOGO_WIDTH=$(sips -g pixelWidth logo.png | awk '/pixelWidth:/ {print $2}')
LOGO_HEIGHT=$(sips -g pixelHeight logo.png | awk '/pixelHeight:/ {print $2}')
LOGO_WIDTH_2X=$((LOGO_WIDTH * 2))
LOGO_HEIGHT_2X=$((LOGO_HEIGHT * 2))
# sips -z takes height then width
sips -z "$LOGO_HEIGHT_2X" "$LOGO_WIDTH_2X" logo.png --out logo@2x.png || error "Failed to generate logo@2x.png"

# Generate manifest.json with SHA1 hashes
# Hash ALL files in build/ EXCEPT signature (which is created after manifest)
# Files to hash: pass.json, icon.png, icon@2x.png, logo.png, logo@2x.png
info "Generating manifest.json..."
manifest_content=""
for file in pass.json icon.png icon@2x.png logo.png logo@2x.png; do
    if [[ -f "$file" ]]; then
        hash=$(shasum -a 1 "$file" | awk '{print $1}')
        if [[ -z "$manifest_content" ]]; then
            manifest_content="  \"$file\": \"$hash\""
        else
            manifest_content="$manifest_content,\n  \"$file\": \"$hash\""
        fi
    fi
done
echo -e "{\n$manifest_content\n}" > manifest.json

# Convert certificate to PEM if needed (in temp directory outside build/)
info "Preparing certificate..."
TEMP_DIR=$(mktemp -d)
trap "rm -rf '$TEMP_DIR'" EXIT
CERT_PEM="$TEMP_DIR/pass.pem"
if file "$REPO_ROOT/pass.cer" | grep -q "DER\|Binary"; then
    openssl x509 -inform DER -in "$REPO_ROOT/pass.cer" -out "$CERT_PEM" 2>/dev/null || {
        # Try as PEM if DER conversion fails
        cp "$REPO_ROOT/pass.cer" "$CERT_PEM"
    }
else
    cp "$REPO_ROOT/pass.cer" "$CERT_PEM"
fi

# Check for WWDR certificate
WWDR_CERT="$WALLET_PASS_DIR/wwdr.pem"
if [[ -f "$WWDR_CERT" ]]; then
    info "Found WWDR certificate, including in signature..."
    HAS_WWDR=1
else
    warn "WWDR certificate not found at $WWDR_CERT"
    warn "Pass may not install on iPhone. Place WWDR cert at wallet-pass/wwdr.pem"
    HAS_WWDR=0
fi

# Sign manifest.json
info "Signing manifest..."
cd "$BUILD_DIR"
if [[ $HAS_WWDR -eq 1 ]]; then
    openssl smime -binary -sign \
        -signer "$CERT_PEM" \
        -certfile "$WWDR_CERT" \
        -inkey "$REPO_ROOT/nerava.key" \
        -in manifest.json \
        -out signature \
        -outform DER \
        -nodetach \
        -noattr || error "Failed to sign manifest. Check certificate and key files."
else
    openssl smime -binary -sign \
        -signer "$CERT_PEM" \
        -inkey "$REPO_ROOT/nerava.key" \
        -in manifest.json \
        -out signature \
        -outform DER \
        -nodetach \
        -noattr || error "Failed to sign manifest. Check certificate and key files."
fi

# Create ZIP archive with only required files
info "Creating .pkpass archive..."
cd "$BUILD_DIR"
zip -q "$DIST_DIR/nerava.pkpass" pass.json icon.png icon@2x.png logo.png logo@2x.png manifest.json signature || error "Failed to create ZIP archive"

info "Build complete!"
info "Output: $DIST_DIR/nerava.pkpass"
info ""
info "To install:"
info "  1. AirDrop $DIST_DIR/nerava.pkpass to your iPhone"
info "  2. Tap the file on your iPhone"
info "  3. Tap 'Add' to add to Wallet"

