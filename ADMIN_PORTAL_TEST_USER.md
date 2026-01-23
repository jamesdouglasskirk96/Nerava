# Admin Portal Test User Guide

## User Search Functionality

The admin portal allows searching for users by:
- **Email address** (partial matches supported)
- **Public ID** (partial matches supported)  
- **Name** (if available, partial matches supported)

## How to Search

1. Navigate to `http://localhost/admin/` or `http://localhost/admin/users`
2. Enter a search query in the search box
3. Results will appear below as you type

## Creating a Test User

To create a test user for searching, you can:

### Option 1: Via OTP Flow (Recommended)
1. Use the driver app at `http://localhost/app/`
2. Complete the OTP authentication flow with a phone number
3. This will create a user in the database
4. Search for the user in admin portal using the phone number or email (if provided)

### Option 2: Direct Database Query
If you have database access, you can query users directly:
```sql
SELECT id, email, phone, public_id FROM users LIMIT 10;
```

### Option 3: API Endpoint
Create a user via the registration endpoint:
```bash
curl -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

## Example Search Queries

Once you have users in the database, try searching for:
- Email addresses: `test@example.com` or just `test`
- Phone numbers: `+1555` or `1555`
- Public IDs: Partial matches work, e.g., `user-` or `usr`

## Notes

- The search is case-insensitive
- Partial matches are supported (uses `ILIKE` with `%query%`)
- Results are limited to 50 users
- Results are ordered by creation date (newest first)

## Admin Authentication

Note: The admin portal requires authentication. You may need to:
1. Set an admin token in localStorage: `localStorage.setItem('admin_token', 'your-token')`
2. Or configure admin authentication in the backend




