# Test User for Admin Portal Search

## Quick Test User

Based on the admin portal code, you can search for users by:
- **Email** (e.g., `test@example.com` or just `test`)
- **Public ID** (e.g., `user-123` or just `user`)
- **Name** (if available)

## Example Search Terms

Try these search queries in the admin portal at `http://localhost/admin/users`:

1. **Email search**: `test` or `@example.com`
2. **Partial match**: `user` or `admin`
3. **Public ID**: If you know a user's public_id, search for part of it

## Creating a Test User

### Via Driver App OTP Flow:
1. Go to `http://localhost/app/`
2. Enter a phone number (e.g., `+15551234567`)
3. Complete OTP verification
4. This creates a user you can then search for

### Via API (if registration endpoint exists):
```bash
# Check if registration endpoint exists
curl -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@nerava.com", "password": "demo123"}'
```

## Admin Portal Search Behavior

- **Case-insensitive**: `TEST` and `test` return same results
- **Partial matching**: Searching `test` will find `test@example.com`
- **Multiple fields**: Searches across email, public_id, and name simultaneously
- **Limit**: Returns up to 50 most recent users

## If No Users Found

If you get "No users found", you may need to:
1. Create a user first via the driver app OTP flow
2. Or check if the database has been initialized with seed data
3. Or create a user directly via database if you have access

## Testing the Search

1. Navigate to `http://localhost/admin/users`
2. Enter any search term in the search box
3. Results appear as you type (debounced)
4. Click on a user to see details and wallet information




