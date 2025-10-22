#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
export PYTHONPATH=.
export GOOGLE_API_KEY=${GOOGLE_API_KEY:-""}  # optional for live merchants
uvicorn app.main:app --reload --port 8000
