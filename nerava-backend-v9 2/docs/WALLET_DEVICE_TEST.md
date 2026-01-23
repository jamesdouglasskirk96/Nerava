# Apple Wallet Pass Device Testing Guide

This guide explains how to test Apple Wallet pass installation on a real iPhone device using ngrok for HTTPS tunneling.

## Prerequisites

1. **Apple Developer Account** with:
   - Pass Type ID configured
   - Signing certificate (.pem or .p12)
   - WWDR intermediate certificate

2. **Local Development Setup**:
   - Backend server running locally
   - ngrok installed (`brew install ngrok` or download from https://ngrok.com)
   - iPhone with Safari browser

3. **Environment Variables**:
   ```bash
   export APPLE_WALLET_SIGNING_ENABLED=true
   export APPLE_WALLET_PASS_TYPE_ID="pass.com.nerava.wallet"
   export APPLE_WALLET_TEAM_ID="YOUR_TEAM_ID"
   export APPLE_WALLET_CERT_PATH="/path/to/cert.pem"
   export APPLE_WALLET_KEY_PATH="/path/to/key.pem"
   export APPLE_WALLET_WWDR_CERT_PATH="/path/to/wwdr.pem"
   export PUBLIC_BASE_URL="https://your-ngrok-url.ngrok.io"
   ```

## Step-by-Step Testing Process

### 1. Start Local Backend Server

```bash
cd nerava-backend-v9
# Set up your environment variables
source .env  # or export them manually

# Start the server (adjust command based on your setup)
python -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000
```

The server should be running on `http://localhost:8000`.

### 2. Expose Server via ngrok HTTPS

In a separate terminal:

```bash
# Start ngrok tunnel
ngrok http 8000
```

ngrok will display output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

**Important**: Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`).

### 3. Update Environment Variable

Set `PUBLIC_BASE_URL` to your ngrok URL:

```bash
export PUBLIC_BASE_URL="https://abc123.ngrok.io"
```

Restart your backend server so it picks up the new `PUBLIC_BASE_URL`.

### 4. Verify Pass Endpoint

Test that the pass endpoint is accessible:

```bash
# Replace with your actual user auth token
curl -X POST https://abc123.ngrok.io/v1/wallet/pass/apple/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  --output test.pkpass
```

Verify the response:
- Content-Type should be `application/vnd.apple.pkpass`
- File should be a valid ZIP (`.pkpass`)

### 5. Open Pass URL in iPhone Safari

On your iPhone:

1. **Open Safari** (not Chrome or other browsers - Safari is required for Apple Wallet)

2. **Navigate to the pass creation endpoint**:
   ```
   https://abc123.ngrok.io/v1/wallet/pass/apple/create
   ```
   
   **Note**: You'll need to authenticate. Options:
   - Use a magic link/login flow first
   - Or use a test endpoint that doesn't require auth (for testing only)

3. **Safari should detect the `.pkpass` file** and show an "Add to Apple Wallet" button

4. **Tap "Add"** to install the pass

### 6. Verify Pass Installation

After tapping "Add":

- ✅ **Success**: Pass appears in Apple Wallet app
- ❌ **Failure**: Error message appears

Common failure reasons:
- Invalid signature (check WWDR cert is included)
- Missing required assets (check icon.png, logo.png dimensions)
- Incorrect Content-Type header
- Certificate chain issues

## Troubleshooting

### Pass Doesn't Install

1. **Check Content-Type Header**:
   ```bash
   curl -I https://abc123.ngrok.io/v1/wallet/pass/apple/create \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
   Should show: `Content-Type: application/vnd.apple.pkpass`

2. **Validate Signature**:
   ```bash
   # Extract signature from pkpass
   unzip test.pkpass signature
   
   # Validate with OpenSSL
   openssl pkcs7 -inform DER -in signature -print_certs -text
   ```
   Should show both signer cert and WWDR cert.

3. **Check Pass Structure**:
   ```bash
   unzip -l test.pkpass
   ```
   Should include: `pass.json`, `manifest.json`, `signature`, `icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`

### ngrok URL Changes

If ngrok restarts, you'll get a new URL. Update `PUBLIC_BASE_URL` and restart the server.

### Certificate Issues

- Ensure WWDR certificate is downloaded from: https://www.apple.com/certificateauthority/
- Verify certificate paths are correct
- Check certificate expiration dates

## Testing Checklist

- [ ] Backend server running locally
- [ ] ngrok tunnel active (HTTPS URL)
- [ ] `PUBLIC_BASE_URL` set to ngrok URL
- [ ] Environment variables configured (cert paths, team ID, pass type ID)
- [ ] Pass endpoint returns `.pkpass` file
- [ ] Content-Type header is `application/vnd.apple.pkpass`
- [ ] Pass installs successfully in iPhone Wallet app
- [ ] Pass displays correctly (balance, tier, status)
- [ ] Pass updates work (if web service is configured)

## Quick Test Commands

```bash
# Generate pkpass locally (for testing structure)
python nerava-backend-v9/scripts/wallet_build_gate.py

# Check pkpass contents
unzip -l test.pkpass

# Validate signature
unzip -p test.pkpass signature | openssl pkcs7 -inform DER -print_certs -text

# Test endpoint (replace with your auth)
curl -X POST https://YOUR_NGROK_URL/v1/wallet/pass/apple/create \
  -H "Authorization: Bearer TOKEN" \
  --output test.pkpass
```

## Notes

- **HTTPS Required**: Apple Wallet requires HTTPS. ngrok provides this automatically.
- **Safari Only**: Pass installation only works in Safari on iOS (not Chrome, Firefox, etc.)
- **Real Device**: Simulator may not fully support Wallet pass installation. Use a real iPhone.
- **Certificate Validity**: Ensure your signing certificate hasn't expired.

## Next Steps

After successful device testing:
1. Verify pass updates work (if PassKit web service is configured)
2. Test push notifications (if APNs is configured)
3. Validate pass refresh flow
4. Test pass uninstallation

