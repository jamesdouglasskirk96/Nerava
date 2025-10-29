web: cd nerava-backend-v9 && python -m alembic upgrade head && uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-4}

