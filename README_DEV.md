# Nerava Development Guide

## Investor Polish (Day Plan)
- Run `./scripts/investor_run.sh` then open the UI. Press **D** for Dev tab.
- Capture screenshots: Explore (deal chip), Charge (map), Wallet (reward), Me (EnergyRep modal), Dev (charts).
- CI uploads artifacts on failure under GitHub Actions.

## 🎬 Investor Demo

### Quick Start (7-9 minutes)

1. **Start the demo:**
   ```bash
   # Terminal 1: Start backend
   cd nerava-backend-v9
   source .venv/bin/activate
   export DEMO_MODE=true
   uvicorn app.main_simple:app --reload --port 8001 --host 127.0.0.1
   
   # Terminal 2: Run investor script
   ./scripts/investor_run.sh
   ```

2. **Open the app:**
   - Navigate to http://127.0.0.1:8001/app/
   - You'll see the demo banner with current state
   - Press 'D' key to access developer tools

3. **Demo flow:**
   - **Explore**: Shows deal chips with countdown timers
   - **Charge**: Full-height map, scan panel hidden in demo
   - **Wallet**: Recent activity from demo export
   - **Me**: EnergyRep score with breakdown modal
   - **Dev Tools**: Merchant Intel & Behavior Cloud analytics

### Screenshots to Capture

- [ ] Demo banner showing grid state
- [ ] Deal chips with countdown timers
- [ ] Full-height map on Charge page
- [ ] Wallet activity list
- [ ] EnergyRep breakdown modal
- [ ] Merchant Intel cohort distribution
- [ ] Behavior Cloud participation rates

### cURL Commands

```bash
# Enable demo mode
curl -X POST "http://127.0.0.1:8001/v1/demo/enable_all" \
  -H "Authorization: Bearer demo_admin_key"

# Seed data
curl -X POST "http://127.0.0.1:8001/v1/demo/seed" \
  -H "Authorization: Bearer demo_admin_key" \
  -d '{"force": false}'

# Toggle scenarios
curl -X POST "http://127.0.0.1:8001/v1/demo/scenario" \
  -H "Authorization: Bearer demo_admin_key" \
  -d '{"key": "grid_state", "value": "peak"}'

# Export data
curl -X GET "http://127.0.0.1:8001/v1/demo/export" \
  -H "Authorization: Bearer demo_admin_key"
```

## Development

### Backend

```bash
cd nerava-backend-v9
source .venv/bin/activate
export DATABASE_URL="sqlite:///./nerava.db"
export DEMO_MODE=true
uvicorn app.main_simple:app --reload --port 8001
```

### Frontend

```bash
cd ui-mobile
npm install
# Open http://127.0.0.1:8001/app/ in browser
```

### Tests

```bash
# Backend tests
cd nerava-backend-v9
pytest -q

# Frontend E2E tests
cd ui-mobile
npx playwright test
```

## Features

### Demo Mode
- Bulk enables all feature flags
- Seeds realistic data
- Scenario toggles for different states
- Export functionality for data analysis

### UI Polish
- Demo banner with state indicators
- Deal chips with countdown timers
- Full-height maps
- EnergyRep breakdown modals
- Recent activity feeds

### Backend Logic v1
- Merchant Intelligence with cohort analysis
- Behavior Cloud with participation metrics
- EnergyRep scoring with component breakdown
- Deterministic calculations for demos

### Developer Tools
- Press 'D' key to access dev tab
- Merchant Intel analytics view
- Behavior Cloud analytics view
- Real-time scenario switching
