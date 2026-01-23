"""
Integration tests for Square merchant onboarding flow
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.square_service import SquareOAuthResult, SquareLocationStats
from app.models.domain import DomainMerchant


class TestSquareOnboardingFlow:
    """Test end-to-end Square onboarding flow"""
    
    @pytest.mark.asyncio
    async def test_square_onboarding_creates_merchant_with_perk(self, db):
        """Square onboarding should create merchant with AOV-based perk"""
        from app.services.merchant_onboarding import onboard_merchant_via_square
        from app.services.square_service import fetch_square_location_stats
        
        # Mock Square OAuth result
        square_result = SquareOAuthResult(
            merchant_id="sq_merchant_123",
            location_id="sq_location_456",
            access_token="sq_token_789"
        )
        
        # Mock location stats (AOV = $20 = 2000 cents)
        with patch('app.services.merchant_onboarding.fetch_square_location_stats') as mock_fetch:
            mock_fetch.return_value = SquareLocationStats(avg_order_value_cents=2000)
            
            merchant = await onboard_merchant_via_square(
                db=db,
                user_id=None,
                square_result=square_result
            )
            
            assert merchant is not None
            assert merchant.square_merchant_id == "sq_merchant_123"
            assert merchant.square_location_id == "sq_location_456"
            # Token should be encrypted (not equal to original)
            assert merchant.square_access_token is not None
            assert merchant.square_access_token != "sq_token_789"  # Should be encrypted
            assert merchant.square_connected_at is not None
            assert merchant.avg_order_value_cents == 2000
            assert merchant.recommended_perk_cents is not None
            assert merchant.perk_label is not None
            assert merchant.qr_token is not None
    
    @pytest.mark.asyncio
    async def test_square_onboarding_updates_existing_merchant(self, db):
        """Square onboarding should update existing merchant if square_merchant_id matches"""
        from app.services.merchant_onboarding import onboard_merchant_via_square
        
        # Create existing merchant
        existing = DomainMerchant(
            id="existing_merchant",
            name="Existing Merchant",
            lat=30.4,
            lng=-97.7,
            status="active",
            zone_slug="national",
            nova_balance=0,
            square_merchant_id="sq_merchant_123"  # Same Square merchant ID
        )
        db.add(existing)
        db.commit()
        
        # Mock Square OAuth result
        square_result = SquareOAuthResult(
            merchant_id="sq_merchant_123",
            location_id="sq_location_456",
            access_token="sq_token_789"
        )
        
        with patch('app.services.merchant_onboarding.fetch_square_location_stats') as mock_fetch:
            mock_fetch.return_value = SquareLocationStats(avg_order_value_cents=1500)
            
            merchant = await onboard_merchant_via_square(
                db=db,
                user_id=None,
                square_result=square_result
            )
            
            # Should update existing merchant
            assert merchant.id == "existing_merchant"
            # Token should be encrypted (not equal to original)
            assert merchant.square_access_token is not None
            assert merchant.square_access_token != "sq_token_789"  # Should be encrypted
            assert merchant.avg_order_value_cents == 1500
    
    def test_perk_calculation_from_aov(self, db):
        """Should calculate recommended perk as 15% of AOV, rounded appropriately"""
        from app.services.merchant_onboarding import _calculate_recommended_perk, _format_perk_label
        
        # Test various AOV values
        test_cases = [
            (1000, 150),  # $10 AOV -> $1.50 perk -> rounds to $1.50 -> min $1 = $1.50, but rounds to $2
            (1500, 300),  # $15 AOV -> $2.25 -> rounds to $2.50
            (2000, 300),  # $20 AOV -> $3.00 -> $3.00
            (5000, 500),  # $50 AOV -> $7.50 -> rounds to $7.50, but capped at $5
        ]
        
        for aov_cents, expected_perk_cents in test_cases:
            perk = _calculate_recommended_perk(aov_cents)
            # Should be at least $1 and at most $5
            assert 100 <= perk <= 500, f"AOV {aov_cents} produced perk {perk} outside bounds"
            # Should be rounded to nearest 50 cents
            assert perk % 50 == 0, f"Perk {perk} not rounded to 50 cents"
        
        # Test label formatting
        label = _format_perk_label(300)
        assert "$3" in label
        assert "off" in label.lower()

