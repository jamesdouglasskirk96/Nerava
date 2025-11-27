# Test Nearby Merchants API

## Endpoint
`GET /v1/drivers/merchants/nearby`

## Required Parameters
- `lat` (float): Latitude (required)
- `lng` (float): Longitude (required)
- `zone_slug` (string): Zone slug, e.g., "domain_austin" (required)
- `radius_m` (float): Radius in meters (optional, defaults to 5000)

## Authentication
This endpoint requires authentication. You must be logged in as a driver user.

---

## Quick Test (Local Backend)

### Step 1: Register a test user (if you don't have one)
```bash
curl -X POST "http://localhost:8001/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "display_name": "Test Driver",
    "role": "driver"
  }'
```

### Step 2: Login to get session cookie
```bash
curl -X POST "http://localhost:8001/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'
```

### Step 3: Call nearby merchants API
```bash
curl -X GET "http://localhost:8001/v1/drivers/merchants/nearby?lat=30.4021&lng=-97.7266&zone_slug=domain_austin&radius_m=5000" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -v
```

---

## One-liner Test (after login)

```bash
curl -X GET "http://localhost:8001/v1/drivers/merchants/nearby?lat=30.4021&lng=-97.7266&zone_slug=domain_austin&radius_m=5000" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -w "\n\nHTTP Status: %{http_code}\n"
```

---

## Test with Different Locations

### Domain Austin (default zone)
```bash
curl -X GET "http://localhost:8001/v1/drivers/merchants/nearby?lat=30.4021&lng=-97.7266&zone_slug=domain_austin" \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

### Domain Austin with custom radius
```bash
curl -X GET "http://localhost:8001/v1/drivers/merchants/nearby?lat=30.4021&lng=-97.7266&zone_slug=domain_austin&radius_m=1000" \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

---

## Test on Production (if deployed)

Replace `localhost:8001` with your production URL:

```bash
# Login
curl -X POST "https://your-production-url.com/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'

# Get nearby merchants
curl -X GET "https://your-production-url.com/v1/drivers/merchants/nearby?lat=30.4021&lng=-97.7266&zone_slug=domain_austin&radius_m=5000" \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

---

## Expected Response

The endpoint returns a list of merchants with the following shape:

```json
{
  "recommended_merchants": [
    {
      "id": "merchant-id",
      "merchant_id": "merchant-id",
      "name": "Merchant Name",
      "lat": 30.4021,
      "lng": -97.7266,
      "logo_url": "https://...",
      "category": "restaurant",
      "nova_reward": 10,
      "walk_time_s": 300,
      "distance_m": 250,
      "walk_time_minutes": 5
    }
  ],
  "chargers": [...]
}
```

---

## Troubleshooting

### 401 Unauthorized
- Make sure you've logged in and the session cookie is valid
- Check that `cookies.txt` file exists and contains a valid session cookie

### 404 Not Found
- Check that `zone_slug=domain_austin` is correct
- Verify the zone exists in the database

### 500 Internal Server Error
- Check backend logs for details
- Verify the database is accessible and migrations have been run

