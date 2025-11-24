# Nerava Backend — Railway Deployment

## Canonical Production Entrypoint

```bash
python -m uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Railway Configuration

- **Project root**: `nerava-backend-v9`
- **Procfile**: `nerava-backend-v9/Procfile`
- **Start Command**: Leave empty in Railway UI (Railway will use the Procfile)
- **Buildpack**: Railway uses Nixpacks which auto-detects Python from `requirements.txt` and `runtime.txt`
- **Nixpacks Config**: `nixpacks.toml` explicitly defines the build process to ensure dependencies are installed
- **Build Script**: `build.sh` is included as an additional fallback to ensure dependencies are installed
- **Build Command**: Railway will use Nixpacks config first, then fall back to auto-detection or build.sh

## Database Migrations

Run manually via Railway shell:

```bash
cd nerava-backend-v9
alembic upgrade head
```

## Important Notes

- **Root-level Procfile** (`/Procfile.localdev`): This is for local/reference only and is **not used by Railway**. Railway only uses `nerava-backend-v9/Procfile`.
- **Dockerfile**: The Dockerfile in `nerava-backend-v9/` is **not used by Railway**. Railway uses Railpack + Procfile. The Dockerfile is for other container-based workflows (e.g., Docker Compose, manual Docker builds).
- **Start Command**: Do not set a custom Start Command in the Railway UI. Railway will automatically use the `web:` process from the Procfile.

## Verification

After deployment, verify the app is running:

```bash
curl https://your-railway-app.railway.app/health
```

Expected response:
```json
{"status": "ok", "db": "ok"}
```

