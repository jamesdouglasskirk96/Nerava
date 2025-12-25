"""
Database configuration with lazy initialization.

The database engine is created lazily on first access to avoid blocking
during module import. This is critical for containerized deployments
where the database might not be immediately available.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from .config import settings
import sys

# Global engine instance (lazily initialized)
_engine = None
_SessionLocal = None

Base = declarative_base()


def get_engine():
    """
    Get or create the database engine (lazy initialization).

    This allows the app to start and respond to health checks
    even if the database is temporarily unavailable.
    """
    global _engine
    if _engine is None:
        print(f"[DB] Creating database engine for: {settings.database_url[:30]}...", flush=True)
        try:
            _engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
            )
            print("[DB] Database engine created successfully", flush=True)
        except Exception as e:
            print(f"[DB] ERROR creating database engine: {e}", flush=True)
            raise
    return _engine


def get_session_local():
    """Get or create the SessionLocal class."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# For backwards compatibility - SessionLocal can be imported but will create engine on first use
class SessionLocal:
    """
    Wrapper class that provides backwards-compatible SessionLocal behavior
    while using lazy engine initialization.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            session_class = get_session_local()
            return session_class()
        return cls._instance()


def get_db():
    """
    Dependency that provides a database session.
    Used by FastAPI's dependency injection.
    """
    session_class = get_session_local()
    db = session_class()
    try:
        yield db
    finally:
        db.close()


# Legacy compatibility: expose engine property for code that imports it directly
# This will trigger lazy initialization when accessed
@property
def engine():
    return get_engine()
