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

# Check if migrations should run on boot
RUN_MIGRATIONS=${RUN_MIGRATIONS_ON_BOOT:-false}

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "=== Running database migrations ==="
    if python -m alembic upgrade head; then
        echo "Migrations completed successfully"
    else
        echo "WARNING: Database migrations failed, but continuing startup" >&2
        echo "This usually means:" >&2
        echo "  1. DATABASE_URL is not set or incorrect" >&2
        echo "  2. Database is not accessible (network/security group issue)" >&2
        echo "  3. Database user lacks permissions" >&2
        echo "  4. Migration files are corrupted or missing" >&2
        # Don't exit - continue to start the app
    fi
    echo ""
else
    echo "Skipping migrations (RUN_MIGRATIONS_ON_BOOT not set to 'true')"
    echo ""
fi

# Start the application
echo "=== Starting FastAPI application ==="
echo "Binding to: 0.0.0.0:${PORT:-8000}"
exec python -m uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}

