"""
Pytest configuration and fixtures for Nerava backend tests.

Provides test database isolation and common test utilities.
"""
import sys
import os
import pathlib
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Use in-memory SQLite for tests to ensure complete isolation
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
    echo=False  # Set to True for SQL debugging
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", help="include slow tests")


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Create and tear down test database schema once per test session.
    
    This ensures all tests run against a clean, isolated test database
    and never touch the dev/prod database.
    """
    from app.db import Base
    # Import all models to ensure they're registered with Base
    from app import models, models_extra, models_while_you_charge, models_demo
    
    # Drop all tables (in case they exist from previous test runs)
    Base.metadata.drop_all(bind=test_engine)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create chargers_openmap table if needed (used by verify_dwell service)
    with test_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chargers_openmap (
                id TEXT PRIMARY KEY,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                name TEXT
            )
        """))
        
        # Create outbox_events table if needed (used by event system)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS outbox_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type VARCHAR(100) NOT NULL,
                payload_json TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                processed_at DATETIME NULL
            )
        """))
        
        conn.commit()
    
    yield
    
    # Cleanup after all tests
    Base.metadata.drop_all(bind=test_engine)
    
    # Clean up chargers_openmap
    with test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS chargers_openmap"))
        conn.commit()


@pytest.fixture(scope="function")
def db():
    """
    Provide a clean database session for each test.
    
    Transactions are rolled back after each test to ensure
    no test data leaks between tests.
    
    Usage:
        def test_something(db: Session):
            # Use db session here
            user = User(email="test@example.com")
            db.add(user)
            db.commit()
            # Test assertions...
            # Session is automatically rolled back after test
    
    IMPORTANT: 
    - Always use this fixture instead of directly calling SessionLocal()
    - Do NOT patch SessionLocal in tests - use dependency overrides instead
    - The session is automatically rolled back, so no cleanup needed
    """
    from app.db import Base
    
    # Start a transaction
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        # Rollback transaction and close session
        # This ensures test isolation - no data persists between tests
        session.close()
        transaction.rollback()
        connection.close()


def override_get_db(db_session):
    """
    Helper function to create a dependency override for get_db.
    
    This ensures consistent dependency overriding across all tests.
    Use this in fixtures that need to override the database dependency.
    """
    def _override():
        """Override get_db to use the provided test database session."""
        yield db_session
    return _override


@pytest.fixture(scope="function")
def client(setup_test_db, db):
    """
    Provide a FastAPI TestClient with test database dependency override.
    
    All API tests will use the test database instead of the dev/prod database.
    Uses the same db session as the db fixture to ensure data consistency.
    
    IMPORTANT: This fixture overrides both app.db.get_db and app.dependencies.get_db
    to ensure compatibility with all routes.
    """
    from fastapi.testclient import TestClient
    from app.main_simple import app
    
    # Import both possible get_db locations
    from app.db import get_db as get_db_from_db
    try:
        from app.dependencies import get_db as get_db_from_deps
    except ImportError:
        get_db_from_deps = None
    
    # Create override function
    override_func = override_get_db(db)
    
    # Override both dependencies to ensure compatibility
    app.dependency_overrides[get_db_from_db] = override_func
    if get_db_from_deps:
        app.dependency_overrides[get_db_from_deps] = override_func
    
    try:
        # Set raise_server_exceptions=False so HTTPException is converted to response
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        # Clear all overrides
        app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create a test user for wallet timeline tests"""
    from app.models import User
    user = User(
        email="test@example.com",
        password_hash="hashed",
        is_active=True,
        role_flags="driver"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_merchant(db):
    """Create a test merchant for wallet timeline tests"""
    from app.models.domain import DomainMerchant
    merchant = DomainMerchant(
        id="test_merchant_123",
        name="Test Merchant",
        lat=30.4,
        lng=-97.7,
        zone_slug="test_zone",
        status="active",
        nova_balance=0
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant
