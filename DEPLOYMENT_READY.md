# Nerava Deployment Readiness

## Summary of Changes

The Nerava app has been made deployment-ready for Render, Fly.io, Vercel, and similar platforms.

### 1. Static File Path Resolution ✅

**File**: `nerava-backend-v9/app/main_simple.py`
- **Change**: Updated UI mount path to use `Path(__file__)` for proper relative resolution
- **Before**: `os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ui-mobile"))`
- **After**: `Path(__file__).parent.parent.parent / "ui-mobile"`

This ensures the ui-mobile directory is correctly resolved regardless of where the server is run from.

### 2. CORS Configuration ✅

**Files**: 
- `nerava-backend-v9/app/config.py`
- `ENV.example`

**Changes**:
- Added `public_base_url` setting from `PUBLIC_BASE_URL` environment variable
- CORS origins now read from `ALLOWED_ORIGINS` environment variable
- Defaults to `*` for development
- Production can set specific origins like `https://nerava.com,https://app.nerava.com`

### 3. Environment Variables ✅

**Files**: `ENV.example`, `nerava-backend-v9/ENV.example`

Both files now include:
- Square API keys (`SQUARE_ACCESS_TOKEN`, etc.)
- Database URL (`DATABASE_URL`)
- Public base URL (`PUBLIC_BASE_URL`)
- CORS origins (`ALLOWED_ORIGINS`)
- Redis configuration
- Logging and request settings
- Feature flags

### 4. Service Worker Enhancements ✅

**File**: `ui-mobile/sw.js`

**Improvements**:
- Cache versioning with `v1.0.0` constant
- Proper `skipWaiting()` call in install event
- `clientsClaim()` in activate event with proper promise handling
- Offline fallback page included in cache
- Better error handling for offline scenarios
- Fallback response for navigation requests

### 5. Deployment Configuration ✅

**Files**: `Procfile`, `nerava-backend-v9/requirements.txt`, `nerava-backend-v9/runtime.txt`

**Changes**:
- Updated Procfile to run migrations on boot: `python -m alembic upgrade head`
- Added `pydantic-settings` and `alembic` to requirements.txt
- Created `runtime.txt` with Python 3.9.18
- Procfile now properly handles PORT and WEB_CONCURRENCY environment variables

### 6. Health Check Endpoints ✅

**File**: `nerava-backend-v9/app/routers/health.py`

**New Endpoints**:
- `GET /v1/health` - Basic health check
- `GET /v1/healthz` - Detailed health check with database connectivity test

The `/healthz` endpoint returns 503 if database is disconnected, making it perfect for orchestration platforms.

### 7. Service Worker Registration ✅

**File**: `ui-mobile/js/app.js`

**Changes**:
- Added service worker registration on app load
- Proper error handling
- Console logging for debugging

## Deployment Instructions

### For Render.com

1. Set environment variables in Render dashboard:
   ```bash
   DATABASE_URL=postgresql://user:pass@host/dbname
   ALLOWED_ORIGINS=https://yourdomain.com
   PUBLIC_BASE_URL=https://yourbackend.render.com
   SQUARE_ACCESS_TOKEN=your_token
   # ... other variables
   ```

2. Deploy from GitHub. Render will use the Procfile automatically.

3. The app will:
   - Run migrations on first deploy
   - Start uvicorn with 4 workers
   - Serve the UI at `/app`
   - Expose API at `/v1/`

### For Fly.io

1. Create `fly.toml`:
   ```toml
   app = "nerava"
   
   [build]
     dockerfile = "nerava-backend-v9/Dockerfile"
   
   [env]
     PORT = "8080"
     DATABASE_URL = "postgresql://..."
   
   [[services]]
     internal_port = 8080
     protocol = "tcp"
   
     [[services.ports]]
       handlers = ["http"]
       port = 80
   
     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   
     [services.concurrency]
       type = "connections"
       hard_limit = 1000
       soft_limit = 500
   
   [[services.tcp_checks]]
     interval = "15s"
     timeout = "2s"
     grace_period = "1s"
   ```

2. Deploy: `flyctl deploy`

### For Vercel

1. Create `vercel.json`:
   ```json
   {
     "buildCommand": "cd nerava-backend-v9 && pip install -r requirements.txt",
     "outputDirectory": "nerava-backend-v9",
     "rewrites": [
       { "source": "/app/(.*)", "destination": "/app/$1" },
       { "source": "/v1/(.*)", "destination": "/api/$1" }
     ]
   }
   ```

2. Note: Vercel is optimized for static sites. For production, consider Render or Fly.io for the full FastAPI app.

## Testing Deployment

### Local Testing

```bash
# Copy environment variables
cp ENV.example .env

# Edit .env with your values
nano .env

# Run migrations
cd nerava-backend-v9
python -m alembic upgrade head

# Start server
uvicorn app.main_simple:app --reload --port 8001
```

Visit:
- UI: http://localhost:8001/app/
- API: http://localhost:8001/v1/health

### Production Testing

1. Check health: `curl https://yourdomain.com/v1/health`
2. Check database connectivity: `curl https://yourdomain.com/v1/healthz`
3. Test UI: Visit `https://yourdomain.com/app/`
4. Test offline mode: Open browser DevTools > Application > Service Workers

## PWA Features Enabled

- ✅ Service Worker with caching
- ✅ Offline page fallback
- ✅ Manifest for mobile install
- ✅ Skip waiting for immediate updates
- ✅ Clients claim for instant control

## Next Steps

1. Set up CI/CD pipeline (GitHub Actions)
2. Configure custom domain
3. Enable SSL/TLS
4. Set up monitoring (Sentry, etc.)
5. Configure backups for production database

## Notes

- SQLite is fine for development but use PostgreSQL in production
- Redis is optional but recommended for caching
- Square webhooks require a publicly accessible URL
- CORS should be tightened in production (remove wildcard)
