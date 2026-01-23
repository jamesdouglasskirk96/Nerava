"""
Tests for Google Places API (New) client
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from app.services.google_places_new import (
    search_nearby,
    get_photo_url,
    _get_geo_cell,
    _haversine_distance,
)


class TestGooglePlacesNew:
    """Test Google Places API (New) client"""
    
    @pytest.mark.asyncio
    @patch('app.services.google_places_new.cache')
    @patch('app.services.google_places_new.httpx.AsyncClient')
    async def test_search_nearby_success(self, mock_client_class, mock_cache):
        """Test successful nearby search"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "places": [
                {
                    "id": "places/ChIJ123",
                    "displayName": {"text": "Test Restaurant"},
                    "location": {"latitude": 37.7749, "longitude": -122.4194},
                    "types": ["restaurant"],
                    "iconMaskBaseUri": "https://example.com/icon.png",
                    "photos": [{"name": "places/ChIJ123/photos/photo_ref_1"}],
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Mock cache
        mock_cache.get.return_value = None
        mock_cache.set = AsyncMock()
        
        # Mock get_photo_url
        with patch('app.services.google_places_new.get_photo_url', new_callable=AsyncMock) as mock_photo:
            mock_photo.return_value = "https://example.com/photo.jpg"
            
            results = await search_nearby(
                lat=37.7749,
                lng=-122.4194,
                radius_m=800,
                max_results=20,
            )
            
            assert len(results) > 0
            assert results[0]["name"] == "Test Restaurant"
            assert results[0]["place_id"] == "ChIJ123"
    
    @pytest.mark.asyncio
    @patch('app.services.google_places_new.cache')
    async def test_search_nearby_cache_hit(self, mock_cache):
        """Test cache hit for nearby search"""
        cached_results = [
            {
                "place_id": "ChIJ123",
                "name": "Cached Restaurant",
                "lat": 37.7749,
                "lng": -122.4194,
                "distance_m": 100,
                "types": ["restaurant"],
            }
        ]
        mock_cache.get.return_value = cached_results
        
        results = await search_nearby(
            lat=37.7749,
            lng=-122.4194,
            radius_m=800,
        )
        
        assert len(results) > 0
        assert results[0]["name"] == "Cached Restaurant"
    
    def test_get_geo_cell(self):
        """Test geo cell calculation"""
        lat, lng = _get_geo_cell(37.7749, -122.4194)
        assert isinstance(lat, float)
        assert isinstance(lng, float)
        # Should be rounded to 0.001 precision
        assert lat == round(37.7749 / 0.001) * 0.001
    
    def test_haversine_distance(self):
        """Test Haversine distance calculation"""
        distance = _haversine_distance(37.7749, -122.4194, 37.7750, -122.4195)
        assert distance > 0
        assert distance < 200  # Should be very close (<200m)



