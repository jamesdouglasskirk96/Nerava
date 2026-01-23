# Docker Compose Validation Checklist

## Configuration Fixes Applied

### 1. Docker Compose Version Warning
- ✅ Removed obsolete `version: '3.8'` from docker-compose.yml

### 2. Nginx Proxy Configuration
- ✅ Fixed location order: `/health` and `/api/health` come before `/api/` and `/`
- ✅ Proxy strips `/api/` prefix correctly: `proxy_pass http://backend:8001/;`
- ✅ Proxy strips `/app/`, `/merchant/`, `/admin/` prefixes for Vite apps
- ✅ Added `/landing/health` endpoint routing

### 3. Vite Apps Nginx Configuration
- ✅ Simplified nginx configs - proxy handles prefix stripping
- ✅ Vite apps serve at root `/` inside containers
- ✅ SPA routing with `try_files $uri $uri/ /index.html;`

### 4. Base Path Configuration
- ✅ Vite apps: `base: process.env.VITE_PUBLIC_BASE || '/'` in vite.config.ts
- ✅ Next.js: `basePath: process.env.NEXT_PUBLIC_BASE_PATH || ''` in next.config.mjs
- ✅ Docker build args set correctly in docker-compose.yml

### 5. Health Endpoints
- ✅ Backend: `/health` and `/healthz` both work
- ✅ Landing: `/health` via Next.js API route
- ✅ Vite apps: `/health` via nginx location
- ✅ Proxy: `/health` returns 200

## Testing Instructions

### Step 1: Clean Slate Run

```bash
# Stop and remove everything
make down
docker system prune -f

# Build and start
make up
```

**Expected**: All containers start successfully, health checks pass.

### Step 2: Health Endpoint Validation

```bash
make health
# or
bash scripts/smoke.sh
```

**Expected Output**:
```
✅ Proxy: http://localhost/health
✅ Backend: http://localhost/api/health
✅ Landing: http://localhost/landing/health
✅ Driver: http://localhost/app/health
✅ Merchant: http://localhost/merchant/health
✅ Admin: http://localhost/admin/health
🎉 All health checks passed!
```

### Step 3: Base Path Verification

Open in browser and check DevTools → Network:

1. **Landing**: http://localhost/
   - Should load landing page
   - Assets load from `/` (no prefix)

2. **Driver**: http://localhost/app/
   - Should load driver app
   - Assets MUST load from `/app/assets/...` (check Network tab)
   - API calls MUST go to `/api/...` (not `http://localhost:8001`)

3. **Merchant**: http://localhost/merchant/
   - Should load merchant portal
   - Assets MUST load from `/merchant/assets/...`
   - API calls MUST go to `/api/...`

4. **Admin**: http://localhost/admin/
   - Should load admin portal
   - Assets MUST load from `/admin/assets/...`
   - API calls MUST go to `/api/...`

### Step 4: API Routing Rewrite Test

```bash
# Backend health (should return JSON)
curl -i http://localhost/api/health

# Should return 200 with JSON body:
# {"ok": true, "service": "nerava-backend", "version": "0.9.0", "status": "healthy"}
```

**Critical**: The `/api/` prefix is stripped, so `/api/health` → backend `/health`

### Step 5: CORS Verification

Check that no frontend code references `http://localhost:8001`:

```bash
# Search for hardcoded 8001 references (should only find dev configs, not production builds)
grep -r "8001" apps/*/dist/ 2>/dev/null || echo "No dist folders (expected - need to build first)"
```

**Expected**: No `8001` references in built assets. All API calls use `/api`.

### Step 6: SPA Routing Test

Test that client-side routing works:

1. Navigate to http://localhost/app/
2. Use the app to navigate to a different route (e.g., `/app/some-route`)
3. Refresh the page (F5)
4. **Expected**: Page still loads (not 404)

Repeat for `/merchant/` and `/admin/`.

## Known Issues & Solutions

### Issue 1: Next.js Standalone Output
**Status**: ✅ Fixed
- Dockerfile uses `output: 'standalone'` in next.config.mjs
- Copies `.next/standalone` and `.next/static` correctly

### Issue 2: Vite Base Path at Build Time
**Status**: ✅ Fixed
- Build args set in docker-compose.yml: `VITE_PUBLIC_BASE=/app/`
- vite.config.ts reads from `process.env.VITE_PUBLIC_BASE`

### Issue 3: Nginx Location Order
**Status**: ✅ Fixed
- Exact matches (`=`) come before prefix matches
- `/health` before `/`
- `/api/health` before `/api/`

### Issue 4: Proxy Prefix Stripping
**Status**: ✅ Fixed
- `/api/` → `backend:8001/` (strips `/api`)
- `/app/` → `driver:3001/` (strips `/app`)
- `/merchant/` → `merchant:3002/` (strips `/merchant`)
- `/admin/` → `admin:3003/` (strips `/admin`)

## Container Status Check

After `make up`, verify all containers are healthy:

```bash
docker compose ps
```

**Expected**: All services show `healthy` status.

## Troubleshooting

### If health checks fail:
1. Check logs: `make logs` or `docker compose logs <service>`
2. Verify ports aren't conflicting: `lsof -i :80 -i :8001 -i :3000-3003`
3. Check nginx config syntax: `docker compose exec proxy nginx -t`

### If assets don't load:
1. Check browser console for 404s
2. Verify Vite base path was set at build time (check container build logs)
3. Check Network tab - assets should request from `/app/assets/...`, not `/assets/...`

### If API calls fail:
1. Check browser console for CORS errors
2. Verify `VITE_API_BASE_URL=/api` was set at build time
3. Check backend logs: `docker compose logs backend`

## Success Criteria

✅ All containers start without errors
✅ All health endpoints return 200
✅ All 4 UIs load under their prefixes
✅ Assets load from correct base paths (`/app/assets/...`, etc.)
✅ API calls go to `/api/...` (not `localhost:8001`)
✅ SPA routing works (refresh doesn't 404)
✅ No CORS errors in browser console

## Next Steps After Validation

Once all checks pass:
1. Test golden path: Driver OTP → Intent → Exclusive → Complete
2. Test merchant toggle affects driver listing
3. Test admin demo location override

If any step fails, the setup is NOT production-ready.




