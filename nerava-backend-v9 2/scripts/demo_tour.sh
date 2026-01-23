#!/bin/bash
# Demo tour script for investor-friendly demo system

set -e

BASE_URL="http://127.0.0.1:8001"
API_KEY="demo-admin-key-2024"
VERIFY_KEY="demo-verify-key-2024"

echo "🎬 Starting Nerava Investor Demo Tour"
echo "======================================"

# Create output directory
mkdir -p tmp/demo

# Step 1: Enable all flags
echo "📋 Step 1: Enabling all feature flags..."
curl -s -X POST "$BASE_URL/v1/demo/enable_all" \
  -H "X-Nerava-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  | jq '.' > tmp/demo/enable_flags.json
echo "✅ Feature flags enabled"

# Step 2: Seed demo data
echo "🌱 Step 2: Seeding demo data..."
curl -s -X POST "$BASE_URL/v1/demo/seed" \
  -H "X-Nerava-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  | jq '.' > tmp/demo/seed_data.json
echo "✅ Demo data seeded"

# Step 3: Set off-peak scenario
echo "🌅 Step 3: Setting off-peak scenario..."
curl -s -X POST "$BASE_URL/v1/demo/scenario" \
  -H "X-Nerava-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key": "grid_state", "value": "offpeak"}' \
  | jq '.' > tmp/demo/offpeak_scenario.json
echo "✅ Off-peak scenario set"

# Step 4: Test Behavior Cloud (off-peak)
echo "☁️ Step 4: Testing Behavior Cloud (off-peak)..."
curl -s -X GET "$BASE_URL/v1/utility/behavior/cloud?utility_id=UT_TX&window=24h" \
  -H "X-Nerava-Key: $API_KEY" \
  | jq '.' > tmp/demo/behavior_cloud_offpeak.json
echo "✅ Behavior Cloud (off-peak) tested"

# Step 5: Set peak scenario
echo "⚡ Step 5: Setting peak scenario..."
curl -s -X POST "$BASE_URL/v1/demo/scenario" \
  -H "X-Nerava-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key": "grid_state", "value": "peak"}' \
  | jq '.' > tmp/demo/peak_scenario.json
echo "✅ Peak scenario set"

# Step 6: Test Autonomous Reward Routing (peak)
echo "🤖 Step 6: Testing Autonomous Reward Routing (peak)..."
curl -s -X POST "$BASE_URL/v1/rewards/routing/rebalance" \
  -H "X-Nerava-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  | jq '.' > tmp/demo/reward_routing_peak.json
echo "✅ Autonomous Reward Routing (peak) tested"

# Step 7: Set merchant A dominance
echo "🏪 Step 7: Setting merchant A dominance..."
curl -s -X POST "$BASE_URL/v1/demo/scenario" \
  -H "X-Nerava-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key": "merchant_shift", "value": "A_dominates"}' \
  | jq '.' > tmp/demo/merchant_a_dominance.json
echo "✅ Merchant A dominance set"

# Step 8: Test Merchant Intelligence
echo "📊 Step 8: Testing Merchant Intelligence..."
curl -s -X GET "$BASE_URL/v1/merchant/intel/overview?merchant_id=M_A" \
  -H "X-Nerava-Key: $API_KEY" \
  | jq '.' > tmp/demo/merchant_intel.json
echo "✅ Merchant Intelligence tested"

# Step 9: Test EnergyRep (high)
echo "⭐ Step 9: Testing EnergyRep (high)..."
curl -s -X GET "$BASE_URL/v1/profile/energy_rep?user_id=1" \
  -H "X-Nerava-Key: $API_KEY" \
  | jq '.' > tmp/demo/energy_rep_high.json
echo "✅ EnergyRep (high) tested"

# Step 10: Test EnergyRep (low)
echo "🥉 Step 10: Testing EnergyRep (low)..."
curl -s -X GET "$BASE_URL/v1/profile/energy_rep?user_id=2" \
  -H "X-Nerava-Key: $API_KEY" \
  | jq '.' > tmp/demo/energy_rep_low.json
echo "✅ EnergyRep (low) tested"

# Step 11: Test Charge Verification (good)
echo "✅ Step 11: Testing Charge Verification (good)..."
curl -s -X POST "$BASE_URL/v1/verify/charge" \
  -H "X-Nerava-Key: $VERIFY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "charge_session_id": "good_charge_123",
    "kwh_charged": 5.0,
    "location": {"lat": 30.2672, "lng": -97.7431},
    "station_location": {"lat": 30.2670, "lng": -97.7430}
  }' \
  | jq '.' > tmp/demo/verify_charge_good.json
echo "✅ Charge Verification (good) tested"

# Step 12: Test Charge Verification (fraud - below min kWh)
echo "🚨 Step 12: Testing Charge Verification (fraud - below min kWh)..."
curl -s -X POST "$BASE_URL/v1/verify/charge" \
  -H "X-Nerava-Key: $VERIFY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "charge_session_id": "fraud_charge_123",
    "kwh_charged": 0.5,
    "location": {"lat": 30.2672, "lng": -97.7431}
  }' \
  | jq '.' > tmp/demo/verify_charge_fraud.json
echo "✅ Charge Verification (fraud) tested"

# Step 13: Test Finance Offers
echo "💰 Step 13: Testing Finance Offers..."
curl -s -X GET "$BASE_URL/v1/finance/offers?user_id=1" \
  -H "X-Nerava-Key: $API_KEY" \
  | jq '.' > tmp/demo/finance_offers.json
echo "✅ Finance Offers tested"

# Step 14: Test City Impact
echo "🏙️ Step 14: Testing City Impact..."
curl -s -X GET "$BASE_URL/v1/city/impact?city_slug=austin" \
  -H "X-Nerava-Key: $API_KEY" \
  | jq '.' > tmp/demo/city_impact.json
echo "✅ City Impact tested"

# Step 15: Test SDK Config
echo "🔧 Step 15: Testing SDK Config..."
curl -s -X GET "$BASE_URL/v1/sdk/config?tenant_id=demo_tenant" \
  -H "X-Nerava-Key: $API_KEY" \
  | jq '.' > tmp/demo/sdk_config.json
echo "✅ SDK Config tested"

# Step 16: Test Wallet Interop
echo "💳 Step 16: Testing Wallet Interop..."
curl -s -X GET "$BASE_URL/v1/wallet/interop/options" \
  -H "X-Nerava-Key: $API_KEY" \
  | jq '.' > tmp/demo/wallet_interop.json
echo "✅ Wallet Interop tested"

# Step 17: Export comprehensive demo data
echo "📤 Step 17: Exporting comprehensive demo data..."
curl -s -X GET "$BASE_URL/v1/demo/export" \
  -H "X-Nerava-Key: $API_KEY" \
  | jq '.' > tmp/demo/export_data.json
echo "✅ Demo data exported"

echo ""
echo "🎉 Demo Tour Complete!"
echo "======================"
echo "📁 Results saved to tmp/demo/"
echo "📊 Check tmp/demo/export_data.json for comprehensive demo data"
echo "🔗 Postman collection: postman/Nerava_Demo.postman_collection.json"
echo ""
echo "📸 Suggested screenshots:"
echo "  - Behavior Cloud (off-peak vs peak)"
echo "  - Merchant Intelligence (A dominance)"
echo "  - EnergyRep (high vs low tiers)"
echo "  - Charge Verification (good vs fraud)"
echo "  - Finance Offers (APR delta)"
echo "  - City Impact (leaderboard)"
echo "  - SDK Config (platformization)"
