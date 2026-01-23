"""
Integration test for EV telemetry endpoint when no vehicle is connected
"""
import pytest
from app.models import User


@pytest.fixture
def test_user_no_vehicle(db):
    """Create a test user with no vehicle account"""
    user = User(
        email="test_no_vehicle@example.com",
        password_hash="hashed_password",
        is_active=True,
        role_flags="driver"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_ev_telemetry_no_vehicle_returns_404(client, db, test_user_no_vehicle):
    """GET /v1/ev/me/telemetry/latest should return 404 when no vehicle connected"""
    from app.main_simple import app
    from app.dependencies.domain import get_current_user
    
    # Override auth dependency to return test_user
    def mock_get_current_user():
        return test_user_no_vehicle
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    try:
        response = client.get("/v1/ev/me/telemetry/latest")
        
        # Should return 404 with specific error message
        # Note: FastAPI TestClient may return 404 for HTTPException
        assert response.status_code == 404, f"Expected 404, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert "detail" in data, f"Response missing 'detail' key: {data}"
        assert "No connected vehicle found" in data["detail"], f"Unexpected detail message: {data.get('detail')}"
    finally:
        # Clear override
        app.dependency_overrides.pop(get_current_user, None)

