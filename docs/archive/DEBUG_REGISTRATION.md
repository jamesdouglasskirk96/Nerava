# Debug Registration Error

The registration endpoint is returning a 500 error. Here's how to debug:

## Check if user already exists

```bash
curl -X GET "http://localhost:8001/v1/auth/me" \
  -H "Cookie: access_token=<your-token>" \
  -v
```

## Try with a fresh email

```bash
curl -X POST "http://localhost:8001/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser'$(date +%s)'@test.com","password":"test123","display_name":"Test","role":"driver"}' \
  -v
```

## Check server logs

Look at the terminal where uvicorn is running for the actual error message.

## Common Issues

1. **User already exists**: Try a different email
2. **Database migration not run**: Run `alembic upgrade head`
3. **Missing table**: Check if `driver_wallets` table exists
4. **Database connection issue**: Check database URL in config

## Alternative: Use legacy registration endpoint

```bash
curl -X POST "http://localhost:8001/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"test123"}'
```

