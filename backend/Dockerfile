# Dockerfile for Nerava Backend
# Builds and runs the FastAPI application on port 8001 (Docker Compose)

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

# Copy application code
COPY . .

# Ensure static directory exists and is accessible
RUN mkdir -p /app/static/demo_chargers || true

# Make startup script executable (if exists)
RUN chmod +x /app/scripts/start.sh 2>/dev/null || true

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose port (App Runner uses 8000)
EXPOSE 8000

# Health check disabled for App Runner - it has its own health checks
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#     CMD python3 -c "import os, urllib.request; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/healthz')" || exit 1

# Simple exec form - no shell, just run uvicorn directly
CMD ["python3", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]

