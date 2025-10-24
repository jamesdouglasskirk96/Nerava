"""
Tests for demo state management.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.routers.demo import set_scenario, get_state
from app.models_demo import DemoState
from sqlalchemy.orm import Session

@pytest.fixture
def mock_db_session():
    mock_session = MagicMock(spec=Session)
    with patch('app.routers.demo.get_db', return_value=iter([mock_session])):
        yield mock_session

def test_set_scenario_new_key(mock_db_session):
    """Test setting a new scenario key."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    result = set_scenario("grid_state", "peak")
    
    assert result["ok"] is True
    assert result["state"]["grid_state"] == "peak"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called()

def test_set_scenario_existing_key(mock_db_session):
    """Test updating an existing scenario key."""
    existing_state = DemoState(key="grid_state", value="offpeak")
    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_state
    
    result = set_scenario("grid_state", "peak")
    
    assert result["ok"] is True
    assert result["state"]["grid_state"] == "peak"
    assert existing_state.value == "peak"
    mock_db_session.commit.assert_called()

def test_get_state_empty(mock_db_session):
    """Test getting state when no scenarios are set."""
    mock_db_session.query.return_value.all.return_value = []
    
    result = get_state()
    
    assert result["state"] == {
        "grid_state": "offpeak",
        "merchant_shift": "balanced", 
        "rep_profile": "medium",
        "city": "austin"
    }

def test_get_state_with_scenarios(mock_db_session):
    """Test getting state with existing scenarios."""
    states = [
        DemoState(key="grid_state", value="peak"),
        DemoState(key="merchant_shift", value="A_dominates")
    ]
    mock_db_session.query.return_value.all.return_value = states
    
    result = get_state()
    
    assert result["state"]["grid_state"] == "peak"
    assert result["state"]["merchant_shift"] == "A_dominates"
    assert result["state"]["rep_profile"] == "medium"  # default
    assert result["state"]["city"] == "austin"  # default
