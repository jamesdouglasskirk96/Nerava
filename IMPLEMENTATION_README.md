# Nerava UI Implementation - Quick Start Guide

This document provides exact commands to run the frontend, backend, and E2E tests.

## Prerequisites

- Node.js 18+ installed
- Python 3.9+ installed
- Backend dependencies installed (`cd nerava-backend-v9 && pip install -r requirements.txt`)
- Database migrations run (`cd nerava-backend-v9 && alembic upgrade head`)

## Running the Application

### 1. Start Backend

```bash
cd nerava-backend-v9
export MOCK_PLACES=true  # For deterministic testing
python -m uvicorn app.main_simple:app --port 8001 --reload
```

Backend will be available at `http://localhost:8001`

### 2. Start Frontend

In a new terminal:

```bash
cd nerava-ui
npm install  # First time only
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 3. Open in Browser

Navigate to `http://localhost:5173/wyc`

The app will:
- Request geolocation permission
- Call `POST /v1/intent/capture` with your location
- Display featured merchant (Asadas Grill or Eggman ATX if `MOCK_PLACES=true`)
- Allow navigation to merchant details
- Support "Add to Wallet" flow

## Running Tests

### Frontend Unit Tests

```bash
cd nerava-ui
npm test
```

### Backend Tests

```bash
cd nerava-backend-v9
pytest tests/api/test_merchant_details.py tests/api/test_wallet_activate.py -v
```

### E2E Tests

**Prerequisites**: Both frontend and backend must be running (see above)

```bash
cd e2e
npm install  # First time only
npx playwright install  # First time only - installs browsers
npm test
```

Or with UI:

```bash
npm run test:ui
```

## Environment Variables

### Backend

Create `nerava-backend-v9/.env`:

```env
DATABASE_URL=sqlite:///./nerava.db
MOCK_PLACES=true  # For deterministic testing
GOOGLE_PLACES_API_KEY=your_key_here  # Optional if MOCK_PLACES=true
```

### Frontend

Create `nerava-ui/.env` (optional):

```env
VITE_API_BASE_URL=http://localhost:8001
```

## MOCK_PLACES Mode

When `MOCK_PLACES=true`, the backend returns fixture merchants for test location (30.2672, -97.7431):

- **Asadas Grill** - Featured merchant with "Happy Hour ⭐️" badge
- **Eggman ATX** - Secondary merchant
- **Test Coffee Shop** - Secondary merchant

This ensures deterministic E2E tests without external API calls.

## Project Structure

```
/nerava-ui/                    # New React frontend
/nerava-backend-v9/            # FastAPI backend
  ├── app/
  │   ├── routers/
  │   │   ├── merchants.py     # GET /v1/merchants/{id}
  │   │   └── wallet.py        # POST /v1/wallet/pass/activate
  │   ├── services/
  │   │   ├── merchant_details.py
  │   │   ├── wallet_activate.py
  │   │   └── google_places_new.py  # MOCK_PLACES support
  │   ├── schemas/
  │   │   ├── merchants.py
  │   │   └── wallet.py
  │   └── models/
  │       └── wallet_pass.py   # WalletPassActivation model
  └── alembic/versions/
      └── 047_add_wallet_pass_states.py
/e2e/                          # Playwright E2E tests
```

## Troubleshooting

### Backend: "Module not found" errors

Run migrations:
```bash
cd nerava-backend-v9
alembic upgrade head
```

### Frontend: "Cannot find module" errors

Install dependencies:
```bash
cd nerava-ui
npm install
```

### E2E: "No merchants found"

- Ensure `MOCK_PLACES=true` is set in backend environment
- Check backend is running on port 8001
- Verify test coordinates (30.2672, -97.7431) match mock merchant locations

### E2E: Geolocation errors

- Tests automatically grant geolocation permissions
- Mock geolocation is set in Playwright config
- Check browser console for detailed errors

## Next Steps

1. **Run migrations**: `cd nerava-backend-v9 && alembic upgrade head`
2. **Start backend**: `export MOCK_PLACES=true && python -m uvicorn app.main_simple:app --port 8001`
3. **Start frontend**: `cd nerava-ui && npm run dev`
4. **Open browser**: `http://localhost:5173/wyc`
5. **Run E2E**: `cd e2e && npm test`

## Notes

- `/ui-mobile` remains unchanged (old frontend)
- New frontend is completely separate in `/nerava-ui`
- All tests use `MOCK_PLACES=true` for deterministic behavior
- No maps or infinite scroll in new UI (per design requirements)




