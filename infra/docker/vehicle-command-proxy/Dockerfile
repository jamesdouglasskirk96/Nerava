# Tesla Vehicle Command HTTP Proxy — signs API requests with developer's private key.
# Required for fleet_telemetry_config and vehicle commands.
FROM tesla/vehicle-command:latest AS source

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /config

COPY --from=source /usr/local/bin/tesla-http-proxy /tesla-http-proxy
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 4443

ENTRYPOINT ["/entrypoint.sh"]
