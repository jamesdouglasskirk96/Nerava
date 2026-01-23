"""
Unit tests for Merchant Onboarding Service
"""
import pytest
from app.services.merchant_onboarding import (
    validate_merchant_location,
    normalize_merchant_data,
    check_duplicate_merchant,
)
from app.models.domain import Zone, DomainMerchant
from app.models import User


class TestValidateMerchantLocation:
    """Test merchant location validation"""
    
    def test_valid_location_within_zone(self, db):
        """Location within zone radius should be valid"""
        # Create test zone
        zone = Zone(
            slug="test_zone",
            name="Test Zone",
            center_lat=30.4021,
            center_lng=-97.7266,
            radius_m=1000
        )
        db.add(zone)
        db.commit()
        
        # Location close to center (within radius)
        result_zone = validate_merchant_location(
            db=db,
            zone_slug="test_zone",
            lat=30.403,  # ~100m from center
            lng=-97.727
        )
        
        assert result_zone.slug == "test_zone"
    
    def test_invalid_zone_not_found(self, db):
        """Non-existent zone should raise ValueError"""
        with pytest.raises(ValueError, match="Invalid zone"):
            validate_merchant_location(
                db=db,
                zone_slug="nonexistent_zone",
                lat=30.4,
                lng=-97.7
            )
    
    def test_location_outside_zone_raises_error(self, db):
        """Location outside zone radius should raise ValueError"""
        zone = Zone(
            slug="small_zone",
            name="Small Zone",
            center_lat=30.4021,
            center_lng=-97.7266,
            radius_m=100  # Small radius
        )
        db.add(zone)
        db.commit()
        
        # Location far from center (outside radius)
        with pytest.raises(ValueError, match="Location must be within"):
            validate_merchant_location(
                db=db,
                zone_slug="small_zone",
                lat=30.5,  # Too far
                lng=-97.8
            )


class TestNormalizeMerchantData:
    """Test merchant data normalization"""
    
    def test_normalizes_business_name(self):
        """Should normalize business name (trim whitespace)"""
        result = normalize_merchant_data(
            business_name="  Test Business  ",
            addr_line1="123 Main St",
            city="Austin",
            state="TX",
            postal_code="78701"
        )
        
        assert result["name"] == "Test Business"  # Trimmed
    
    def test_preserves_google_place_id(self):
        """Should preserve Google Place ID if provided"""
        result = normalize_merchant_data(
            business_name="Test Business",
            google_place_id="ChIJN1t_tDeuEmsRUsoyG83frY4",
            addr_line1="123 Main St",
            city="Austin",
            state="TX",
            postal_code="78701"
        )
        
        assert result["google_place_id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    
    def test_handles_none_values(self):
        """Should handle None values gracefully"""
        result = normalize_merchant_data(
            business_name="Test Business",
            google_place_id=None,
            addr_line1=None,
            city="Austin",
            state="TX",
            postal_code="78701"
        )
        
        assert result["name"] == "Test Business"
        assert result["google_place_id"] is None


class TestCheckDuplicateMerchant:
    """Test duplicate merchant detection"""
    
    def test_finds_duplicate_by_google_place_id(self, db):
        """Should find existing merchant by Google Place ID"""
        # Create existing merchant
        existing = DomainMerchant(
            id="m1",
            name="Existing Merchant",
            google_place_id="ChIJN1t_tDeuEmsRUsoyG83frY4",
            lat=30.4,
            lng=-97.7,
            zone_slug="test_zone"
        )
        db.add(existing)
        db.commit()
        
        # Check for duplicate with same Place ID
        result = check_duplicate_merchant(
            db=db,
            google_place_id="ChIJN1t_tDeuEmsRUsoyG83frY4"
        )
        
        assert result is not None
        assert result.id == "m1"
    
    def test_no_duplicate_returns_none(self, db):
        """Should return None if no duplicate found"""
        result = check_duplicate_merchant(
            db=db,
            google_place_id="new_place_id_123"
        )
        
        assert result is None
    
    def test_duplicate_by_location_and_name(self, db):
        """Should find duplicate by name and location proximity"""
        # Create existing merchant
        existing = DomainMerchant(
            id="m2",
            name="Coffee Shop",
            lat=30.4021,
            lng=-97.7266,
            zone_slug="test_zone"
        )
        db.add(existing)
        db.commit()
        
        # Check for duplicate with similar name and close location
        result = check_duplicate_merchant(
            db=db,
            name="Coffee Shop",
            lat=30.4022,  # Very close (within 100m)
            lng=-97.7267
        )
        
        assert result is not None
        assert result.name == "Coffee Shop"


