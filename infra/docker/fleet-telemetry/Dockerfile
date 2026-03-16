# Wrapper for Tesla's fleet-telemetry (FROM scratch) that adds a shell
# for cert extraction from env vars before starting the binary.
FROM tesla/fleet-telemetry:latest AS source

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /etc/fleet-telemetry

COPY --from=source /fleet-telemetry /fleet-telemetry
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 443

ENTRYPOINT ["/entrypoint.sh"]
