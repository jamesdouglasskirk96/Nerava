# Magic-Link 500 Error Fix

## Issue
Getting 500 Internal Server Error when requesting a magic link.

## Fixes Applied

1. **Fixed Indentation Error**: The `try/except` block had incorrect indentation - fixed
2. **Added Error Handling**: Wrapped the entire endpoint in try/except to catch and log actual errors
3. **Added `auth_provider` Field**: User model requires `auth_provider` field (has default, but explicit is safer)
4. **Updated FRONTEND_URL Default**: Changed from `http://localhost:3000` to `http://localhost:8001` to match the actual frontend

## Next Steps

1. **Check Backend Terminal**: The server should have auto-reloaded. Look at the backend terminal output to see the actual error message (it will be logged with full traceback)

2. **Test Again**: Try entering your email again in the frontend

3. **If Still Failing**: The error logs in the backend terminal will show the exact issue (database error, missing field, etc.)

## Common Issues

- **Database not initialized**: Run migrations if needed
- **Missing table**: Check if `users` and `user_preferences` tables exist
- **Import error**: Check if all dependencies are installed (`python-jose`, etc.)

The error handling will now show the exact error in the backend logs.

