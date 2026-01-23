# Apple Wallet Pass Generator

This directory contains a self-contained builder for generating a signed Apple Wallet pass (`.pkpass` file) for Nerava's "While You Charge" feature.

## Prerequisites

Before building the pass, ensure you have:

1. **Certificate and Key Files** (in repo root):
   - `./nerava.key` - Private key file for signing
   - `./pass.cer` - Apple Pass Type ID certificate

2. **WWDR Certificate** (optional but recommended):
   - `wallet-pass/wwdr.pem` - Apple Worldwide Developer Relations intermediate certificate
   - If missing, the build will warn but continue (prototype mode)
   - **Required for iPhone to show "Add to Wallet"**: Download from Apple and place at `wallet-pass/wwdr.pem`

3. **Image Assets** (place in `assets/` directory):
   - `assets/logo.png` - Logo image with transparent background
   - `assets/icon.png` - Icon image (29x29 pixels, transparent background)

See `assets/README.md` for more details on the image requirements.

## Building the Pass

1. **Place image assets** in `wallet-pass/assets/`:
   ```bash
   # Copy your logo and icon files
   cp /path/to/logo.png wallet-pass/assets/
   cp /path/to/icon.png wallet-pass/assets/
   ```

2. **Run the build script**:
   ```bash
   ./wallet-pass/build.sh
   ```

The script will:
- Validate all required files exist
- Create a build directory with pass files
- Generate a manifest.json with SHA1 hashes
- Sign the manifest using your certificate and key
- Create `wallet-pass/dist/nerava.pkpass`

## Installing the Pass

### Method 1: AirDrop (Recommended)
1. AirDrop `wallet-pass/dist/nerava.pkpass` to your iPhone
2. Tap the file when it arrives
3. Tap "Add" to add to Wallet

### Method 2: Email/Web
1. Email the `.pkpass` file to yourself or host it on a web server
2. Open the email/link on your iPhone
3. Tap "Add" to add to Wallet

### Method 3: Direct Transfer
1. Transfer `nerava.pkpass` to your iPhone via Files app or cloud storage
2. Open the file
3. Tap "Add" to add to Wallet

## Pass Contents

The generated pass includes:
- **Header**: "Charging Active" status indicator
- **Primary Field**: "You're Charging. Here's What's Nearby."
- **Secondary Field**: "Walkable places while you wait."
- **QR Code**: Links to `https://nerava.network` with alt text "Show for Perks"
- **Logo**: Nerava logo (top-left)
- **Icon**: Small icon (29x29)

## Troubleshooting

### Build Fails: "Missing ./nerava.key"
- Ensure the private key file exists in the repo root
- Check file permissions

### Build Fails: "Missing ./pass.cer"
- Ensure the certificate file exists in the repo root
- Verify it's a valid Apple Pass Type ID certificate

### Build Fails: "Failed to sign manifest"
- Verify the certificate and key are valid and match
- Check that the certificate is not expired
- Ensure the certificate format is correct (DER or PEM)
- **Note**: Apple Wallet passes typically require the Apple Worldwide Developer Relations (WWDR) intermediate certificate. If the pass fails to install, you may need to download the WWDR certificate from Apple and include it in the signing process. The current script uses only `pass.cer` and `nerava.key`.

### Pass Won't Install on iPhone / "Add to Wallet" Not Showing
- **Most common issue**: Missing WWDR certificate. Place the Apple Worldwide Developer Relations intermediate certificate at `wallet-pass/wwdr.pem`
  - Download from: https://www.apple.com/certificateauthority/AppleWWDRCAG4.cer (or G3/G4 depending on your certificate)
  - Convert to PEM: `openssl x509 -inform DER -in AppleWWDRCAG4.cer -out wallet-pass/wwdr.pem`
- Verify the certificate is properly configured in Apple Developer Portal
- Check that the pass type identifier matches your Apple Developer account
- Ensure the team identifier is correct
- Try rebuilding with a fresh certificate/key pair

### Pass Installs But Shows Errors
- Verify all image assets are present and properly formatted
- Check that `pass.json` is valid JSON
- Ensure QR code URL is accessible

### "Add to Wallet" Not Showing in Email
- **Delivery method matters**: Some email clients strip the `.pkpass` MIME type or don't recognize it properly
- **Recommended**: Use AirDrop or open the `.pkpass` file from Safari on your iPhone
- **Alternative**: Host the `.pkpass` file on a web server and open the download link in Safari on iPhone
- If Mail doesn't show "Add to Wallet", try:
  1. Save the `.pkpass` attachment to Files app
  2. Tap the file in Files app
  3. It should prompt to add to Wallet

## Technical Details

- **Format**: Apple Wallet pass (PKPass)
- **Signing**: Uses OpenSSL S/MIME signing with SHA1 manifest
- **Tools**: Uses system tools only (openssl, zip, shasum) - no npm dependencies
- **Certificate**: Automatically converts DER to PEM if needed

## File Structure

```
wallet-pass/
├── README.md           # This file
├── pass.json           # Pass definition (JSON)
├── build.sh            # Build script
├── assets/
│   ├── README.md       # Asset requirements
│   ├── logo.png        # (user-provided)
│   └── icon.png        # (user-provided)
├── build/              # (generated during build)
│   ├── pass.json
│   ├── logo.png
│   ├── icon.png
│   ├── manifest.json
│   └── signature
└── dist/
    └── nerava.pkpass   # (final output)
```

