# Integration Test Notes

This document provides guidance for testing the Driver app integration with the backend.

## Environment Setup

### `.env.local` Example

Create a `.env.local` file in the `nerava-ui` directory:

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_MOCK_MODE=false
```

**Note:** 
- Set `VITE_MOCK_MODE=true` to use mock data (for UI development/testing)
- Set `VITE_MOCK_MODE=false` to use real backend API calls (default)

## Running the Application

### 1. Start Backend

```bash
cd nerava-backend-v9
uvicorn app.main:app --reload
```

The backend should start on `http://localhost:8001`

### 2. Start UI

```bash
cd nerava-ui
npm install  # If not already done
npm run dev
```

The UI should start on `http://localhost:5173` (or another port if 5173 is taken)

## Testing Checklist

### OTP Authentication

1. **Start OTP Flow:**
   - Navigate to a merchant detail modal
   - Click "Activate Exclusive"
   - Enter a 10-digit phone number (e.g., `555-123-4567`)
   - Click "Send code"
   - Verify: Modal transitions to OTP input screen
   - Verify: Backend receives `POST /v1/auth/otp/start` request

2. **Verify OTP:**
   - Enter the 6-digit code received via SMS
   - Click "Confirm & Activate" (or wait for auto-submit)
   - Verify: Tokens are stored in `localStorage` (`access_token`, `refresh_token`)
   - Verify: Modal closes and exclusive activates
   - Verify: Backend receives `POST /v1/auth/otp/verify` request

3. **Error Cases:**
   - **Invalid phone:** Enter < 10 digits → Should show "Please enter a valid 10-digit phone number"
   - **Wrong code:** Enter incorrect code → Should show "Incorrect code. Please try again."
   - **Rate limit:** Send multiple requests quickly → Should show "Too many requests. Please try again in a moment."
   - **Network error:** Disconnect network → Should show "Network error. Please check your connection and try again."

### Intent Capture

1. **Location Permission:**
   - On app load, browser should request location permission
   - Grant permission → Should see "Finding nearby experiences..."
   - Deny permission → Should show friendly CTA to enable location

2. **Intent Capture Call:**
   - After location is obtained, verify in browser console:
     - `POST /v1/intent/capture` is called with `{ lat, lng, accuracy_m, client_ts }`
     - Response includes `session_id`, `merchants`, and optionally `charger_summary`
   - Verify: `session_id` is stored in DriverSession context

3. **UI Updates:**
   - **PRE_CHARGING state:** Should show charger card with nearby experiences
   - **CHARGING_ACTIVE state:** Should show merchant carousel
   - Verify: Merchants display with correct names, categories, distances, photos
   - Verify: Charger displays with name, distance, network name

4. **Empty States:**
   - If no merchants returned → Should show "No nearby experiences found yet."
   - If location error → Should show appropriate error message

### State Transitions

1. **PRE_CHARGING → CHARGING_ACTIVE:**
   - Click toggle button in header
   - Verify: UI switches from charger card to merchant carousel
   - Verify: Headline changes to "What to do while you charge"
   - Verify: Subheadline changes to "Curated access, active while charging"

2. **CHARGING_ACTIVE → EXCLUSIVE_ACTIVE:**
   - Click on a merchant with Exclusive badge
   - Click "Activate Exclusive" (after OTP if not authenticated)
   - Verify: UI switches to `ExclusiveActiveView`
   - Verify: Countdown timer shows minutes remaining
   - Verify: Backend receives `POST /v1/wallet/pass/activate` request

3. **EXCLUSIVE_ACTIVE → CHARGING_ACTIVE:**
   - Click "Done" after completing exclusive
   - Verify: Returns to merchant carousel
   - Verify: Exclusive state is cleared

### Token Refresh

1. **Automatic Refresh:**
   - Make an API call that returns 401
   - Verify: `POST /auth/refresh` is called automatically
   - Verify: New tokens are stored
   - Verify: Original request is retried successfully

2. **Refresh Failure:**
   - Use an invalid refresh token
   - Verify: Tokens are cleared from localStorage
   - Verify: Next protected action shows OTP modal

## Dev Console Logging

Open browser DevTools Console and look for "Nerava Integration" group:

```
Nerava Integration
  Mock mode: false
  API base URL: http://localhost:8001
  Location permission: granted
  Location fix: located
  Coordinates: { lat: 30.2672, lng: -97.7431, ... }
  App charging state: PRE_CHARGING
  Session ID: abc123...
  Intent capture loading: false
  Intent data: { session_id: "...", merchants: [...], ... }
```

## Troubleshooting

### Location Not Working

- Check browser console for geolocation errors
- Verify HTTPS or localhost (geolocation requires secure context)
- Check browser permissions in settings

### API Calls Failing

- Verify backend is running on correct port
- Check `VITE_API_BASE_URL` matches backend URL
- Check CORS settings in backend
- Verify tokens are present in localStorage

### Mock Mode Still Active

- Verify `.env.local` has `VITE_MOCK_MODE=false`
- Restart dev server after changing env vars
- Check browser console for "Mock mode: false"

### Type Errors

- Run `npm run build` to check TypeScript errors
- Ensure all imports are correct
- Check that types match backend schemas

## Next Steps

After verifying all tests pass:

1. Test on mobile device (if applicable)
2. Test with real phone numbers (SMS delivery)
3. Test with various location scenarios (urban, suburban, rural)
4. Test edge cases (no merchants, no charger, expired sessions)
5. Performance testing (large merchant lists, slow network)

