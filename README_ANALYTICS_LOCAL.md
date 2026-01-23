# Local PostHog Analytics Setup Guide

This guide explains how to set up and use the local PostHog analytics instance for development.

## Overview

The Nerava monorepo includes a self-hosted PostHog instance running in Docker Compose. This allows you to track analytics events locally without sending data to PostHog Cloud.

## Architecture

- **PostHog UI**: Accessible at http://localhost:8080 (or http://localhost/ph via nginx proxy)
- **PostHog Service**: Runs on port 8000 internally, exposed on 8080
- **PostgreSQL**: Database for PostHog data
- **Redis**: Cache for PostHog

## Initial Setup

### Step 1: Start PostHog Services

Start the PostHog infrastructure services:

```bash
docker compose up -d posthog-db posthog-redis posthog
```

Wait for PostHog to be healthy (check logs):

```bash
docker compose logs -f posthog
```

Look for messages indicating PostHog is ready. This may take 1-2 minutes on first startup.

### Step 2: Access PostHog UI

Open your browser and navigate to:

- **Direct access**: http://localhost:8080
- **Via nginx proxy**: http://localhost/ph

### Step 3: Create Admin User

On first access, PostHog will prompt you to create an admin user:

1. Enter your email address
2. Create a password
3. Complete the setup wizard

### Step 4: Create or Select Project

1. If prompted, create a new project (or use the default project)
2. Note the **Project API Key** - you'll need this in the next step

### Step 5: Configure Environment Variables

Set the PostHog API key in your environment. You can do this in two ways:

**Option A: Using .env file (recommended)**

Create or update `.env` in the project root:

```bash
POSTHOG_KEY=your_project_api_key_here
POSTHOG_HOST=http://localhost:8080
POSTHOG_ENABLED=true
```

**Option B: Export environment variables**

```bash
export POSTHOG_KEY=your_project_api_key_here
export POSTHOG_HOST=http://localhost:8080
export POSTHOG_ENABLED=true
```

### Step 6: Restart Services

Rebuild and restart all services to pick up the new environment variables:

```bash
docker compose down
docker compose up --build
```

## Verification Checklist

Once everything is set up, verify that analytics are working:

### 1. Open PostHog Live Events

- Navigate to http://localhost:8080 (or http://localhost/ph)
- Go to **Activity** → **Live Events** (or use the search bar)
- You should see a live event stream

### 2. Test Driver App Events

1. Navigate to the driver app: http://localhost/app/
2. Perform the following actions and verify events appear in PostHog:

   - **Activate Exclusive**: Click "Activate Exclusive" button
     - Expected event: `driver_activate_exclusive_clicked`
   
   - **Send Code**: Enter phone number and click "Send code"
     - Expected event: `driver_otp_send_code_clicked`
   
   - **Confirm & Activate**: Enter OTP and click "Confirm & Activate"
     - Expected event: `driver_otp_verify_clicked`
   
   - **Get Directions**: Click "Get Directions" button
     - Expected event: `driver_get_directions_clicked`
   
   - **I'm at the Merchant**: Click "I'm at the Merchant" button
     - Expected event: `driver_im_at_merchant_clicked`
   
   - **Done** (Arrival): Click "Done" in arrival confirmation modal
     - Expected event: `driver_arrival_done_clicked`
   
   - **Done** (Preferences): Open preferences modal and click "Done"
     - Expected event: `driver_preferences_done_clicked`

### 3. Verify Event Properties

Click on any event in PostHog to see its properties. Each event should include:

- `merchant_id` (when applicable)
- `path` (current page path)
- `app` (should be "driver")
- `env` (should be "dev" in local development)
- `ts` (timestamp)

## Debugging

### Enable Debug Logging

To see analytics events in the browser console, set:

```bash
VITE_ANALYTICS_DEBUG=true
```

Then rebuild the app:

```bash
docker compose up --build driver
```

You'll see console logs like:

```
[Analytics] PostHog initialized { appName: 'driver', anonId: '...', host: '...' }
[Analytics] Event captured driver_activate_exclusive_clicked { ... }
```

### Check PostHog Logs

```bash
docker compose logs posthog
```

### Check PostHog Health

```bash
curl http://localhost:8080/_health
```

Should return a healthy status.

### Verify CORS

If events aren't appearing, check the browser console for CORS errors. PostHog should accept requests from `http://localhost` and `http://localhost:80`.

### Common Issues

**Issue: PostHog UI not loading**

- Check if PostHog service is healthy: `docker compose ps`
- Check logs: `docker compose logs posthog`
- Verify port 8080 is not in use: `lsof -i :8080`

**Issue: Events not appearing**

- Verify `POSTHOG_KEY` is set correctly
- Check `POSTHOG_ENABLED=true` is set
- Verify `POSTHOG_HOST=http://localhost:8080` matches your setup
- Check browser console for errors
- Verify PostHog is receiving requests: Check Network tab in browser dev tools

**Issue: Database connection errors**

- Ensure `posthog-db` service is running: `docker compose ps posthog-db`
- Check database logs: `docker compose logs posthog-db`
- Verify environment variables match between services

**Issue: Redis connection errors**

- Ensure `posthog-redis` service is running: `docker compose ps posthog-redis`
- Check Redis logs: `docker compose logs posthog-redis`

## Event Naming Convention

All driver app events use snake_case format:

- `driver_activate_exclusive_clicked`
- `driver_otp_send_code_clicked`
- `driver_otp_verify_clicked`
- `driver_get_directions_clicked`
- `driver_im_at_merchant_clicked`
- `driver_arrival_done_clicked`
- `driver_exclusive_done_clicked`
- `driver_preferences_done_clicked`

## Production Considerations

⚠️ **Important**: This setup is for **local development only**. 

For production:

1. Do NOT enable PostHog by default - require explicit opt-in via environment variables
2. Use PostHog Cloud or a properly secured self-hosted instance
3. Set `POSTHOG_ENABLED=false` in production unless explicitly enabled
4. Use secure `POSTHOG_SECRET_KEY` and database passwords
5. Configure proper CORS and security headers

## Stopping PostHog

To stop PostHog services:

```bash
docker compose stop posthog posthog-db posthog-redis
```

To remove PostHog data (⚠️ this deletes all analytics data):

```bash
docker compose down -v posthog-db
```

## Additional Resources

- [PostHog Documentation](https://posthog.com/docs)
- [PostHog Self-Hosting Guide](https://posthog.com/docs/self-host)
- [PostHog JavaScript SDK](https://posthog.com/docs/integrate/client/js)




