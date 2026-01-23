# Dockerfile for Nerava Backend
# Builds and runs the FastAPI application on port 8000 (App Runner default, respects PORT env var)

# Multi-stage build for production
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies to a shared location
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy Python packages from builder to system location
COPY --from=builder /install /usr/local

# Copy application code (includes merchant_photos_asadas_grill if copied into directory)
COPY . .

# Make startup script executable (if exists)
RUN chmod +x /app/scripts/start.sh 2>/dev/null || true

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Note: HEALTHCHECK disabled for App Runner - it has its own health checks
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python3 -c "import os, urllib.request; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/healthz')" || exit 1

# Run uvicorn directly with exec form (no shell)
# Port 8000 is hardcoded since App Runner sets PORT=8000 in env
CMD ["python", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
