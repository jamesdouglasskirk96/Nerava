#!/bin/bash
# Start Cloudflare Tunnel for local backend

echo "Starting Cloudflare Tunnel to http://localhost:8001..."
echo ""
echo "The tunnel URL will appear below. Copy it to use on your phone."
echo "Press Ctrl+C to stop the tunnel."
echo ""

/opt/homebrew/bin/cloudflared tunnel --url http://localhost:8001


