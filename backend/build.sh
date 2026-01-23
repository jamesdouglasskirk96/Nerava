#!/usr/bin/env bash
# Railway build script - ensures dependencies are installed
set -e

echo "🔨 Building Nerava backend..."
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Upgrade pip first
pip install --upgrade pip

# Install dependencies from requirements.txt
echo "📦 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "✅ Build complete!"

