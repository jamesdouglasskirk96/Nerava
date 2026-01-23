# Admin Portal Fix

## Issue
Admin portal was not loading properly when accessed via `/admin/` route through Docker Compose proxy, preventing navigation between admin pages.

## Root Cause
React Router's `BrowserRouter` was missing the `basename` prop. When the app is served from `/admin/` prefix, React Router needs to know about this base path to correctly match routes and handle navigation.

## Solution
Added `basename` prop to `BrowserRouter` using Vite's built-in `BASE_URL` environment variable:

```tsx
// apps/admin/src/App.tsx
const basename = import.meta.env.BASE_URL || '/admin'
<BrowserRouter basename={basename}>
```

`import.meta.env.BASE_URL` is automatically provided by Vite based on the `base` configuration in `vite.config.ts`, which is set to `/admin/` during Docker build via `VITE_PUBLIC_BASE=/admin/`.

## Admin Portal Features
The admin portal includes the following pages:
- **Users** (`/admin/users`) - User management
- **Merchants** (`/admin/merchants`) - Merchant management
- **Locations** (`/admin/locations`) - Location management
- **Demo** (`/admin/demo`) - Demo location override for driver testing

The Demo page allows setting a static location for demo driver mode, which is useful for testing the driver app without requiring actual geolocation.

## Files Changed
- `apps/admin/src/App.tsx` - Added `basename` prop to `BrowserRouter`

## Verification
1. Rebuild admin container: `docker compose build admin --no-cache`
2. Restart admin service: `docker compose up -d admin`
3. Access portal at: `http://localhost/admin/`
4. Verify navigation works:
   - `/admin/` or `/admin/users` - Users page
   - `/admin/merchants` - Merchants page
   - `/admin/locations` - Locations page
   - `/admin/demo` - Demo location override page

## Status
✅ **FIXED** - Admin portal should now load and navigation should work correctly when accessed via `/admin/`




