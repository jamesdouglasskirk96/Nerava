# Railway Deployment Instructions

## Important Configuration

Railway needs to be configured with:
1. **Root Directory**: `nerava-backend-v9/`
2. **No Custom Start Command**: Leave start command empty to use Procfile

## Steps to Fix "cd could not be found" Error

1. Go to Railway Dashboard → Your Service → Settings
2. Under "Service Settings", find "Root Directory"
3. Set Root Directory to: `nerava-backend-v9/`
4. Under "Deploy" or "Start Command", ensure it's **EMPTY** (delete any custom command)
5. Railway will automatically use `nerava-backend-v9/Procfile` which contains:
   ```
   web: uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}
   ```

## After First Deploy

Run migrations manually via Railway shell:
```bash
alembic upgrade head
```

## Verify Configuration

- ✅ Root Directory: `nerava-backend-v9/`
- ✅ Start Command: (empty - uses Procfile)
- ✅ Procfile exists at: `nerava-backend-v9/Procfile`

