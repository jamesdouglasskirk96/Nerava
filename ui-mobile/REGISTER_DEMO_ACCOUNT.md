# Register Demo Account

Since the frontend currently uses real authentication, you'll need to create an account via the API before using the demo mode.

## Quick Registration via curl

```bash
# Replace with your backend URL (local or production)
BACKEND_URL="http://127.0.0.1:8001"  # or your Railway/production URL

# Register a new driver account
curl -X POST "${BACKEND_URL}/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@test.com",
    "password": "demo123",
    "display_name": "Demo User",
    "role": "driver"
  }'
```

This will return:
```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

## Then in the Frontend

1. Open the PWA in your browser
2. Enable demo mode: Add `?demo=1` to the URL or run `localStorage.setItem('nerava_demo', '1')` in console
3. The frontend should prompt for login/registration
4. **For now, you'll need to log in via the browser's Network tab or use the login endpoint:**

```bash
# Login to get a session cookie
curl -X POST "${BACKEND_URL}/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "demo@test.com",
    "password": "demo123"
  }'
```

## Quick Test Script

Save this as `register-and-login.sh`:

```bash
#!/bin/bash
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8001}"
EMAIL="demo@test.com"
PASSWORD="demo123"

echo "Registering account..."
REGISTER_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\",
    \"display_name\": \"Demo User\",
    \"role\": \"driver\"
  }")

echo "Register response: $REGISTER_RESPONSE"

echo ""
echo "Login to get session cookie..."
LOGIN_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d "{
    \"email\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\"
  }")

echo "Login response: $LOGIN_RESPONSE"
echo ""
echo "✅ Account created! Now open the PWA and:"
echo "   1. Add ?demo=1 to the URL"
echo "   2. The demo should auto-run after login"
```

## Future: Frontend Registration UI

**Note:** The frontend currently doesn't have a registration UI. The old SSO overlay just sets a fake email. For production, you'll want to add a proper registration form that calls `/v1/auth/register`.

## Alternative: Create via Python Script

If you want to create the account directly in the database:

```python
from app.db import get_db
from app.services.auth_service import AuthService

db = next(get_db())
user = AuthService.register_user(
    db=db,
    email="demo@test.com",
    password="demo123",
    display_name="Demo User",
    roles=["driver"]
)
print(f"Created user: {user.email} (ID: {user.id})")
```

