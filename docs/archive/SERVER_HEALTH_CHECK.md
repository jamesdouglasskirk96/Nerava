# Server Health Check & Test Commands

## ✅ Server Status
The server is **RUNNING** and responding:
```bash
curl http://localhost:8001/health
# Returns: {"ok":true}
```

## ❌ Current Issue
Both `/v1/auth/register` and `/v1/auth/login` are returning **500 Internal Server Error**.

The actual error details should be visible in your **server terminal logs** (where uvicorn is running).

## 🔍 Debug Steps

### 1. Check Server Logs
Look at the terminal where you started the server (`uvicorn app.main_simple:app --port 8001 --reload`) for the actual error traceback.

### 2. Test Health Endpoint
```bash
curl http://localhost:8001/health
# Should return: {"ok":true}
```

### 3. Test Nearby Merchants (After Login Works)
Once you can login successfully, test the nearby merchants API:

```bash
# First, login and save cookie
curl -X POST "http://localhost:8001/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"your-email@example.com","password":"your-password"}'

# Then test nearby merchants
curl -X GET "http://localhost:8001/v1/drivers/merchants/nearby?lat=30.4021&lng=-97.7266&zone_slug=domain_austin&radius_m=5000" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -v
```

## 🐛 Common Issues

1. **Database not migrated**: Run `alembic upgrade head` in the backend directory
2. **Missing user**: User doesn't exist in database - need to register first
3. **Password mismatch**: Wrong password
4. **Server not reloaded**: Changes haven't taken effect - check server logs for reload messages

## 📝 Next Steps

1. Check your server terminal logs for the actual error
2. If you see specific error messages, share them and I can help fix them
3. Once login works, we can test the nearby merchants endpoint

