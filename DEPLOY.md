# Nerava Deployment Guide

## Quick Start

### Environment Variables
Copy `ENV.example` to `.env` and configure:
- Square API keys
- Database URL
- Public base URL
- CORS allowed origins

### Local Development
```bash
cd nerava-backend-v9/server
python -m uvicorn main_simple:app --port 8001 --reload
```

### Production with Gunicorn
```bash
gunicorn main_simple:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Deployment Platforms

### Render
1. Connect GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: Use Procfile
4. Add environment variables from `.env`

### Fly.io
```bash
flyctl launch
flyctl deploy
```

### Railway
1. Connect GitHub repository
2. Railway auto-detects `Procfile`
3. Add environment variables

## Health Check
- Endpoint: `GET /health`
- Returns: `{"ok": true}`

## Database Migrations
Migrations run automatically on server startup.

## PWA Features
- Service Worker with offline support
- Cache busting with version numbers
- Network-first strategy for API calls



