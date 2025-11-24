"""
Run Alembic migrations programmatically.

This module can be called before uvicorn starts to ensure the database schema
is up to date. Safe to call multiple times - Alembic will be a no-op if already at head.
"""
from pathlib import Path
import logging
import sys

from alembic import command
from alembic.config import Config
import os

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """
    Run Alembic migrations up to head using the current DATABASE_URL.
    This should be safe to call on startup; Alembic will be a no-op if already at head.
    """
    # Resolve alembic.ini relative to project root
    # This file is at: nerava-backend-v9/app/run_migrations.py
    # alembic.ini is at: nerava-backend-v9/alembic.ini
    # So we need to go up 2 levels from this file
    project_root = Path(__file__).resolve().parents[1]
    alembic_ini = project_root / "alembic.ini"

    if not alembic_ini.exists():
        logger.error(f"Alembic config not found at {alembic_ini}")
        raise FileNotFoundError(f"Alembic config not found at {alembic_ini}")

    cfg = Config(str(alembic_ini))
    
    # Get DATABASE_URL from environment (matches how the app uses it)
    database_url = os.getenv("DATABASE_URL", "sqlite:///./nerava.db")
    
    # Force URL from runtime environment (overrides alembic.ini default)
    cfg.set_main_option("sqlalchemy.url", database_url)

    logger.info(f"Running Alembic migrations to head on {database_url.split('@')[-1] if '@' in database_url else database_url}")
    try:
        command.upgrade(cfg, "head")
        logger.info("Alembic migrations complete.")
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )
    try:
        run_migrations()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}", exc_info=True)
        sys.exit(1)

