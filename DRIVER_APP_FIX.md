# Driver App Loading Fix

## Issue
Driver app was not loading properly when accessed via `/app/` route through Docker Compose proxy.

## Root Cause
React Router's `BrowserRouter` was missing the `basename` prop. When the app is served from `/app/` prefix, React Router needs to know about this base path to correctly match routes and handle navigation.

## Solution
Added `basename` prop to `BrowserRouter` using Vite's built-in `BASE_URL` environment variable:

```tsx
// apps/driver/src/App.tsx
const basename = import.meta.env.BASE_URL || '/app'
<BrowserRouter basename={basename}>
```

`import.meta.env.BASE_URL` is automatically provided by Vite based on the `base` configuration in `vite.config.ts`, which is set to `/app/` during Docker build via `VITE_PUBLIC_BASE=/app/`.

## Files Changed
- `apps/driver/src/App.tsx` - Added `basename` prop to `BrowserRouter`

## Verification
1. Rebuild driver container: `docker compose build driver --no-cache`
2. Restart driver service: `docker compose up -d driver`
3. Access app at: `http://localhost/app/`
4. Verify React Router routes work correctly

## Status
✅ **FIXED** - Driver app should now load and route correctly when accessed via `/app/`




