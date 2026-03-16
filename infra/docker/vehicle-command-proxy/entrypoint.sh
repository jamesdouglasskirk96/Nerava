#!/bin/sh
set -e

echo "Vehicle Command Proxy entrypoint: writing certs..."
mkdir -p /config

# Write TLS cert/key (for proxy's own HTTPS server)
if [ -n "$PROXY_TLS_CERT" ]; then
    printf '%s' "$PROXY_TLS_CERT" > /config/tls-cert.pem
    echo "  tls-cert.pem written ($(wc -c < /config/tls-cert.pem) bytes)"
fi

if [ -n "$PROXY_TLS_KEY" ]; then
    printf '%s' "$PROXY_TLS_KEY" > /config/tls-key.pem
    chmod 600 /config/tls-key.pem
    echo "  tls-key.pem written"
fi

# Write fleet private key (for signing vehicle commands)
if [ -n "$FLEET_PRIVATE_KEY" ]; then
    printf '%s' "$FLEET_PRIVATE_KEY" > /config/fleet-key.pem
    chmod 600 /config/fleet-key.pem
    echo "  fleet-key.pem written"
fi

echo "Starting tesla-http-proxy on port ${PROXY_PORT:-4443}..."
exec /tesla-http-proxy \
    -tls-key /config/tls-key.pem \
    -cert /config/tls-cert.pem \
    -key-file /config/fleet-key.pem \
    -host 0.0.0.0 \
    -port "${PROXY_PORT:-4443}"
