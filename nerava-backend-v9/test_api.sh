#!/usr/bin/env bash
set -e
echo "🚀 Running regression tests..."
pytest -q --disable-warnings
