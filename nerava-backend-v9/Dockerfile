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

# Create non-root user first (before copying files)
RUN useradd --create-home --shell /bin/bash app

# Copy Python packages from builder to system location (accessible by all users)
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x /app/scripts/start.sh

# Set ownership of app directory
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check (using Python since curl may not be available)
# Uses PORT env var with fallback to 8000 (App Runner default)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import os, urllib.request; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/healthz')" || exit 1

# Run the application using startup script (runs migrations then starts uvicorn)
# Using main_simple as the entry point (as per Procfile)
CMD ["/app/scripts/start.sh"]

