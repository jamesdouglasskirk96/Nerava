#!/usr/bin/env python3
"""Download Apple WWDR certificate"""
import urllib.request
import ssl
import sys
from pathlib import Path

WWDR_URL = "https://www.apple.com/certificateauthority/AppleWWDRCAG4.cer"
OUTPUT_DIR = Path(__file__).parent.parent / "certs"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "wwdr.pem"

print("Downloading WWDR certificate...")
try:
    # Create SSL context that doesn't verify (for sandbox environments)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    with urllib.request.urlopen(WWDR_URL, context=ctx) as response:
        cer_data = response.read()
    
    # Save .cer file
    cer_path = OUTPUT_DIR / "wwdr.cer"
    with open(cer_path, 'wb') as f:
        f.write(cer_data)
    print(f"✅ Downloaded to: {cer_path}")
    
    # Try to convert to PEM
    try:
        from cryptography import x509
        cert = x509.load_der_x509_certificate(cer_data)
        pem_data = cert.public_bytes(x509.Encoding.PEM)
        with open(OUTPUT_PATH, 'wb') as f:
            f.write(pem_data)
        print(f"✅ Converted to PEM: {OUTPUT_PATH}")
    except Exception as e:
        print(f"⚠️  Could not convert to PEM: {e}")
        print(f"   Using .cer file: {cer_path}")
        OUTPUT_PATH = cer_path
    
    print(f"\n✅ WWDR certificate ready: {OUTPUT_PATH}")
    sys.exit(0)
except Exception as e:
    print(f"❌ Failed to download: {e}")
    print(f"\nPlease download manually from:")
    print(f"  {WWDR_URL}")
    print(f"Save as: {OUTPUT_PATH}")
    sys.exit(1)

