# Health Check Failure Analysis

## Current Status
- **Service URL:** `bdna52kgup.us-east-1.awsapprunner.com`
- **Service Status:** OPERATION_IN_PROGRESS
- **Health Check Response:** HTTP 404 Not Found
- **Health Check Path:** `/healthz`
- **Port:** 8000

## Observations

### 1. Missing Application Logs
**Critical Finding:** No application logs are visible in CloudWatch, despite:
- Early startup logging code in `main_simple.py` (lines 1-50) that should print `[STARTUP]` messages
- Logging configured to `sys.stdout` which should be captured by App Runner

**Implications:**
- Application may not be starting at all
- Python process may be crashing before logging begins
- Docker container may be failing to execute the CMD

### 2. Health Check Returns 404
- **Server:** envoy (App Runner proxy)
- **Status Code:** 404 Not Found
- **Response:** Empty body

This indicates:
- ✅ App Runner proxy is running and responding
- ✅ Network connectivity works
- ❌ FastAPI application is not handling requests
- ❌ Routes are not registered (app not started or crashed)

### 3. Dockerfile Configuration
```dockerfile
CMD ["python", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Issue Identified:** The CMD uses `python` but the system may only have `python3`. However, App Runner should handle this, or the Dockerfile should specify `python3`.

### 4. Application Code
The `/healthz` endpoint exists at:
- `app/main_simple.py:616-631`
- Defined as `@app.get("/healthz")`
- Should return JSON with `{"ok": True, ...}`

## Root Cause Analysis

### Most Likely Causes:

#### 1. **Python Command Not Found** ⚠️ HIGH PROBABILITY
- Dockerfile uses `CMD ["python", ...]` 
- Container may only have `python3` available
- **Result:** Container exits immediately, no logs generated

#### 2. **Import Error During Startup** ⚠️ MEDIUM PROBABILITY  
- Application has complex import chain
- One of the imports may be failing silently
- Startup logging happens before FastAPI app creation, so if imports fail, no logs appear

#### 3. **Module Not Found** ⚠️ MEDIUM PROBABILITY
- PYTHONPATH is set to `/app`
- But module resolution might fail
- Error would occur before logging starts

#### 4. **Port Binding Issue** ⚠️ LOW PROBABILITY
- CMD specifies port 8000
- App Runner expects port 8000
- Should match, but worth verifying

### Why No Logs Appear

If the Python process fails immediately:
1. Docker CMD executes
2. `python` command not found (or import error)
3. Process exits with error code
4. Container exits
5. No stdout/stderr captured (process died too quickly)
6. App Runner keeps retrying, but container keeps dying

## Recommended Investigation Steps

### 1. Fix Dockerfile CMD (IMMEDIATE)
Change from:
```dockerfile
CMD ["python", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
```

To:
```dockerfile
CMD ["python3", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
```

Or use explicit Python path:
```dockerfile
CMD ["/usr/bin/python3", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Add Error Handling to CMD
```dockerfile
CMD ["sh", "-c", "python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 2>&1"]
```

### 3. Test Docker Image Locally
```bash
docker run -p 8000:8000 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:latest
```

This will show immediate errors that aren't appearing in CloudWatch.

### 4. Check Docker Image Base
Verify the base image has `python3` available:
```dockerfile
FROM python:3.9-slim
```
Should have both `python` and `python3`, but `python3` is more reliable.

## Conclusion

**Primary Issue:** Dockerfile CMD uses `python` instead of `python3`, causing the container to fail immediately before any logs are generated.

**Secondary Issue:** Lack of application logs suggests the container is exiting before the Python application starts, which aligns with a command not found error.

**Fix Required:** Update Dockerfile CMD to use `python3` instead of `python`.


