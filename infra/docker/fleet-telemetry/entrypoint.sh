#!/bin/sh
set -e

echo "Fleet Telemetry entrypoint: writing config and certs..."

# Write config, cert, and key from env vars (set via ECS Secrets Manager)
if [ -n "$FLEET_TELEMETRY_CONFIG_JSON" ]; then
    printf '%s' "$FLEET_TELEMETRY_CONFIG_JSON" > /etc/fleet-telemetry/config.json
    echo "  config.json written"
fi

if [ -n "$FLEET_TELEMETRY_CERT" ]; then
    printf '%s' "$FLEET_TELEMETRY_CERT" > /etc/fleet-telemetry/cert.pem
    echo "  cert.pem written ($(wc -c < /etc/fleet-telemetry/cert.pem) bytes)"
fi

if [ -n "$FLEET_TELEMETRY_KEY" ]; then
    printf '%s' "$FLEET_TELEMETRY_KEY" > /etc/fleet-telemetry/key.pem
    chmod 600 /etc/fleet-telemetry/key.pem
    echo "  key.pem written"
fi

echo "Starting fleet-telemetry..."
exec /fleet-telemetry --config /etc/fleet-telemetry/config.json
