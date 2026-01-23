"""
Tests for Energy Reputation Tier computation.

Tests tier boundaries, progress calculation, and edge cases.
"""
import pytest
from app.services.reputation import compute_reputation


@pytest.mark.parametrize("points,expected_tier,expected_next,expected_to_next,expected_progress", [
    (0, "Bronze", "Silver", 100, 0.0),
    (50, "Bronze", "Silver", 50, 0.5),
    (99, "Bronze", "Silver", 1, pytest.approx(0.99, abs=0.001)),
    (100, "Silver", "Gold", 200, 0.0),
    (200, "Silver", "Gold", 100, 0.5),
    (299, "Silver", "Gold", 1, pytest.approx(0.995, abs=0.001)),
    (300, "Gold", "Platinum", 400, 0.0),
    (500, "Gold", "Platinum", 200, 0.5),
    (699, "Gold", "Platinum", 1, pytest.approx(0.9975, abs=0.001)),
    (700, "Platinum", None, None, 1.0),
    (1000, "Platinum", None, None, 1.0),
])
def test_tier_boundaries(points, expected_tier, expected_next, expected_to_next, expected_progress):
    """Test tier boundaries at all thresholds with correct progress values."""
    rep = compute_reputation(points)
    assert rep["tier"] == expected_tier
    assert rep["next_tier"] == expected_next
    assert rep["points_to_next"] == expected_to_next
    assert rep["points"] == points
    assert "tier_color" in rep
    assert isinstance(rep["progress_to_next"], float)
    # Use pytest.approx for float comparison (handles both exact and approximate)
    if isinstance(expected_progress, float):
        assert rep["progress_to_next"] == pytest.approx(expected_progress, abs=0.001)
    else:
        assert rep["progress_to_next"] == expected_progress


def test_progress_within_tier():
    """Test progress calculation within a tier."""
    # Silver tier: 100-299, midpoint at 200 should be 0.5
    rep = compute_reputation(200)
    assert rep["tier"] == "Silver"
    assert rep["progress_to_next"] == 0.5
    
    # Bronze tier: 0-99, at 50 should be 0.5
    rep = compute_reputation(50)
    assert rep["tier"] == "Bronze"
    assert rep["progress_to_next"] == 0.5
    
    # Gold tier: 300-699, at 500 should be 0.5
    rep = compute_reputation(500)
    assert rep["tier"] == "Gold"
    assert rep["progress_to_next"] == 0.5


def test_negative_points_clamped():
    """Test that negative points are clamped to 0."""
    rep = compute_reputation(-50)
    assert rep["points"] == 0
    assert rep["tier"] == "Bronze"
    assert rep["next_tier"] == "Silver"
    assert rep["points_to_next"] == 100
    assert rep["progress_to_next"] == 0.0


def test_platinum_progress_is_one():
    """Test that Platinum always returns progress_to_next = 1.0."""
    rep = compute_reputation(700)
    assert rep["tier"] == "Platinum"
    assert rep["progress_to_next"] == 1.0
    assert rep["next_tier"] is None
    assert rep["points_to_next"] is None
    
    # Test higher Platinum scores
    rep = compute_reputation(1000)
    assert rep["tier"] == "Platinum"
    assert rep["progress_to_next"] == 1.0
    assert rep["next_tier"] is None
    assert rep["points_to_next"] is None


def test_progress_at_tier_boundaries():
    """Test progress at exact tier boundaries (no rounding - exact float values)."""
    # At Bronze start (0)
    rep = compute_reputation(0)
    assert rep["tier"] == "Bronze"
    assert rep["progress_to_next"] == 0.0
    
    # At Bronze end (99)
    rep = compute_reputation(99)
    assert rep["tier"] == "Bronze"
    # Exact: 99/100 = 0.99 (no rounding)
    assert rep["progress_to_next"] == pytest.approx(0.99, abs=0.001)
    
    # At Silver start (100)
    rep = compute_reputation(100)
    assert rep["tier"] == "Silver"
    assert rep["progress_to_next"] == 0.0
    
    # At Silver end (299)
    rep = compute_reputation(299)
    assert rep["tier"] == "Silver"
    # Exact: (299-100)/200 = 199/200 = 0.995 (no rounding)
    assert rep["progress_to_next"] == pytest.approx(0.995, abs=0.001)
    
    # At Gold start (300)
    rep = compute_reputation(300)
    assert rep["tier"] == "Gold"
    assert rep["progress_to_next"] == 0.0
    
    # At Gold end (699)
    rep = compute_reputation(699)
    assert rep["tier"] == "Gold"
    # Exact: (699-300)/400 = 399/400 = 0.9975 (no rounding)
    assert rep["progress_to_next"] == pytest.approx(0.9975, abs=0.001)


def test_tier_colors():
    """Test that tier colors are returned correctly."""
    rep_bronze = compute_reputation(50)
    assert rep_bronze["tier_color"] == "#78716c"
    
    rep_silver = compute_reputation(150)
    assert rep_silver["tier_color"] == "#64748b"
    
    rep_gold = compute_reputation(500)
    assert rep_gold["tier_color"] == "#eab308"
    
    rep_platinum = compute_reputation(700)
    assert rep_platinum["tier_color"] == "#06b6d4"


def test_none_points_handled():
    """Test that None points are handled gracefully."""
    rep = compute_reputation(None)
    assert rep["points"] == 0
    assert rep["tier"] == "Bronze"


def test_progress_clamped_to_one():
    """Test that progress never exceeds 1.0."""
    # Test at tier boundaries and beyond
    for points in [99, 100, 299, 300, 699, 700, 1000]:
        rep = compute_reputation(points)
        assert rep["progress_to_next"] <= 1.0
        assert rep["progress_to_next"] >= 0.0

