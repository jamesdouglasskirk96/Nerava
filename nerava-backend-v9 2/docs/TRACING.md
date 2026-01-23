# OpenTelemetry Distributed Tracing Guide

This document describes how to enable OpenTelemetry distributed tracing in the Nerava platform.

## Overview

OpenTelemetry tracing provides distributed tracing capabilities for monitoring and debugging requests across services. Tracing is **optional** and disabled by default to avoid any performance impact.

## Current Status

Tracing is implemented but **not enabled by default**. To enable tracing, set `OTEL_ENABLED=true`.

## Prerequisites

Install OpenTelemetry dependencies:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-httpx
```

## Configuration

### Environment Variables

Set the following environment variables to enable tracing:

```bash
# Enable tracing
export OTEL_ENABLED=true

# OTLP exporter endpoint (default: http://localhost:4318/v1/traces)
export OTEL_EXPORTER_ENDPOINT=http://localhost:4318/v1/traces

# Optional: Service name (default: nerava-api)
export OTEL_SERVICE_NAME=nerava-api

# Optional: Service version (default: 1.0.0)
export OTEL_SERVICE_VERSION=1.0.0
```

### Exporter Endpoints

Common OTLP exporter endpoints:

- **Local development**: `http://localhost:4318/v1/traces`
- **Jaeger**: `http://localhost:4317/v1/traces`
- **Tempo**: `http://localhost:4318/v1/traces`
- **Datadog**: `https://trace-intake.datadoghq.com/api/v0/traces`
- **New Relic**: `https://otlp.nr-data.net`

## Enabling Tracing

### Step 1: Initialize Tracing

Tracing is initialized in `app/main_simple.py`:

```python
from app.core.tracing import initialize_tracing

# Initialize tracing (only if OTEL_ENABLED=true)
initialize_tracing()
```

### Step 2: Instrument FastAPI

FastAPI instrumentation is handled automatically by the tracing module when enabled.

### Step 3: Instrument HTTP Clients

HTTP clients (httpx) are instrumented automatically when tracing is enabled.

## Usage

### Manual Tracing

You can create spans manually:

```python
from app.core.tracing import get_tracer

tracer = get_tracer(__name__)

with tracer.start_as_current_span("my_operation"):
    # Your code here
    pass
```

### Automatic Instrumentation

When tracing is enabled, the following are automatically instrumented:
- FastAPI requests/responses
- HTTP client calls (httpx)
- Database queries (if SQLAlchemy instrumentation is added)

## Testing

### Local Testing

1. **Start an OTLP collector** (e.g., Jaeger):
   ```bash
   docker run -d -p 4318:4318 -p 16686:16686 jaegertracing/opentelemetry-collector:latest
   ```

2. **Enable tracing**:
   ```bash
   export OTEL_ENABLED=true
   export OTEL_EXPORTER_ENDPOINT=http://localhost:4318/v1/traces
   ```

3. **Start the application**:
   ```bash
   python -m app.main_simple
   ```

4. **View traces**: Open http://localhost:16686 (Jaeger UI)

### Production Setup

1. **Deploy an OTLP collector** (e.g., AWS X-Ray, Datadog, New Relic)

2. **Set environment variables** in your deployment:
   ```bash
   OTEL_ENABLED=true
   OTEL_EXPORTER_ENDPOINT=https://your-collector-endpoint/v1/traces
   ```

3. **Verify tracing**: Check collector logs/metrics to confirm traces are being received

## Disabling Tracing

Tracing is disabled by default. To explicitly disable:

```bash
export OTEL_ENABLED=false
```

Or simply don't set `OTEL_ENABLED` (defaults to false).

## Performance Impact

When tracing is **disabled** (default):
- **Zero overhead** - No instrumentation code runs
- **No dependencies required** - OpenTelemetry packages are optional

When tracing is **enabled**:
- Minimal overhead (~1-2ms per request)
- Traces are batched and sent asynchronously
- Failed trace exports don't affect application performance

## Troubleshooting

### Tracing Not Working

1. **Check logs**: Look for "OpenTelemetry tracing initialized" message
2. **Verify dependencies**: Ensure OpenTelemetry packages are installed
3. **Check exporter endpoint**: Verify `OTEL_EXPORTER_ENDPOINT` is correct
4. **Verify network**: Ensure collector endpoint is reachable

### Import Errors

If you see `ImportError: opentelemetry not installed`:
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

### Traces Not Appearing

1. **Check collector logs**: Verify traces are being received
2. **Verify service name**: Check `OTEL_SERVICE_NAME` matches your collector configuration
3. **Check sampling**: Some collectors sample traces (check collector config)

## Example Traces

When tracing is enabled, you'll see traces for:
- HTTP requests (method, path, status code)
- External API calls (Google Places, NREL, Smartcar)
- Database queries (if SQLAlchemy instrumentation added)
- Custom spans (if manually created)

## Future Enhancements

Potential future improvements:
- SQLAlchemy instrumentation for database query tracing
- Redis instrumentation for cache operation tracing
- Custom spans for business logic (Nova grants, redemptions)
- Trace sampling configuration
- Multiple exporter support







