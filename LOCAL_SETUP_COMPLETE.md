# Local Development Setup - Complete ✅

## Status

**Backend:** ✅ Running on http://localhost:8001  
**Frontend:** ✅ Running on http://localhost:5173 (already started)

## Configuration

### Backend (.env)
- ✅ Created from `ENV.example`
- ✅ Added development secrets:
  - `JWT_SECRET=dev-secret-change-me`
  - `TOKEN_ENCRYPTION_KEY=IvpXa1gvJhEVbZyshHc_eqzjBm3ZrEhyox1319lmcH8=`
  - `OTP_PROVIDER=stub`
  - `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175`

### Frontend (apps/driver/.env.local)
- ✅ Updated to use local backend:
  - `VITE_API_BASE_URL=http://localhost:8001`
  - `VITE_MOCK_MODE=false`
  - `VITE_ENV=local`

### Database
- ✅ SQLite database exists with 101 tables
- ✅ Migrations at revision 054

## Access URLs

- **Backend API:** http://localhost:8001
- **API Docs (Swagger):** http://localhost:8001/docs
- **Backend Health:** http://localhost:8001/health
- **Driver App:** http://localhost:5173
- **Debug Analytics:** http://localhost:8001/debug/analytics/posthog/status (dev only)

## Running Services

### Backend
```bash
cd backend
python3 -m uvicorn app.main_simple:app --reload --port 8001
```

**Or use the startup script:**
```bash
./start-local-dev.sh
```

### Frontend (Driver App)
```bash
cd apps/driver
npm run dev
```

## Testing

### Test Backend Health
```bash
curl http://localhost:8001/health
```

### Test PostHog Debug Endpoint
```bash
curl http://localhost:8001/debug/analytics/posthog/status
```

### Test Frontend → Backend Connection
1. Open http://localhost:5173
2. Open browser DevTools → Network tab
3. Check API calls to `http://localhost:8001`

## Troubleshooting

### Backend won't start
- Check logs: `tail -f /tmp/nerava-backend-startup.log`
- Verify Python dependencies: `pip install -r backend/requirements.txt`
- Check port 8001: `lsof -ti:8001`

### Frontend won't connect to backend
- Verify `.env.local` has `VITE_API_BASE_URL=http://localhost:8001`
- Check browser console for CORS errors
- Verify backend CORS allows `http://localhost:5173`

### Port conflicts
- Backend (8001): `lsof -ti:8001 | xargs kill -9`
- Frontend (5173): `lsof -ti:5173 | xargs kill -9`

## Fixed Issues

1. ✅ Created backend `.env` file
2. ✅ Updated driver `.env.local` to use localhost
3. ✅ Fixed syntax error in `admin_domain.py` (async function)
4. ✅ Added development secrets for local dev

## Next Steps

1. Test the driver app: http://localhost:5173
2. Test API endpoints: http://localhost:8001/docs
3. Test PostHog events: Use debug endpoint to fire test events
4. Check merchant click tracking: Click merchants in the app and verify PostHog events
