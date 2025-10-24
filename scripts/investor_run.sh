#!/bin/bash
set -euo pipefail

# Investor demo run script
echo "🎬 Starting Nerava Investor Demo..."

# Set demo mode
export DEMO_MODE=true

# Enable all features
echo "Enabling all demo features..."
curl -s -X POST "http://127.0.0.1:8001/v1/demo/enable_all" \
  -H "Authorization: Bearer demo_admin_key" \
  -H "Content-Type: application/json" | jq '.'

# Seed demo data
echo "Seeding demo data..."
curl -s -X POST "http://127.0.0.1:8001/v1/demo/seed" \
  -H "Authorization: Bearer demo_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"force": false}' | jq '.'

# Get initial state
echo "Getting demo state..."
curl -s -X GET "http://127.0.0.1:8001/v1/demo/state" \
  -H "Authorization: Bearer demo_admin_key" | jq '.'

# Demo scenario: Off-peak to Peak
echo "Setting scenario: Off-peak → Peak"
curl -s -X POST "http://127.0.0.1:8001/v1/demo/scenario" \
  -H "Authorization: Bearer demo_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"key": "grid_state", "value": "offpeak"}' | jq '.'

sleep 2

curl -s -X POST "http://127.0.0.1:8001/v1/demo/scenario" \
  -H "Authorization: Bearer demo_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"key": "grid_state", "value": "peak"}' | jq '.'

# Demo scenario: Merchant A dominates
echo "Setting scenario: Merchant A dominates"
curl -s -X POST "http://127.0.0.1:8001/v1/demo/scenario" \
  -H "Authorization: Bearer demo_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"key": "merchant_shift", "value": "merchant_a_dominates"}' | jq '.'

# Demo scenario: Rep profile high/low
echo "Setting scenario: Rep profile high → low"
curl -s -X POST "http://127.0.0.1:8001/v1/demo/scenario" \
  -H "Authorization: Bearer demo_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"key": "rep_profile", "value": "high"}' | jq '.'

sleep 2

curl -s -X POST "http://127.0.0.1:8001/v1/demo/scenario" \
  -H "Authorization: Bearer demo_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"key": "rep_profile", "value": "low"}' | jq '.'

# Export demo data
echo "Exporting demo data..."
mkdir -p tmp/demo
curl -s -X GET "http://127.0.0.1:8001/v1/demo/export" \
  -H "Authorization: Bearer demo_admin_key" | jq '.' > tmp/demo/export.json

echo "✅ Investor demo setup complete!"
echo "📊 Demo data exported to tmp/demo/export.json"
echo "🌐 Open http://127.0.0.1:8001/app/ to see the demo"
echo "⌨️  Press 'D' key to access developer tools"
