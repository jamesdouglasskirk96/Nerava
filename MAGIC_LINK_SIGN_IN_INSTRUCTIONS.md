# Magic Link Sign-In Instructions (Dev Mode)

## How to Complete Sign-In

Since you're in development mode, the magic link URL is **logged to your backend terminal** (not sent via email).

### Step 1: Find the Magic Link URL

1. **Look at your backend terminal** where you ran `uvicorn`
2. You should see a log message like:
   ```
   [Auth][MagicLink] Magic link sent: http://localhost:8001/app/#/auth/magic?token=eyJ...
   ```
   Or it might be in the email sender log output

3. **Copy the entire URL** from the terminal

### Step 2: Open the Magic Link

**Option A: Copy & Paste**
1. Copy the full URL from the backend terminal
2. Paste it into your browser's address bar
3. Press Enter

**Option B: Click if Clickable**
- Some terminals allow clicking URLs directly

### Step 3: Automatic Sign-In

Once you open the magic link:
- The frontend will automatically:
  1. Verify the token with the backend
  2. Create your session (HTTP-only cookie)
  3. Redirect you to the Wallet tab
  4. You'll be signed in! 🎉

### What the URL Looks Like

```
http://localhost:8001/app/#/auth/magic?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Troubleshooting

**If the link expired:**
- Magic links expire after 15 minutes
- Request a new one by entering your email again

**If you get an error:**
- Check the browser console (F12) for error messages
- Check the backend terminal for error logs

**Can't find the URL?**
- Look for any log lines with `[Auth][MagicLink]`
- The URL should appear right after you submit your email

