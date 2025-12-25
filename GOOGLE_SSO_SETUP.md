# Google SSO Setup Guide

This guide will walk you through setting up Google Sign-In for your Nerava application.

## Prerequisites

- A Google account
- Access to Google Cloud Console
- Your backend server running
- Your frontend application running

## Step 1: Create Google Cloud Project and OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project** (or select existing)
   - Click the project dropdown at the top
   - Click "New Project"
   - Enter project name: `Nerava` (or your preferred name)
   - Click "Create"

3. **Enable Google Identity Services API**
   - In the left sidebar, go to "APIs & Services" > "Library"
   - Search for "Google Identity Services API"
   - Click on it and click "Enable"

4. **Create OAuth 2.0 Client ID**
   - Go to "APIs & Services" > "Credentials"
   - Click "+ CREATE CREDENTIALS" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen first:
     - User Type: Choose "External" (unless you have a Google Workspace)
     - App name: `Nerava`
     - User support email: Your email
     - Developer contact: Your email
     - Click "Save and Continue"
     - Scopes: Click "Save and Continue" (default scopes are fine)
     - Test users: Add your email, click "Save and Continue"
     - Click "Back to Dashboard"

5. **Create OAuth Client ID**
   - Application type: Select "Web application"
   - Name: `Nerava Web Client`
   - **Authorized JavaScript origins:**
     - Add: `http://localhost:8001`
     - Add: `http://127.0.0.1:8001`
     - Add your production domain if applicable (e.g., `https://yourdomain.com`)
   - **Authorized redirect URIs:**
     - Add: `http://localhost:8001/app`
     - Add: `http://127.0.0.1:8001/app`
     - Add your production redirect URI if applicable
   - Click "Create"

6. **Copy Your Client ID**
   - A popup will show your Client ID (looks like: `123456789-abcdefghijklmnop.apps.googleusercontent.com`)
   - **Copy this Client ID** - you'll need it for both frontend and backend

## Step 2: Configure Frontend (Browser)

1. **Open your browser's Developer Console**
   - Navigate to: `http://127.0.0.1:8001/app/#/login`
   - Press `F12` to open DevTools
   - Go to the "Console" tab

2. **Set the Google Client ID in localStorage**
   ```javascript
   localStorage.setItem('GOOGLE_CLIENT_ID', 'YOUR_CLIENT_ID_HERE');
   ```
   Replace `YOUR_CLIENT_ID_HERE` with the Client ID you copied from Google Cloud Console.

3. **Verify it's set**
   ```javascript
   localStorage.getItem('GOOGLE_CLIENT_ID');
   ```
   This should return your Client ID.

4. **Refresh the page**
   - Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac) for a hard refresh
   - The Google Sign-In button should now work without errors

## Step 3: Configure Backend

1. **Set Environment Variable**
   
   **Option A: Using .env file** (Recommended for local development)
   - Create or edit `.env` file in your `nerava-backend-v9` directory
   - Add this line:
     ```
     GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
     ```
   - Replace `YOUR_CLIENT_ID_HERE` with your actual Client ID
   - Make sure `.env` is in `.gitignore` (don't commit secrets!)

   **Option B: Export environment variable** (Linux/Mac)
   ```bash
   export GOOGLE_CLIENT_ID="YOUR_CLIENT_ID_HERE"
   ```

   **Option C: Set in Windows Command Prompt**
   ```cmd
   set GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
   ```

   **Option D: Set in Windows PowerShell**
   ```powershell
   $env:GOOGLE_CLIENT_ID="YOUR_CLIENT_ID_HERE"
   ```

2. **Install Google Auth Library** (if not already installed)
   ```bash
   cd nerava-backend-v9
   pip install google-auth
   ```

3. **Restart Your Backend Server**
   - Stop your backend server (Ctrl+C)
   - Start it again so it picks up the new environment variable
   - Verify the environment variable is loaded:
     ```python
     # In Python shell or add to your startup logs
     from app.core.config import settings
     print(f"Google Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...")
     ```

## Step 4: Test the Flow

1. **Open the Login Page**
   - Navigate to: `http://127.0.0.1:8001/app/#/login`
   - You should see the login page with "Continue with Google" button

2. **Click "Continue with Google"**
   - A Google Sign-In popup should appear
   - Sign in with your Google account
   - Grant permissions if prompted

3. **Verify Success**
   - After signing in, you should be redirected to the wallet page
   - Check the browser console for success messages
   - Check the backend logs for authentication success

## Troubleshooting

### Error: "The given client ID is not found"
- **Cause**: Client ID is incorrect or not set properly
- **Fix**: 
  - Verify the Client ID in Google Cloud Console
  - Check localStorage: `localStorage.getItem('GOOGLE_CLIENT_ID')`
  - Ensure backend has `GOOGLE_CLIENT_ID` environment variable set
  - Restart both frontend and backend

### Error: "Redirect URI mismatch"
- **Cause**: The redirect URI in your code doesn't match what's configured in Google Cloud Console
- **Fix**: 
  - Go to Google Cloud Console > Credentials > Your OAuth Client
  - Add the exact redirect URI you're using
  - For local dev, ensure `http://localhost:8001` and `http://127.0.0.1:8001` are both added

### Error: "403 Forbidden" from Google
- **Cause**: OAuth consent screen not configured or app not verified
- **Fix**: 
  - Complete the OAuth consent screen setup in Google Cloud Console
  - Add your email as a test user
  - For production, you'll need to verify your app with Google

### Error: "Google authentication library not installed"
- **Cause**: `google-auth` Python package not installed
- **Fix**: 
  ```bash
  pip install google-auth
  ```

### Error: "Token audience mismatch"
- **Cause**: Frontend and backend are using different Client IDs
- **Fix**: 
  - Ensure both use the EXACT same Client ID
  - Check frontend: `localStorage.getItem('GOOGLE_CLIENT_ID')`
  - Check backend: `echo $GOOGLE_CLIENT_ID` (or check your .env file)

### Login page not showing
- **Cause**: CSS or routing issues
- **Fix**: 
  - Hard refresh: `Ctrl+Shift+R` or `Cmd+Shift+R`
  - Check browser console for errors
  - Verify you're navigating to `#/login` hash route

## Important Notes

1. **Same Client ID**: The frontend and backend MUST use the EXACT same Google Client ID. This is critical for token verification.

2. **Authorized Origins**: Make sure all your development and production URLs are added to "Authorized JavaScript origins" in Google Cloud Console.

3. **Security**: Never commit your Client ID to version control if it's sensitive. Use environment variables and `.env` files (which should be in `.gitignore`).

4. **Production**: For production deployment:
   - Add your production domain to authorized origins
   - Set up proper OAuth consent screen
   - Consider app verification for better user trust
   - Use environment variables or secrets management for Client ID

## Quick Reference

**Frontend Setup:**
```javascript
localStorage.setItem('GOOGLE_CLIENT_ID', 'your-client-id-here');
```

**Backend Setup:**
```bash
export GOOGLE_CLIENT_ID="your-client-id-here"
# or add to .env file
```

**Verify Setup:**
- Frontend: `localStorage.getItem('GOOGLE_CLIENT_ID')`
- Backend: Check environment variable or config

## Next Steps

Once Google Sign-In is working:
1. Test with different Google accounts
2. Verify user creation in your database
3. Test token refresh flow
4. Set up Apple Sign-In (similar process)
5. Configure production OAuth settings


