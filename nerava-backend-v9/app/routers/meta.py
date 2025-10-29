from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter(tags=["meta"])

@router.get("/health")
def health():
    """Basic health check endpoint"""
    return {"ok": True}

@router.get("/version")
def version():
    """Get version info"""
    git_sha = os.getenv("GIT_SHA", "dev")
    build_time = os.getenv("BUILD_TIME", datetime.utcnow().isoformat())
    return {
        "git_sha": git_sha,
        "build_time": build_time
    }

@router.get("/debug")
def debug():
    """Minimal environment snapshot (safe for debugging)"""
    return {
        "python_version": os.sys.version.split()[0],
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./nerava.db").split("//")[0] + "//***",  # Hide credentials
        "region": os.getenv("REGION", "local"),
        "timestamp": datetime.utcnow().isoformat()
    }

