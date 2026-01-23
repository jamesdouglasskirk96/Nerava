# Quick Start: Apple Wallet Pass Testing with ngrok

Complete step-by-step guide to test Apple Wallet pass installation on iPhone.

## Prerequisites

1. **ngrok installed**: `brew install ngrok` or download from https://ngrok.com
2. **Python dependencies installed**: `pip install -r requirements.txt`
3. **Database set up**: SQLite database should exist (created on first run)

## Option 1: Automated Script (Recommended)

The easiest way to start everything:

```bash
cd nerava-backend-v9
./scripts/start_with_ngrok.sh
```

This script will:
- ✅ Start ngrok tunnel on port 8000
- ✅ Get the ngrok HTTPS URL automatically
- ✅ Set `PUBLIC_BASE_URL` environment variable
- ✅ Start the backend server
- ✅ Display the iPhone Safari URL

**To stop**: Press `Ctrl+C` (stops both ngrok and server)

## Option 2: Manual Steps

### Step 1: Start ngrok

```bash
ngrok http 8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### Step 2: Set Environment Variables

```bash
export PUBLIC_BASE_URL="https://abc123.ngrok.io"  # Replace with your ngrok URL
```

**Optional** (for signed passes):
```bash
export APPLE_WALLET_SIGNING_ENABLED=true
export APPLE_WALLET_PASS_TYPE_ID="pass.com.nerava.wallet"
export APPLE_WALLET_TEAM_ID="YOUR_TEAM_ID"
export APPLE_WALLET_CERT_PATH="/path/to/cert.pem"
export APPLE_WALLET_KEY_PATH="/path/to/key.pem"
export APPLE_WALLET_WWDR_CERT_PATH="/path/to/wwdr.pem"
```

### Step 3: Start Backend Server

```bash
cd nerava-backend-v9
python -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000
```

### Step 4: Test on iPhone Safari

1. **Open Safari** on your iPhone (not Chrome or other browsers)
2. **Navigate to**: `https://YOUR_NGROK_URL/v1/wallet/pass/apple/create`
3. **Authenticate** (you'll need to log in first, or use a test endpoint)
4. **Tap "Add to Apple Wallet"** when prompted

## Testing Without iPhone (Quick Validation)

Test the endpoint locally to verify it works:

```bash
cd nerava-backend-v9

# Set your auth token
export AUTH_TOKEN="your-token-here"

# Run test script
./scripts/test_wallet_pass_endpoint.sh
```

Or manually:
```bash
curl -X POST https://YOUR_NGROK_URL/v1/wallet/pass/apple/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output test.pkpass

# Verify it's a valid ZIP
unzip -l test.pkpass
```

## Authentication Options

The pass endpoint requires authentication. Options:

### Option A: Use Test User (if enabled)
If `NERAVA_DEV_ALLOW_ANON_DRIVER=true` is set, you can test without auth.

### Option B: Get Auth Token
1. Log in via web interface: `https://YOUR_NGROK_URL/app/login`
2. Get auth token from browser dev tools (Network tab)
3. Use token in curl or Safari

### Option C: Create Test Endpoint
For testing only, you can temporarily modify the router to skip auth (not recommended for production).

## Troubleshooting

### ngrok URL Changes
If ngrok restarts, you'll get a new URL. Update `PUBLIC_BASE_URL` and restart the server.

### Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it or use a different port
kill -9 <PID>
```

### Pass Doesn't Install
1. **Check Content-Type**: Should be `application/vnd.apple.pkpass`
2. **Check Signature**: Run build gate: `python scripts/wallet_build_gate.py`
3. **Check Assets**: Ensure icon.png, logo.png exist with correct dimensions

### Signature Validation Fails
- Ensure `APPLE_WALLET_WWDR_CERT_PATH` is set
- Download WWDR cert from: https://www.apple.com/certificateauthority/
- Verify certificate paths are correct

## Expected Output

When everything works:

1. **Backend starts**: `INFO:     Uvicorn running on http://0.0.0.0:8000`
2. **ngrok shows**: `Forwarding https://abc123.ngrok.io -> http://localhost:8000`
3. **iPhone Safari**: Shows "Add to Apple Wallet" button
4. **Wallet app**: Pass appears with balance, tier, and status

## Next Steps

After successful installation:
- ✅ Verify pass displays correctly
- ✅ Test pass updates (if web service configured)
- ✅ Test push notifications (if APNs configured)
- ✅ Validate pass refresh flow

## Files Created

- `test.pkpass` - Generated pass file (for local testing)
- `WALLET_AUDIT_ARTIFACT_REPORT.md` - Build gate validation report

## Quick Reference

```bash
# Start everything (automated)
./scripts/start_with_ngrok.sh

# Test endpoint locally
export AUTH_TOKEN="your-token"
./scripts/test_wallet_pass_endpoint.sh

# Run build gate validation
python scripts/wallet_build_gate.py

# Check pass contents
unzip -l test.pkpass

# Validate signature
unzip -p test.pkpass signature | openssl pkcs7 -inform DER -print_certs -text
```

