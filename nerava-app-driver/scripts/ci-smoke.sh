#!/bin/bash
set -euo pipefail

# CI Smoke Test Script for Driver App
# Runs a minimal validation suite to ensure the app builds and basic tests pass

echo "🔍 Running CI smoke tests..."

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Lint
echo "🔎 Running linter..."
npm run lint

# Build
echo "🏗️  Building application..."
npm run build

# Verify build output exists
if [ ! -f "dist/index.html" ]; then
  echo "❌ Error: dist/index.html not found after build"
  exit 1
fi

# Run unit tests
echo "🧪 Running unit tests..."
vitest run

# Install Playwright browsers (if not already installed)
echo "🎭 Installing Playwright browsers..."
npx playwright install --with-deps chromium

# Build and start preview server for E2E
echo "🚀 Starting preview server..."
npm run build
npm run preview -- --port 4173 &
PREVIEW_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for preview server..."
timeout=60
elapsed=0
while ! curl -f http://localhost:4173 > /dev/null 2>&1; do
  if [ $elapsed -ge $timeout ]; then
    echo "❌ Error: Preview server did not start within ${timeout}s"
    kill $PREVIEW_PID 2>/dev/null || true
    exit 1
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done

echo "✅ Preview server is ready"

# Run a single critical E2E test (or all if quick)
echo "🎬 Running E2E tests..."
BASE_URL=http://localhost:4173 npm run test:e2e || {
  echo "❌ E2E tests failed"
  kill $PREVIEW_PID 2>/dev/null || true
  exit 1
}

# Cleanup
echo "🧹 Cleaning up..."
kill $PREVIEW_PID 2>/dev/null || true

echo "✅ All smoke tests passed!"


