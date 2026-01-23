# Apple Wallet Signing Setup

## Quick Setup Steps

### 1. Download WWDR Certificate

Download the Apple WWDR certificate:
```bash
cd nerava-backend-v9
mkdir -p certs
curl -L "https://www.apple.com/certificateauthority/AppleWWDRCAG4.cer" -o certs/wwdr.cer
openssl x509 -inform DER -in certs/wwdr.cer -out certs/wwdr.pem
```

Or download manually from: https://www.apple.com/certificateauthority/
Save as: `nerava-backend-v9/certs/wwdr.pem`

### 2. Get Your Apple Developer Certificates

You need:
- **Pass Type ID Certificate** (.p12 file OR .pem certificate + .pem key)
- **Team ID** (from Apple Developer account)
- **Pass Type ID** (e.g., `pass.com.nerava.wallet`)

Get these from: https://developer.apple.com/account/resources/identifiers/list/passTypeId

### 3. Set Environment Variables

Create a file `certs/env_setup.sh`:

```bash
export APPLE_WALLET_SIGNING_ENABLED=true
export APPLE_WALLET_WWDR_CERT_PATH="/Users/jameskirk/Desktop/Nerava/nerava-backend-v9/certs/wwdr.pem"
export APPLE_WALLET_CERT_P12_PATH="/path/to/your/cert.p12"  # OR use CERT_PATH + KEY_PATH
export APPLE_WALLET_CERT_P12_PASSWORD=""  # If your P12 has a password
export APPLE_WALLET_PASS_TYPE_ID="pass.com.nerava.wallet"
export APPLE_WALLET_TEAM_ID="YOUR_TEAM_ID"
```

Or if using PEM files:
```bash
export APPLE_WALLET_CERT_PATH="/path/to/cert.pem"
export APPLE_WALLET_KEY_PATH="/path/to/key.pem"
export APPLE_WALLET_KEY_PASSWORD=""  # If your key has a password
```

### 4. Start Server with Signing

```bash
cd nerava-backend-v9
source certs/env_setup.sh  # Load environment variables
./scripts/start_with_ngrok.sh  # Or start manually
```

## Testing Without Certificates

If you don't have certificates yet, you can test the endpoint structure:

```bash
# Endpoint will return 501 error, but you can verify it's working
curl https://your-ngrok-url/v1/wallet/pass/apple/create
```

The endpoint will return:
```json
{
  "detail": {
    "error": "APPLE_WALLET_SIGNING_DISABLED",
    "message": "Apple Wallet pass signing is not enabled on this environment."
  }
}
```

This confirms the endpoint is working - you just need certificates to generate actual passes.

## Current Status

✅ GET endpoint working  
✅ Authentication working (with NERAVA_DEV_ALLOW_ANON_DRIVER=true)  
⏳ Signing configuration needed

## Next Steps

1. Download WWDR certificate (see step 1 above)
2. Get your Pass Type ID certificate from Apple Developer
3. Set environment variables
4. Restart server
5. Test on iPhone Safari

