"""
Tests for EV Arrival Code Checkin flow (V0).

Unit tests for the checkin service that don't require full app startup.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.checkin_service import CheckinService, CODE_TTL_MINUTES, CHARGER_RADIUS_M
from app.models.arrival_session import ArrivalSession


class TestCheckinServiceUnit:
    """Unit tests for CheckinService methods."""

    @pytest.fixture
    def service(self):
        """Create checkin service instance."""
        return CheckinService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        return db

    def test_generate_arrival_code_format(self, service, mock_db):
        """Test that generated codes follow the NVR-XXXX format."""
        code = service.generate_arrival_code(mock_db)

        assert code.startswith("NVR-")
        assert len(code) >= 8  # NVR-XXXX
        # Check that suffix uses valid characters
        suffix = code[4:]
        valid_chars = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
        for char in suffix:
            assert char in valid_chars, f"Invalid character '{char}' in code"

    def test_generate_arrival_code_uniqueness(self, service, mock_db):
        """Test that generated codes are unique."""
        codes = set()
        for _ in range(100):
            code = service.generate_arrival_code(mock_db)
            assert code not in codes, "Generated duplicate code"
            codes.add(code)

    def test_generate_pairing_token(self, service):
        """Test pairing token generation."""
        token1 = service.generate_pairing_token()
        token2 = service.generate_pairing_token()

        assert len(token1) > 20
        assert token1 != token2

    def test_mask_phone_full_number(self, service):
        """Test phone masking with full US number."""
        assert service.mask_phone("+15125551234") == "(512) ***-1234"

    def test_mask_phone_without_country_code(self, service):
        """Test phone masking without country code."""
        assert service.mask_phone("5125551234") == "(512) ***-1234"

    def test_mask_phone_empty(self, service):
        """Test phone masking with empty string."""
        assert service.mask_phone("") == "***"

    def test_mask_phone_short(self, service):
        """Test phone masking with short number."""
        assert service.mask_phone("1234") == "***-1234"


class TestStartCheckin:
    """Tests for starting a checkin session."""

    @pytest.fixture
    def service(self):
        return CheckinService()

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.all.return_value = []
        db.query.return_value.limit.return_value.all.return_value = []
        return db

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = 1001
        user.phone = "+15125551234"
        return user

    @pytest.fixture
    def mock_charger(self):
        charger = MagicMock()
        charger.id = "charger-001"
        charger.lat = 29.4241
        charger.lng = -98.4936
        charger.name = "Test Charger"
        return charger

    @pytest.mark.asyncio
    async def test_start_checkin_authenticated(self, service, mock_db, mock_user, mock_charger):
        """Test starting checkin as authenticated user."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_charger

        with patch.object(service, '_get_nearby_merchants', return_value=[]):
            with patch('app.services.checkin_service.settings') as mock_settings:
                mock_settings.PUBLIC_BASE_URL = "https://app.nerava.network"

                session, pairing_required, pairing_url, nearby = await service.start_checkin(
                    db=mock_db,
                    lat=29.4241,
                    lng=-98.4936,
                    accuracy_m=10.0,
                    user=mock_user,
                    charger_id=mock_charger.id,
                    ev_browser_info={"browser_source": "tesla_browser", "brand": "Tesla"},
                    idempotency_key=None,
                )

        assert session is not None
        assert session.driver_id == mock_user.id
        assert session.flow_type == "arrival_code"
        assert session.status == "pending_verification"
        assert pairing_required is False
        assert pairing_url is None
        assert session.browser_source == "tesla_browser"
        assert session.ev_brand == "Tesla"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_start_checkin_unauthenticated(self, service, mock_db, mock_charger):
        """Test starting checkin without authentication."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_charger

        with patch.object(service, '_get_nearby_merchants', return_value=[]):
            with patch('app.services.checkin_service.settings') as mock_settings:
                mock_settings.PUBLIC_BASE_URL = "https://app.nerava.network"

                session, pairing_required, pairing_url, nearby = await service.start_checkin(
                    db=mock_db,
                    lat=29.4241,
                    lng=-98.4936,
                    accuracy_m=10.0,
                    user=None,
                    charger_id=mock_charger.id,
                    ev_browser_info={"browser_source": "tesla_browser", "brand": "Tesla"},
                    idempotency_key=None,
                )

        assert session is not None
        assert session.driver_id is None
        assert session.status == "pending_pairing"
        assert pairing_required is True
        assert pairing_url is not None
        assert session.pairing_token is not None
        assert "/pair?token=" in pairing_url

    @pytest.mark.asyncio
    async def test_start_checkin_idempotent(self, service, mock_db, mock_user, mock_charger):
        """Test idempotency of checkin start."""
        idempotency_key = f"test-{uuid.uuid4()}"

        # Create existing session for idempotency
        existing_session = MagicMock()
        existing_session.id = uuid.uuid4()
        existing_session.charger_id = mock_charger.id
        existing_session.driver_id = mock_user.id
        existing_session.paired_at = None
        existing_session.pairing_token = None

        mock_db.query.return_value.filter.return_value.first.return_value = existing_session

        with patch.object(service, '_get_nearby_merchants', return_value=[]):
            session, _, _, _ = await service.start_checkin(
                db=mock_db,
                lat=29.4241,
                lng=-98.4936,
                accuracy_m=10.0,
                user=mock_user,
                charger_id=mock_charger.id,
                ev_browser_info={},
                idempotency_key=idempotency_key,
            )

        assert session.id == existing_session.id
        # No new session should be added
        mock_db.add.assert_not_called()


class TestVerifyCheckin:
    """Tests for checkin verification."""

    @pytest.fixture
    def service(self):
        return CheckinService()

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        return db

    @pytest.fixture
    def mock_charger(self):
        charger = MagicMock()
        charger.id = "charger-001"
        charger.lat = 29.4241
        charger.lng = -98.4936
        return charger

    @pytest.fixture
    def pending_session(self, mock_charger):
        session = MagicMock(spec=ArrivalSession)
        session.id = uuid.uuid4()
        session.status = "pending_verification"
        session.charger_id = mock_charger.id
        session.verification_attempts = 0
        session.verified_at = None
        return session

    @pytest.mark.asyncio
    async def test_verify_browser_geofence_success(
        self, service, mock_db, pending_session, mock_charger
    ):
        """Test successful browser geofence verification."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_charger

        verified, error = await service.verify_checkin(
            db=mock_db,
            session=pending_session,
            method="browser_geofence",
            lat=29.4241,  # Same as charger
            lng=-98.4936,
            qr_payload=None,
        )

        assert verified is True
        assert error is None
        assert pending_session.status == "verified"
        assert pending_session.verification_method == "browser_geofence"

    @pytest.mark.asyncio
    async def test_verify_browser_geofence_too_far(
        self, service, mock_db, pending_session, mock_charger
    ):
        """Test browser geofence verification fails when too far."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_charger

        verified, error = await service.verify_checkin(
            db=mock_db,
            session=pending_session,
            method="browser_geofence",
            lat=29.5,  # ~8+ km away
            lng=-98.5,
            qr_payload=None,
        )

        assert verified is False
        assert error is not None
        assert "Too far" in error or "max" in error

    @pytest.mark.asyncio
    async def test_verify_qr_scan_success(
        self, service, mock_db, pending_session, mock_charger
    ):
        """Test successful QR scan verification."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_charger

        verified, error = await service.verify_checkin(
            db=mock_db,
            session=pending_session,
            method="qr_scan",
            lat=None,
            lng=None,
            qr_payload=mock_charger.id,
        )

        assert verified is True
        assert error is None
        assert pending_session.verification_method == "qr_scan"

    @pytest.mark.asyncio
    async def test_verify_rate_limited(
        self, service, mock_db, pending_session, mock_charger
    ):
        """Test verification rate limiting."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_charger
        pending_session.verification_attempts = 11  # Over limit

        verified, error = await service.verify_checkin(
            db=mock_db,
            session=pending_session,
            method="browser_geofence",
            lat=29.5,
            lng=-98.5,
            qr_payload=None,
        )

        assert verified is False
        assert "Too many" in error

    @pytest.mark.asyncio
    async def test_verify_already_verified(
        self, service, mock_db, pending_session
    ):
        """Test verification when already verified returns true."""
        pending_session.verified_at = datetime.utcnow()

        verified, error = await service.verify_checkin(
            db=mock_db,
            session=pending_session,
            method="browser_geofence",
            lat=29.4241,
            lng=-98.4936,
            qr_payload=None,
        )

        assert verified is True
        assert error is None


class TestGenerateCode:
    """Tests for code generation."""

    @pytest.fixture
    def service(self):
        return CheckinService()

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    @pytest.fixture
    def verified_session(self):
        session = MagicMock(spec=ArrivalSession)
        session.id = uuid.uuid4()
        session.status = "verified"
        session.charger_id = "charger-001"
        session.arrival_code = None
        session.arrival_lat = 29.4241
        session.arrival_lng = -98.4936
        return session

    @pytest.mark.asyncio
    async def test_generate_code_success(self, service, mock_db, verified_session):
        """Test successful code generation."""
        with patch.object(service, '_get_nearby_merchants', return_value=[]):
            session, nearby = await service.generate_code(
                db=mock_db,
                session=verified_session,
                merchant_id=None,
            )

        assert session.arrival_code is not None
        assert session.arrival_code.startswith("NVR-")
        assert session.status == "code_generated"
        assert session.arrival_code_expires_at > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_generate_code_idempotent(self, service, mock_db, verified_session):
        """Test code generation is idempotent."""
        verified_session.arrival_code = "NVR-TEST"
        verified_session.arrival_code_expires_at = datetime.utcnow() + timedelta(minutes=30)

        with patch.object(service, '_get_nearby_merchants', return_value=[]):
            session, _ = await service.generate_code(
                db=mock_db,
                session=verified_session,
                merchant_id=None,
            )

        assert session.arrival_code == "NVR-TEST"

    @pytest.mark.asyncio
    async def test_generate_code_not_verified_fails(self, service, mock_db):
        """Test that unverified session cannot generate code."""
        session = MagicMock(spec=ArrivalSession)
        session.status = "pending_verification"
        session.arrival_code = None

        with pytest.raises(ValueError, match="must be verified"):
            await service.generate_code(
                db=mock_db,
                session=session,
                merchant_id=None,
            )


class TestRedeemCode:
    """Tests for code redemption."""

    @pytest.fixture
    def service(self):
        return CheckinService()

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        return db

    @pytest.fixture
    def code_session(self):
        session = MagicMock(spec=ArrivalSession)
        session.id = uuid.uuid4()
        session.arrival_code = "NVR-TEST"
        session.arrival_code_expires_at = datetime.utcnow() + timedelta(minutes=30)
        session.arrival_code_redeemed_at = None
        session.arrival_code_redemption_count = 0
        return session

    @pytest.mark.asyncio
    async def test_redeem_code_success(self, service, mock_db, code_session):
        """Test successful code redemption."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = code_session

        session, already_redeemed, error = await service.redeem_code(
            db=mock_db,
            code="NVR-TEST",
            order_number="ORDER-123",
            order_total_cents=2500,
        )

        assert session is not None
        assert already_redeemed is False
        assert error is None
        assert code_session.status == "code_redeemed"
        assert code_session.order_number == "ORDER-123"
        assert code_session.order_total_cents == 2500

    @pytest.mark.asyncio
    async def test_redeem_code_already_redeemed(self, service, mock_db, code_session):
        """Test that already redeemed code returns already_redeemed=True."""
        code_session.arrival_code_redeemed_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = code_session

        session, already_redeemed, error = await service.redeem_code(
            db=mock_db,
            code="NVR-TEST",
        )

        assert already_redeemed is True

    @pytest.mark.asyncio
    async def test_redeem_code_expired(self, service, mock_db, code_session):
        """Test that expired codes cannot be redeemed."""
        code_session.arrival_code_expires_at = datetime.utcnow() - timedelta(minutes=1)
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = code_session

        session, already_redeemed, error = await service.redeem_code(
            db=mock_db,
            code="NVR-TEST",
        )

        assert error is not None
        assert "expired" in error.lower()

    @pytest.mark.asyncio
    async def test_redeem_code_not_found(self, service, mock_db):
        """Test redemption of non-existent code."""
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None

        session, already_redeemed, error = await service.redeem_code(
            db=mock_db,
            code="NVR-XXXX",
        )

        assert session is None
        assert error is not None


