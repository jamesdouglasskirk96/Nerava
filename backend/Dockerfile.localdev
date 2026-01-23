# NOTE: This Dockerfile is NOT used by Railway.
# Railway uses Railpack + Procfile in nerava-backend-v9/Procfile.
# This Dockerfile is for other container-based workflows (e.g., Docker Compose, manual Docker builds).

# Multi-stage build for production
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV UVICORN_WORKERS=4

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run the application
# NOTE: This CMD is for Docker-based deployments only, NOT used by Railway.
# Railway uses the Procfile: python -m uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}
CMD ["uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "${UVICORN_WORKERS}"]
