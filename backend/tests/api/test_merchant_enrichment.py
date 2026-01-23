"""
Tests for merchant enrichment service.
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.models.while_you_charge import Merchant
from app.services.merchant_enrichment import enrich_from_google_places, refresh_open_status


@pytest.fixture
def test_merchant_with_place_id(db: Session):
    """Create a test merchant with place_id"""
    merchant = Merchant(
        id="test_merchant_enrich",
        name="Test Merchant",
        place_id="test_place_id_123",
        lat=30.2680,
        lng=-97.7435,
        category="restaurant",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@patch('app.services.merchant_enrichment.place_details')
@patch('app.services.merchant_enrichment.get_photo_url')
async def test_enrich_from_google_places(mock_get_photo, mock_place_details, db: Session, test_merchant_with_place_id):
    """Test merchant enrichment from Google Places"""
    # Mock place details response
    mock_place_details.return_value = {
        "id": "places/test_place_id_123",
        "displayName": {"text": "Test Restaurant"},
        "location": {"latitude": 30.2680, "longitude": -97.7435},
        "formattedAddress": "501 W Canyon Ridge Dr, Austin, TX 78753",
        "nationalPhoneNumber": "+15125551234",
        "websiteUri": "https://test.com",
        "rating": 4.5,
        "userRatingCount": 150,
        "priceLevel": 2,
        "businessStatus": "OPERATIONAL",
        "types": ["restaurant", "food"],
        "photos": [
            {"name": "places/test_place_id_123/photos/photo_ref_1"}
        ],
        "regularOpeningHours": {
            "periods": [
                {
                    "open": {"day": 1, "hours": 9, "minutes": 0},
                    "close": {"day": 1, "hours": 22, "minutes": 0}
                }
            ]
        }
    }
    
    # Mock photo URL
    mock_get_photo.return_value = "https://maps.googleapis.com/photo.jpg"
    
    # Enrich merchant
    success = await enrich_from_google_places(db, test_merchant_with_place_id, "test_place_id_123", force_refresh=True)
    
    assert success is True
    db.refresh(test_merchant_with_place_id)
    
    # Verify fields were updated
    assert test_merchant_with_place_id.rating == 4.5
    assert test_merchant_with_place_id.user_rating_count == 150
    assert test_merchant_with_place_id.price_level == 2
    assert test_merchant_with_place_id.business_status == "OPERATIONAL"
    assert test_merchant_with_place_id.phone == "+15125551234"
    assert test_merchant_with_place_id.website == "https://test.com"
    assert test_merchant_with_place_id.primary_photo_url is not None
    assert len(test_merchant_with_place_id.photo_urls) > 0


@patch('app.services.merchant_enrichment.get_open_status')
async def test_refresh_open_status(mock_get_status, db: Session, test_merchant_with_place_id):
    """Test open status refresh"""
    # Mock open status response
    mock_get_status.return_value = {
        "open_now": True,
        "open_until": "Open until 10:00 PM"
    }
    
    # Refresh status
    success = await refresh_open_status(db, test_merchant_with_place_id, force_refresh=True)
    
    assert success is True
    db.refresh(test_merchant_with_place_id)
    
    # Verify status was updated
    assert test_merchant_with_place_id.open_now is True
    assert test_merchant_with_place_id.last_status_check is not None



