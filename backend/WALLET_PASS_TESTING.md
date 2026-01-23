# Apple Wallet Pass Testing Guide

## Image Requirements ✅

All images in the pass are now correctly formatted:
- **icon.png**: 29x29 pixels (RGBA mode)
- **icon@2x.png**: 58x58 pixels (RGBA mode)  
- **logo.png**: 160x50 pixels (RGBA mode)
- **logo@2x.png**: 320x100 pixels (RGBA mode)

All images use RGBA mode for proper transparency support (Apple requirement).

## Testing with Apple Sample Passes

Apple doesn't provide official sample `.pkpass` files, but you can test with:

### Option 1: Use Test Apps (Recommended)

1. **Passbook - Wallet Pass Creator** (App Store)
   - Create test passes directly on your iPhone
   - Verify Wallet functionality works on your device

2. **MakePass: AI Wallet Editor** (App Store)
   - AI-driven design tools
   - Easy pass creation and testing

3. **Wallet Creator** (App Store)
   - Create various pass types
   - Test pass functionality

### Option 2: Use Known Working Passes

Test with passes from major brands that definitely work:
- Starbucks Rewards card
- Apple Store gift card
- Any airline boarding pass
- Event tickets from Ticketmaster

If these work on your iPhone, then Wallet functionality is fine and the issue is with our pass configuration.

## Current Pass Status

✅ **File Structure**: Valid
✅ **Signature**: Valid PKCS#7 detached signature
✅ **WWDR Certificate**: Included
✅ **Images**: Correct dimensions, RGBA mode
✅ **pass.json**: All required fields present
✅ **Certificate**: Valid and not expired

## Testing Methods

### Method 1: Email (Most Reliable)
1. Download pass from: `https://YOUR_NGROK_URL/v1/wallet/pass/apple/create.pkpass`
2. Email it to yourself
3. Open email on iPhone
4. Tap attachment - Wallet should open automatically

### Method 2: Direct URL
1. Open in Safari: `https://YOUR_NGROK_URL/v1/wallet/pass/apple/create.pkpass`
2. Safari should recognize it and prompt to add to Wallet

### Method 3: Form Button
1. Visit: `https://YOUR_NGROK_URL/v1/wallet/pass/apple/create`
2. Tap "Add to Apple Wallet" button
3. Form submission should trigger download

## Known Issues with Safari iOS

Safari iOS can be very strict about `.pkpass` files, especially from:
- ngrok domains (certificate warnings)
- Non-HTTPS sources
- Domains without proper SSL certificates

**Solution**: In production with a real domain and SSL certificate, this should work fine.

## Debugging

If the pass still doesn't work:

1. **Check Safari Console**:
   - Settings > Safari > Advanced > Web Inspector
   - Connect iPhone to Mac
   - Check for errors in Safari Developer Tools

2. **Verify File**:
   ```bash
   python3 scripts/diagnose_signature.py your-pass.pkpass
   ```

3. **Test with Email**:
   - Most reliable method
   - Bypasses Safari download restrictions

4. **Check Certificate**:
   ```bash
   openssl x509 -in cert.pem -noout -dates
   ```

## Next Steps

1. Test with one of the Wallet Creator apps to verify your iPhone can add passes
2. If those work, try the email method with our pass
3. If email works but Safari doesn't, it's a Safari/ngrok issue, not a pass issue
4. In production with real domain, Safari should work fine

