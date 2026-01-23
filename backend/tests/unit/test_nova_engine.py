"""
Unit tests for Nova Engine - pure reward calculation logic
"""
import pytest
from datetime import datetime, time
from app.services.nova_engine import (
    is_off_peak,
    calculate_nova_for_session,
    calc_award_cents,
)


class TestIsOffPeak:
    """Test off-peak window detection"""
    
    def test_off_peak_within_window(self):
        """Session during off-peak hours should return True"""
        # Test 23:00 (11 PM) - within 22:00-06:00 window
        dt = datetime(2025, 1, 15, 23, 0, 0)
        assert is_off_peak(dt, ["22:00", "06:00"]) is True
    
    def test_off_peak_midnight_crossing(self):
        """Session at 02:00 should be off-peak (window crosses midnight)"""
        dt = datetime(2025, 1, 15, 2, 0, 0)
        assert is_off_peak(dt, ["22:00", "06:00"]) is True
    
    def test_off_peak_at_start_boundary(self):
        """Session at exactly 22:00 should be off-peak"""
        dt = datetime(2025, 1, 15, 22, 0, 0)
        assert is_off_peak(dt, ["22:00", "06:00"]) is True
    
    def test_off_peak_before_end_boundary(self):
        """Session at 05:59 should be off-peak"""
        dt = datetime(2025, 1, 15, 5, 59, 0)
        assert is_off_peak(dt, ["22:00", "06:00"]) is True
    
    def test_peak_at_end_boundary(self):
        """Session at exactly 06:00 should be peak (exclusive end)"""
        dt = datetime(2025, 1, 15, 6, 0, 0)
        assert is_off_peak(dt, ["22:00", "06:00"]) is False
    
    def test_peak_during_day(self):
        """Session during peak hours (14:00) should return False"""
        dt = datetime(2025, 1, 15, 14, 0, 0)
        assert is_off_peak(dt, ["22:00", "06:00"]) is False


class TestCalculateNovaForSession:
    """Test Nova calculation for charging sessions"""
    
    def test_off_peak_session_grants_nova(self):
        """Off-peak session should grant Nova based on rules"""
        session_time = datetime(2025, 1, 15, 23, 0, 0)  # Off-peak
        rules = [
            {
                "code": "OFF_PEAK_BASE",
                "active": True,
                "params": {"cents": 25, "window": ["22:00", "06:00"]}
            }
        ]
        
        nova = calculate_nova_for_session(
            kwh=10.5,
            duration_minutes=60,
            session_time=session_time,
            rules=rules
        )
        
        assert nova == 25  # Should grant the base reward
    
    def test_peak_session_grants_zero_nova(self):
        """Peak session should grant zero Nova"""
        session_time = datetime(2025, 1, 15, 14, 0, 0)  # Peak
        rules = [
            {
                "code": "OFF_PEAK_BASE",
                "active": True,
                "params": {"cents": 25, "window": ["22:00", "06:00"]}
            }
        ]
        
        nova = calculate_nova_for_session(
            kwh=10.5,
            duration_minutes=60,
            session_time=session_time,
            rules=rules
        )
        
        assert nova == 0  # Peak sessions get zero Nova
    
    def test_missing_kwh_returns_zero(self):
        """Missing kWh should return zero (no crash)"""
        session_time = datetime(2025, 1, 15, 23, 0, 0)
        rules = [{"code": "OFF_PEAK_BASE", "active": True, "params": {"cents": 25, "window": ["22:00", "06:00"]}}]
        
        nova = calculate_nova_for_session(
            kwh=None,  # Missing
            duration_minutes=60,
            session_time=session_time,
            rules=rules
        )
        
        assert nova == 0
    
    def test_missing_duration_returns_zero(self):
        """Missing duration should return zero (no crash)"""
        session_time = datetime(2025, 1, 15, 23, 0, 0)
        rules = [{"code": "OFF_PEAK_BASE", "active": True, "params": {"cents": 25, "window": ["22:00", "06:00"]}}]
        
        nova = calculate_nova_for_session(
            kwh=10.5,
            duration_minutes=None,  # Missing
            session_time=session_time,
            rules=rules
        )
        
        assert nova == 0
    
    def test_inactive_rule_not_applied(self):
        """Inactive rules should not grant Nova"""
        session_time = datetime(2025, 1, 15, 23, 0, 0)
        rules = [
            {
                "code": "OFF_PEAK_BASE",
                "active": False,  # Inactive
                "params": {"cents": 25, "window": ["22:00", "06:00"]}
            }
        ]
        
        nova = calculate_nova_for_session(
            kwh=10.5,
            duration_minutes=60,
            session_time=session_time,
            rules=rules
        )
        
        assert nova == 0
    
    def test_empty_rules_returns_zero(self):
        """Empty rules list should return zero"""
        session_time = datetime(2025, 1, 15, 23, 0, 0)
        
        nova = calculate_nova_for_session(
            kwh=10.5,
            duration_minutes=60,
            session_time=session_time,
            rules=[]
        )
        
        assert nova == 0


class TestCalcAwardCents:
    """Test simple time-based award calculation"""
    
    def test_off_peak_time_grants_award(self):
        """Current time during off-peak should grant award"""
        now = datetime(2025, 1, 15, 23, 0, 0)  # Off-peak
        rules = [
            {
                "code": "OFF_PEAK_BASE",
                "active": True,
                "params": {"cents": 25, "window": ["22:00", "06:00"]}
            }
        ]
        
        award = calc_award_cents(now, rules)
        assert award == 25
    
    def test_peak_time_grants_zero(self):
        """Current time during peak should grant zero"""
        now = datetime(2025, 1, 15, 14, 0, 0)  # Peak
        rules = [
            {
                "code": "OFF_PEAK_BASE",
                "active": True,
                "params": {"cents": 25, "window": ["22:00", "06:00"]}
            }
        ]
        
        award = calc_award_cents(now, rules)
        assert award == 0


