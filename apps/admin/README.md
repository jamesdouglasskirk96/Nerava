# Nerava Admin UI

Minimal admin UI for Nerava backend operations.

## Setup

```bash
npm install
npm run dev
```

## Features

- User search and wallet management
- Merchant search and status
- Google Places mapping for merchant locations

## Authentication

Currently uses bearer token from localStorage. Set `admin_token` in localStorage with a valid JWT token.

For production, implement proper Google SSO or passwordless allowlist authentication.







