# Fix CORS Errors - Browser Refresh Required

## The Issue
The browser has cached the old JavaScript code that was hardcoded to use `127.0.0.1:8001`. The fix is already in place, but the browser needs to reload the new code.

## Quick Fix: Hard Refresh

### Option 1: Hard Refresh (Recommended)
1. **Mac**: Press `Cmd + Shift + R`
2. **Windows/Linux**: Press `Ctrl + Shift + R`

This will force the browser to reload all JavaScript files from the server, bypassing the cache.

### Option 2: Clear Cache and Reload
1. Open Developer Tools (F12 or Cmd+Option+I)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Option 3: Disable Cache (Dev Mode)
1. Open Developer Tools (F12)
2. Go to the Network tab
3. Check "Disable cache"
4. Keep DevTools open while testing
5. Refresh the page

## After Refresh
- CORS errors should disappear
- API calls will use `localhost:8001` instead of `127.0.0.1:8001`
- You may still see 500/404 errors (those are separate backend issues)

## What Changed
The `ui-mobile/js/core/api.js` file now uses `window.location.origin` for local development, ensuring same-origin requests and avoiding CORS issues.