class TestMerchantConfirm:
    """Tests for merchant confirmation."""

    @pytest.fixture
    def service(self):
        return CheckinService()

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    @pytest.fixture
    def redeemed_session(self):
        session = MagicMock(spec=ArrivalSession)
        session.id = uuid.uuid4()
        session.arrival_code = "NVR-TEST"
        session.status = "code_redeemed"
        session.platform_fee_bps = 500
        session.merchant_id = "merchant-001"
        session.order_total_cents = 2500
        session.total_source = "driver_reported"
        return session

    @pytest.mark.asyncio
    async def test_merchant_confirm_creates_billing(self, service, mock_db, redeemed_session):
        """Test that merchant confirmation creates billing event."""
        mock_db.query.return_value.filter.return_value.first.return_value = redeemed_session

        session, billing_event, error = await service.merchant_confirm(
            db=mock_db,
            code="NVR-TEST",
            order_total_cents=2500,
        )

        assert session is not None
        assert session.status == "merchant_confirmed"
        # Verify billing event was created
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_merchant_confirm_idempotent(self, service, mock_db, redeemed_session):
        """Test that merchant confirmation is idempotent."""
        redeemed_session.status = "merchant_confirmed"

        # Mock existing billing event
        existing_billing = MagicMock()
        existing_billing.id = uuid.uuid4()

        def query_filter(model_class):
            mock_query = MagicMock()
            if hasattr(model_class, '__tablename__') and model_class.__tablename__ == 'billing_events':
                mock_query.filter.return_value.first.return_value = existing_billing
            else:
                mock_query.filter.return_value.first.return_value = redeemed_session
                mock_query.filter.return_value.like.return_value = MagicMock()
            return mock_query

        mock_db.query.side_effect = query_filter

        session, billing_event, _ = await service.merchant_confirm(
            db=mock_db,
            code="NVR-TEST",
            order_total_cents=3000,  # Different amount
        )

        assert session.id == redeemed_session.id

    @pytest.mark.asyncio
    async def test_merchant_confirm_by_session_id(self, service, mock_db, redeemed_session):
        """Test merchant confirmation by session ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = redeemed_session

        session, billing_event, error = await service.merchant_confirm(
            db=mock_db,
            session_id=str(redeemed_session.id),
            order_total_cents=3000,
        )

        assert session is not None
        assert session.status == "merchant_confirmed"


class TestBillingCalculation:
    """Tests for billing fee calculation."""

    def test_billing_min_fee(self):
        """Test minimum fee of $0.50."""
        # For a $5 order at 5%, fee would be $0.25
        # But minimum is $0.50
        total = 500
        fee_bps = 500
        billable = (total * fee_bps) // 10000
        billable = max(50, min(500, billable))
        assert billable == 50  # Minimum

    def test_billing_normal_fee(self):
        """Test normal fee calculation."""
        # For a $30 order at 5%, fee is $1.50
        total = 3000
        fee_bps = 500
        billable = (total * fee_bps) // 10000
        billable = max(50, min(500, billable))
        assert billable == 150

    def test_billing_max_fee(self):
        """Test maximum fee of $5.00."""
        # For a $200 order at 5%, fee would be $10
        # But maximum is $5.00
        total = 20000
        fee_bps = 500
        billable = (total * fee_bps) // 10000
        billable = max(50, min(500, billable))
        assert billable == 500  # Maximum


class TestEVBrowserDetection:
    """Tests for EV browser detection integration."""

    def test_tesla_browser_detection(self):
        """Test Tesla browser user agent detection."""
        from app.utils.ev_browser import detect_ev_browser

        user_agent = "Mozilla/5.0 (X11; GNU/Linux) AppleWebKit/537.36 Chrome/80.0.3987.149 Safari/537.36 Tesla/2024.44.6"
        info = detect_ev_browser(user_agent)

        assert info.is_ev_browser is True
        assert info.brand == "Tesla"
        assert info.firmware_version == "2024.44.6"

    def test_non_tesla_browser(self):
        """Test non-Tesla browser detection."""
        from app.utils.ev_browser import detect_ev_browser

        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/605.1.15"
        info = detect_ev_browser(user_agent)

        assert info.is_ev_browser is False
        assert info.brand is None

    def test_android_automotive_detection(self):
        """Test Android Automotive browser detection."""
        from app.utils.ev_browser import detect_ev_browser

        user_agent = "Mozilla/5.0 (Linux; Android Automotive 13) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        info = detect_ev_browser(user_agent)

        assert info.is_ev_browser is True
        assert info.brand == "Android Automotive"


class TestGeofenceVerification:
    """Tests for geofence distance calculation."""

    def test_haversine_same_point(self):
        """Test haversine with same point returns 0."""
        from app.services.geo import haversine_m

        distance = haversine_m(29.4241, -98.4936, 29.4241, -98.4936)
        assert distance < 1  # Should be essentially 0

    def test_haversine_known_distance(self):
        """Test haversine with known distance."""
        from app.services.geo import haversine_m

        # San Antonio to Austin is ~120km
        # Using approximate coordinates
        sa_lat, sa_lng = 29.4241, -98.4936
        austin_lat, austin_lng = 30.2672, -97.7431

        distance = haversine_m(sa_lat, sa_lng, austin_lat, austin_lng)
        # Should be approximately 120km (120000m)
        assert 100000 < distance < 140000

    def test_within_charger_radius(self):
        """Test point within charger radius."""
        from app.services.geo import haversine_m

        charger_lat, charger_lng = 29.4241, -98.4936
        # Point ~100m away
        nearby_lat, nearby_lng = 29.4250, -98.4936

        distance = haversine_m(charger_lat, charger_lng, nearby_lat, nearby_lng)
        assert distance < CHARGER_RADIUS_M  # 250m radius


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
