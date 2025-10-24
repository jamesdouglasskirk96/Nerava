"""
Tests for demo tour functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.routers.demo import run_tour
from app.models_demo import DemoState
from sqlalchemy.orm import Session

@pytest.fixture
def mock_db_session():
    mock_session = MagicMock(spec=Session)
    with patch('app.routers.demo.get_db', return_value=iter([mock_session])):
        yield mock_session

def test_run_tour_success(mock_db_session):
    """Test successful tour execution."""
    # Mock scenario states
    states = [
        DemoState(key="grid_state", value="peak"),
        DemoState(key="merchant_shift", value="A_dominates"),
        DemoState(key="rep_profile", value="high"),
        DemoState(key="city", value="austin")
    ]
    mock_db_session.query.return_value.all.return_value = states
    
    result = run_tour()
    
    assert "steps" in result
    assert "artifacts" in result
    assert len(result["steps"]) == 6  # 6 tour steps
    assert result["artifacts"]["city_impact"] is not None
    assert result["artifacts"]["behavior_cloud"] is not None
    assert result["artifacts"]["merchant_intel"] is not None

def test_run_tour_with_defaults(mock_db_session):
    """Test tour execution with default scenario states."""
    mock_db_session.query.return_value.all.return_value = []
    
    result = run_tour()
    
    assert "steps" in result
    assert "artifacts" in result
    # Should still work with default states
    assert len(result["steps"]) == 6

def test_run_tour_step_validation(mock_db_session):
    """Test that tour steps contain required fields."""
    mock_db_session.query.return_value.all.return_value = []
    
    result = run_tour()
    
    for step in result["steps"]:
        assert "title" in step
        assert "endpoint" in step
        assert "description" in step
        assert "expected_response" in step

def test_run_tour_robustness(mock_db_session):
    """Test tour never raises and has proper structure."""
    mock_db_session.query.return_value.all.return_value = []
    
    result = run_tour()
    
    # Tour should never raise
    assert result is not None
    assert "steps" in result
    assert "artifacts" in result
    
    # Steps array should have at least 8 steps
    assert len(result["steps"]) >= 8
    
    # Each step should have ms > 0
    for step in result["steps"]:
        assert step["ms"] > 0
    
    # Artifact directory should exist
    if "artifact_dir" in result:
        import os
        assert os.path.exists(result["artifact_dir"])
