# Health Check Failure - Root Cause Identified

## Root Cause

**Error:** `AttributeError: module 'app.routers.config' has no attribute 'routes'`

**Location:** `app/main_simple.py:613`

**Error Message:**
```
File "/app/app/main_simple.py", line 613, in <module>
    app.include_router(config_router)
  File "/usr/local/lib/python3.9/site-packages/fastapi/applications.py", line 462, in include_router
    self.router.include_router(
  File "/usr/local/lib/python3.9/site-packages/fastapi/routing.py", line 802, in include_router
    for r in router.routes:
AttributeError: module 'app.routers.config' has no attribute 'routes'
```

## Problem Analysis

1. **Import Statement (line 222):** In `main_simple.py`, the code imports:
   ```python
   config as config_router,
   ```
   This imports the entire `app.routers.config` **module**, not the router object.

2. **Router Definition:** The router object is defined as `router` inside `app/routers/config.py`:
   ```python
   router = APIRouter(prefix="/v1/public", tags=["config"])
   ```

3. **Usage (line 613):** When `app.include_router(config_router)` is called, FastAPI expects a router object with a `routes` attribute, but `config_router` is a module, which doesn't have a `routes` attribute.

## Why Logs Don't Appear in CloudWatch

1. The application crashes during module import/startup (line 613)
2. The error occurs **after** the startup logging code but **during** FastAPI app initialization
3. Python traceback goes to stderr, which App Runner may not capture properly
4. The container keeps crashing, so health checks fail with 404
5. App Runner retries, but the container keeps failing on startup

## Fix Required

Change line 613 in `main_simple.py` from:
```python
app.include_router(config_router)
```

To:
```python
app.include_router(config.router)
```

The import on line 222 is fine (`config as config_router`), we just need to use `config_router.router` instead of `config_router` directly.

Actually, wait - if we import `config as config_router`, then we should use `config_router.router`. But it's cleaner to just import `config` and use `config.router`.

**Recommended fix:**
- Line 222: Change `config as config_router,` to `config,`
- Line 613: Change `app.include_router(config_router)` to `app.include_router(config.router)`

## Verification

When I ran the Docker container locally:
```bash
docker run --rm -e DATABASE_URL=sqlite:///./test.db \
  566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest \
  timeout 10 python -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000
```

The exact same `AttributeError` appeared, confirming this is the root cause of the health check failures.

## Summary

✅ **Root Cause:** Importing module instead of router object, then trying to use module as router  
✅ **Impact:** Application crashes on startup, container exits, health checks fail  
✅ **Fix:** Change `app.include_router(config_router)` to `app.include_router(config.router)`  
✅ **Verification:** Reproduced locally, error matches exactly
