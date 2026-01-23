# Admin Portal Functionality Test Guide

## Overview
The admin portal provides four main pages for managing the Nerava platform:
1. **Users** - Search users, view wallet details, adjust balances
2. **Merchants** - Search merchants, view merchant status
3. **Locations** - Map merchants to Google Places
4. **Demo** - Set demo location override for testing

## Fixes Applied

### 1. API Endpoint Paths
- **Issue**: Direct API calls in `Users.tsx` and `Locations.tsx` were missing `/api` prefix
- **Fix**: Updated all endpoints to use `/api/v1/admin/...` instead of `/v1/admin/...`
- **Files Changed**:
  - `apps/admin/src/pages/Users.tsx` - Fixed 3 API calls
  - `apps/admin/src/pages/Locations.tsx` - Fixed 3 API calls

### 2. Token Storage Consistency
- **Issue**: Mixed usage of `admin_token` and `access_token` in localStorage
- **Fix**: Unified to use `access_token` with fallback to `admin_token` for backward compatibility
- **Files Changed**:
  - `apps/admin/src/pages/Users.tsx` - Updated token retrieval
  - `apps/admin/src/pages/Locations.tsx` - Updated token retrieval

## Functionality Tests

### 1. Users Page (`/admin/users`)

**Features:**
- Search users by email, name, or public_id
- View user details (email, public_id, roles)
- View wallet balance and Nova balance
- View recent transactions
- Adjust wallet balance (credit/debit)

**Test Steps:**
1. Navigate to `http://localhost/admin/users`
2. Enter a search query (e.g., `test`, `@example.com`, or a user's public_id)
3. Click on a user from search results
4. Verify user details and wallet information display
5. Click "Adjust Wallet" button
6. Enter amount (positive for credit, negative for debit) and reason
7. Submit and verify wallet updates

**API Endpoints Used:**
- `GET /api/v1/admin/users?query={query}` - Search users
- `GET /api/v1/admin/users/{userId}/wallet` - Get user wallet
- `POST /api/v1/admin/users/{userId}/wallet/adjust` - Adjust wallet

### 2. Merchants Page (`/admin/merchants`)

**Features:**
- Search merchants by name or ID
- View merchant status
- View Square integration status
- View Nova balance

**Test Steps:**
1. Navigate to `http://localhost/admin/merchants`
2. Enter a search query (e.g., merchant name)
3. Click on a merchant from search results
4. Verify merchant status displays:
   - Merchant name and ID
   - Status (active/inactive)
   - Square connection status
   - Last Square error (if any)
   - Nova balance

**API Endpoints Used:**
- `GET /api/v1/admin/merchants?query={query}` - Search merchants (via `searchMerchants` service)
- `GET /api/v1/admin/merchants/{merchantId}/status` - Get merchant status (via `getMerchantStatus` service)

### 3. Locations Page (`/admin/locations`)

**Features:**
- Search merchants
- View Google Places candidates for a merchant
- Resolve Google Place ID for a merchant

**Test Steps:**
1. Navigate to `http://localhost/admin/locations`
2. Enter a merchant search query
3. Click on a merchant
4. Verify Google Places candidates load
5. Click "Resolve" on a candidate to map it to the merchant
6. Verify success message appears

**API Endpoints Used:**
- `GET /api/v1/admin/merchants?query={query}` - Search merchants
- `GET /api/v1/admin/locations/{merchantId}/google-place/candidates` - Get Google Places candidates
- `POST /api/v1/admin/locations/{merchantId}/google-place/resolve` - Resolve Google Place ID

### 4. Demo Page (`/admin/demo`)

**Features:**
- Set static demo location (latitude, longitude)
- Optionally set charger ID
- Used for testing driver app without real geolocation

**Test Steps:**
1. Navigate to `http://localhost/admin/demo`
2. Enter latitude (default: 30.2672)
3. Enter longitude (default: -97.7431)
4. Optionally enter charger ID
5. Click "Set Demo Location"
6. Verify success message appears
7. Test driver app to verify location is set

**API Endpoints Used:**
- `POST /api/v1/admin/demo/location` - Set demo location (via `setDemoLocation` service)

**Note:** Requires `DEMO_STATIC_DRIVER_ENABLED=true` environment variable in backend.

## Authentication

The admin portal requires authentication. You may need to:

1. **Set admin token** in browser console:
   ```javascript
   localStorage.setItem('access_token', 'your-admin-token-here')
   ```

2. **Or use admin login** (if implemented):
   - Navigate to admin login page
   - Enter admin credentials
   - Token will be stored automatically

## API Base URL Configuration

The admin portal uses:
- **API Base URL**: `/api` (configured via `VITE_API_BASE_URL=/api` in Docker build)
- **Full endpoint format**: `/api/v1/admin/{endpoint}`

## Common Issues and Solutions

### Issue: "Unauthorized" errors
**Solution**: Set admin token in localStorage or configure admin authentication

### Issue: API calls return 404
**Solution**: Verify endpoints use `/api/v1/admin/...` format (not `/v1/admin/...`)

### Issue: CORS errors
**Solution**: Verify nginx proxy is correctly routing `/api/*` to backend

### Issue: Demo location not working
**Solution**: Ensure `DEMO_STATIC_DRIVER_ENABLED=true` is set in backend environment

## Status

✅ **All API endpoint paths fixed**
✅ **Token storage unified**
✅ **All pages should now work correctly**

## Next Steps

1. Test each page functionality
2. Verify API endpoints are accessible
3. Test with actual data (users, merchants)
4. Verify authentication flow works




