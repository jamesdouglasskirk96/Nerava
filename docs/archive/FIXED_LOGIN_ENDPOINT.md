# Fixed Login Endpoint

## Issue
The `/v1/auth/login` endpoint was using `OAuth2PasswordRequestForm` which expects form-encoded data (`application/x-www-form-urlencoded`), but the frontend/client is sending JSON (`application/json`).

## Fix Applied
Changed the login endpoint to accept JSON using `LoginRequest` instead of `OAuth2PasswordRequestForm`.

## Testing

### Option 1: JSON Login (Updated endpoint)
```bash
curl -X POST "http://localhost:8001/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"james@nerava.network","password":"nerava123"}'
```

### Option 2: Form-encoded (if you need OAuth2 compatibility)
```bash
curl -X POST "http://localhost:8001/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt \
  -d "username=james@nerava.network&password=nerava123"
```

## After Login - Test Nearby Merchants

```bash
curl -X GET "http://localhost:8001/v1/drivers/merchants/nearby?lat=30.4021&lng=-97.7266&zone_slug=domain_austin&radius_m=5000" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -v
```

