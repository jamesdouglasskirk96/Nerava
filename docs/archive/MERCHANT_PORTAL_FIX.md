# Merchant Portal Dashboard Fix

## Issue
Merchant portal dashboard was not loading properly when accessed via `/merchant/` route through Docker Compose proxy, preventing demo navigation from working.

## Root Cause
React Router's `BrowserRouter` was missing the `basename` prop. When the app is served from `/merchant/` prefix, React Router needs to know about this base path to correctly match routes and handle navigation.

## Solution
Added `basename` prop to `BrowserRouter` using Vite's built-in `BASE_URL` environment variable:

```tsx
// apps/merchant/app/App.tsx
const basename = import.meta.env.BASE_URL || '/merchant'
<BrowserRouter basename={basename}>
```

`import.meta.env.BASE_URL` is automatically provided by Vite based on the `base` configuration in `vite.config.ts`, which is set to `/merchant/` during Docker build via `VITE_PUBLIC_BASE=/merchant/`.

## Demo Navigation Features
The merchant portal includes a `DemoNav` component that provides:
- **FLOW A - Onboarding**: Claim Business, Select Location
- **FLOW B - Dashboard**: Overview, Exclusives, Create Exclusive, Primary Experience, Pickup Packages, Billing, Settings
- **FLOW G - Staff View**: Customer Exclusive Screen

The demo navigation:
- Shows current route path
- Allows quick navigation between demo flows
- Handles business claim state for dashboard routes
- Provides "Reset Demo" functionality

## Files Changed
- `apps/merchant/app/App.tsx` - Added `basename` prop to `BrowserRouter`

## Verification
1. Rebuild merchant container: `docker compose build merchant --no-cache`
2. Restart merchant service: `docker compose up -d merchant`
3. Access portal at: `http://localhost/merchant/`
4. Verify demo navigation bar appears at top
5. Test navigation to dashboard routes:
   - `/merchant/overview` - Dashboard Overview
   - `/merchant/exclusives` - Exclusives list
   - `/merchant/exclusives/new` - Create Exclusive
   - `/merchant/primary-experience` - Primary Experience
   - `/merchant/pickup-packages` - Pickup Packages
   - `/merchant/billing` - Billing
   - `/merchant/settings` - Settings

## Status
✅ **FIXED** - Merchant portal dashboard should now load and demo navigation should work correctly when accessed via `/merchant/`




