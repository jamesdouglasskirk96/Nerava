#!/usr/bin/env bash
# Local dev only. Production uses: python -m uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}
# Canonical production start command is defined via Procfile in nerava-backend-v9/Procfile
set -euo pipefail
source .venv/bin/activate
export PYTHONPATH=.
export GOOGLE_API_KEY=${GOOGLE_API_KEY:-""}  # optional for live merchants
uvicorn app.main:app --reload --port 8000
