# E2E Tests

End-to-end tests for Nerava UI using Playwright.

## Prerequisites

- Node.js 18+
- Frontend dev server (`nerava-ui`) running on port 5173
- Backend server (`nerava-backend-v9`) running on port 8001
- `MOCK_PLACES=true` environment variable set for backend

## Setup

```bash
npm install
npx playwright install
```

## Running Tests

### Run All Tests

```bash
npm test
```

### Run with UI

```bash
npm run test:ui
```

### Run Specific Test

```bash
npx playwright test charging-flow-e2e
```

## Test Configuration

Tests are configured in `playwright.config.ts`:

- **Base URL**: `http://localhost:5173` (Vite dev server)
- **Backend URL**: `http://localhost:8001`
- **MOCK_PLACES**: Automatically set to `true` for backend server
- **Geolocation**: Mocked to Austin, TX (30.2672, -97.7431) for deterministic testing

## Test: Charging Flow End-to-End

The `charging-flow-e2e.spec.ts` test verifies:

1. Geolocation permission granted
2. Navigate to `/wyc`
3. Featured merchant renders with "Happy Hour ⭐️" badge
4. Tap featured merchant → navigates to details page
5. Tap "Add to Wallet"
6. Success modal appears
7. Tap "Done" closes modal

## Deterministic Testing

Tests use `MOCK_PLACES=true` to return fixture merchants:
- **Asadas Grill** (featured merchant)
- **Eggman ATX** (secondary merchant)
- **Test Coffee Shop** (secondary merchant)

All merchants are located near test coordinates (30.2672, -97.7431) for consistent distance calculations.

## Troubleshooting

### Tests Fail with "No merchants found"

- Ensure backend has `MOCK_PLACES=true` environment variable
- Check backend is running on port 8001
- Verify test coordinates match mock merchant locations

### Geolocation Errors

- Tests automatically grant geolocation permissions
- Mock geolocation is set to Austin, TX coordinates
- If issues persist, check browser console for geolocation errors







