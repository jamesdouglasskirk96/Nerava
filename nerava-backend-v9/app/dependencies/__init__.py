"""
FastAPI dependencies for database sessions and other common dependencies.
"""
from sqlalchemy.orm import Session
from ..db import SessionLocal

def get_db():
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


