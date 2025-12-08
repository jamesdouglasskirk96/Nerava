# CORS Fix Applied

## Issue
The frontend app at `http://localhost:8001` was making API requests to `http://127.0.0.1:8001`, which browsers treat as different origins, causing CORS errors.

## Fix Applied
Updated `ui-mobile/js/core/api.js` to use `window.location.origin` for local development, ensuring same-origin requests.

## Next Steps
1. **Reload the browser** - The frontend JavaScript changes will take effect on page reload
2. **Check browser console** - CORS errors should be resolved
3. **Test API calls** - Endpoints should now work without CORS issues

## Note on Backend Errors
The 500 errors you're seeing are separate backend issues (likely missing data or database setup). Once CORS is fixed, you'll be able to see the actual error messages in the browser console.

## If Issues Persist
1. Hard refresh the browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
2. Clear browser cache
3. Check backend logs in the terminal for actual error messages

