# Tesla Virtual Key End-to-End Testing Guide

This guide explains how to test the Tesla Virtual Key onboarding flow locally without a real Tesla Developer Account.

## Prerequisites

1. Backend running locally
2. Feature flags enabled
3. Mock mode active

## Quick Start

### 1. Configure Environment

Add to your `.env` or export these environment variables:

```bash
# Enable Virtual Key feature
export FEATURE_VIRTUAL_KEY_ENABLED=true

# Enable mock mode (bypasses real Tesla API)
export TESLA_MOCK_MODE=true

# Alternative: DEBUG=true also enables mock mode
export DEBUG=true
```

### 2. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 3. Run E2E Test Script

```bash
chmod +x scripts/test_tesla_virtual_key_e2e.sh
./scripts/test_tesla_virtual_key_e2e.sh
```

---

## Manual Testing with cURL

### Step 1: Check Mock API Status

```bash
curl http://localhost:8000/mock-tesla/status | jq
```

Expected response:
```json
{
  "mock_mode": true,
  "vehicles": ["MOCK_VEHICLE_001"],
  "pending_pairings": 0,
  "webhook_callbacks_sent": 0
}
```

### Step 2: List Mock Vehicles

```bash
curl http://localhost:8000/mock-tesla/vehicles | jq
```

### Step 3: Provision Virtual Key

```bash
curl -X POST http://localhost:8000/v1/virtual-key/provision \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vin": "5YJ3E1EA1NF000001"}' | jq
```

Save the `provisioning_token` from the response.

### Step 4: Register Mock Pairing

```bash
curl -X POST http://localhost:8000/mock-tesla/register-pairing \
  -H "Content-Type: application/json" \
  -d '{"provisioning_token": "YOUR_TOKEN", "vehicle_id": "MOCK_VEHICLE_001"}'
```

### Step 5: Complete Pairing (Simulate Tesla App)

```bash
curl -X POST http://localhost:8000/mock-tesla/complete-pairing \
  -H "Content-Type: application/json" \
  -d '{"provisioning_token": "YOUR_TOKEN", "vehicle_id": "MOCK_VEHICLE_001"}' | jq
```

### Step 6: Check Virtual Key Status

```bash
curl http://localhost:8000/v1/virtual-key/status/YOUR_PROVISIONING_TOKEN \
  -H "Authorization: Bearer YOUR_TOKEN" | jq
```

### Step 7: Simulate Vehicle Arrival

```bash
# Set vehicle at Asadas Grill location
curl -X POST http://localhost:8000/mock-tesla/simulate-arrival \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "MOCK_VEHICLE_001",
    "lat": 30.4027969,
    "lng": -97.6719438
  }' | jq
```

---

## Test Scenarios

### Scenario A: First-Time User Flow

1. User opens Nerava in Tesla browser
2. No active Virtual Key → sees onboarding prompt
3. Taps "Scan QR to Set Up"
4. QR code displayed with provisioning token
5. User scans with Tesla app (simulated by `complete-pairing`)
6. Virtual Key paired and activated
7. User proceeds to order from Asadas Grill
8. Vehicle arrival detected automatically

### Scenario B: Returning User Flow

1. User opens Nerava in Tesla browser
2. Active Virtual Key detected → no prompt
3. User orders from Asadas Grill
4. Arrival session created with Virtual Key linked
5. Vehicle arrival detected automatically

### Scenario C: Phone Handoff Fallback

1. User opens Nerava in Tesla browser
2. No active Virtual Key → sees onboarding prompt
3. Taps "Skip - Use Phone Instead"
4. Phone handoff QR displayed
5. User continues order on phone
6. Manual check-in when arriving

---

## Mock Tesla API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mock-tesla/status` | GET | Check mock API status |
| `/mock-tesla/vehicles` | GET | List mock vehicles |
| `/mock-tesla/vehicle/{id}/data` | GET | Get vehicle telemetry |
| `/mock-tesla/register-pairing` | POST | Register pairing request |
| `/mock-tesla/complete-pairing` | POST | Simulate pairing completion |
| `/mock-tesla/simulate-arrival` | POST | Simulate vehicle arrival |
| `/mock-tesla/set-vehicle-location` | POST | Update vehicle location |
| `/mock-tesla/set-vehicle-battery` | POST | Update battery state |
| `/mock-tesla/add-vehicle` | POST | Add new mock vehicle |
| `/mock-tesla/webhooks` | GET | View webhook history |
| `/mock-tesla/reset` | POST | Reset mock state |

---

## Test Data

### Asadas Grill

```json
{
  "merchant_id": "asadas_grill_canyon_ridge",
  "name": "Asadas Grill",
  "location": {
    "lat": 30.4027969,
    "lng": -97.6719438
  },
  "address": "501 W Canyon Ridge Dr, Austin, TX 78753"
}
```

### Canyon Ridge Supercharger

```json
{
  "charger_id": "canyon_ridge_tesla",
  "name": "Tesla Supercharger - Canyon Ridge",
  "location": {
    "lat": 30.3979,
    "lng": -97.7044
  },
  "address": "500 W Canyon Ridge Dr, Austin, TX 78753"
}
```

### Default Mock Vehicle

```json
{
  "vehicle_id": "MOCK_VEHICLE_001",
  "vin": "5YJ3E1EA1NF000001",
  "display_name": "James's Model Y",
  "battery_level": 65,
  "charging_state": "Charging"
}
```

---

## Troubleshooting

### Mock API Returns 403 Forbidden

**Cause:** Mock mode not enabled.

**Fix:** Set environment variables:
```bash
export TESLA_MOCK_MODE=true
# or
export DEBUG=true
```

### Virtual Key Provision Returns 410 Gone

**Cause:** Feature flag not enabled.

**Fix:** Enable the feature:
```bash
export FEATURE_VIRTUAL_KEY_ENABLED=true
```

### Pairing Status Returns "expired"

**Cause:** Provisioning token has 5-minute expiry.

**Fix:** Create a new provisioning request.

### Webhook Not Triggering Arrival

**Cause:** Arrival detection logic not fully implemented in webhook handler.

**Note:** The `vehicle_location` webhook handler has a TODO for implementing arrival detection. For now, simulate arrivals directly via the mock API.

---

## Next Steps

After validating with the mock API:

1. **Apply for Tesla Developer Account** - See `TESLA_DEVELOPER_ACCOUNT_SETUP.md`
2. **Configure Real Credentials** - Set `TESLA_CLIENT_ID` and `TESLA_CLIENT_SECRET`
3. **Test with Real Vehicle** - Pair a real Tesla using the Fleet API
4. **Enable in Production** - Set `FEATURE_VIRTUAL_KEY_ENABLED=true` and `TESLA_MOCK_MODE=false`
