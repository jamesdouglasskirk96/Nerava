# Nerava Development Guide

## How to Run Server

### Prerequisites
- Python 3.8+
- SQLite (included with Python)

### Quick Start

1. **Navigate to server directory:**
   ```bash
   cd nerava-backend-v9/server
   ```

2. **Start the FastAPI server:**
   ```bash
   python -m uvicorn main_simple:app --port 8001 --reload
   ```

3. **Verify server is running:**
   ```bash
   curl http://127.0.0.1:8001/health
   ```
   Should return: `{"ok":true}`

### Server Features

- **Health Check**: `GET /health` - Returns server status
- **API Routes**: All `/v1/*` endpoints for wallet, activity, payments
- **Static Files**: Serves frontend from `ui-mobile/` directory
- **Database**: SQLite with automatic migrations
- **CORS**: Enabled for development

### Key Endpoints

- `GET /health` - Server health check
- `GET /v1/wallet/summary` - Wallet balance and transactions
- `GET /v1/activity` - User activity and reputation
- `GET /v1/square/payments/test` - Payment system test
- `POST /v1/square/checkout` - Create payment checkout

### Development Notes

- Server auto-reloads on code changes (`--reload` flag)
- Database migrations run automatically on startup
- Static files served from `../../ui-mobile` (robust path resolution)
- All routes properly imported and functional