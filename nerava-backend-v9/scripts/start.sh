#!/bin/bash
# Startup script for Nerava Backend
# Runs database migrations then starts the FastAPI application

set -euo pipefail  # Exit on error, undefined vars, and pipe failures

echo "=== Nerava Backend Startup ==="
echo "Working directory: $(pwd)"
echo "Python path: $(which python)"
echo "PORT: ${PORT:-8000}"
echo ""

# Change to app directory (where alembic.ini is located)
cd /app

# Run database migrations
echo "=== Running database migrations ==="
if ! python -m alembic upgrade head; then
    echo "ERROR: Database migrations failed" >&2
    echo "This usually means:" >&2
    echo "  1. DATABASE_URL is not set or incorrect" >&2
    echo "  2. Database is not accessible (network/security group issue)" >&2
    echo "  3. Database user lacks permissions" >&2
    echo "  4. Migration files are corrupted or missing" >&2
    exit 1
fi
echo "Migrations completed successfully"
echo ""

# Start the application
echo "=== Starting FastAPI application ==="
echo "Binding to: 0.0.0.0:${PORT:-8000}"
exec python -m uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}

