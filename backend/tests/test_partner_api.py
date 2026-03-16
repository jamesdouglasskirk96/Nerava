"""
End-to-end tests for the Partner Incentive API.

Tests the full flow: create partner → create API key → submit session → verify grant.
Also tests idempotency, partner session controls on campaigns, and scope enforcement.
"""
import hashlib
import uuid
from datetime import datetime, timedelta

import pytest

from app.models.user import User
from app.models.partner import Partner, PartnerAPIKey
from app.models.campaign import Campaign
from app.models.session_event import SessionEvent, IncentiveGrant
from app.services.partner_service import PartnerService
from app.services.campaign_service import CampaignService


# --- Helpers ---

def _make_admin(db):
    user = User(
        email="admin@nerava.network",
        password_hash="hashed",
        is_active=True,
        role_flags="admin",
        admin_role="super_admin",
    )
    db.add(user)
    db.flush()
    return user


def _make_partner(db, slug="evject", trust_tier=2, status="active"):
    partner = PartnerService.create_partner(
        db,
        name="EVject",
        slug=slug,
        partner_type="driver_app",
        trust_tier=trust_tier,
    )
    partner.status = status
    db.commit()
    db.refresh(partner)
    return partner


def _make_api_key(db, partner_id, scopes=None):
    api_key, plaintext = PartnerService.create_api_key(
        db,
        partner_id=partner_id,
        name="Test Key",
        scopes=scopes or ["sessions:write", "sessions:read", "grants:read", "campaigns:read"],
    )
    return api_key, plaintext


def _make_campaign(db, allow_partner=True, rule_partner_ids=None, rule_min_trust_tier=None):
    user = _make_admin(db)
    campaign = CampaignService.create_campaign(
        db,
        sponsor_name="Test Sponsor",
        name="Austin Off-Peak Charging",
        campaign_type="utilization_boost",
        budget_cents=100000,
        cost_per_session_cents=250,
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=30),
        created_by_user_id=user.id,
    )
    # Fund and activate
    campaign.funding_status = "funded"
    campaign.funded_at = datetime.utcnow()
    campaign.status = "active"
    campaign.allow_partner_sessions = allow_partner
    campaign.rule_partner_ids = rule_partner_ids
    campaign.rule_min_trust_tier = rule_min_trust_tier
    db.commit()
    db.refresh(campaign)
    return campaign


# --- Unit Tests: Partner Service ---

class TestPartnerService:
    def test_create_partner(self, db):
        partner = PartnerService.create_partner(
            db, name="ChargePoint", slug="chargepoint",
            partner_type="charging_network", trust_tier=1,
        )
        assert partner.id is not None
        assert partner.slug == "chargepoint"
        assert partner.status == "pending"
        assert partner.trust_tier == 1

    def test_create_api_key(self, db):
        partner = _make_partner(db)
        api_key, plaintext = _make_api_key(db, partner.id)

        assert plaintext.startswith("nrv_pk_")
        assert len(plaintext) == 7 + 32  # prefix + 16 bytes hex
        assert api_key.key_prefix == plaintext[:12]
        assert api_key.key_hash == hashlib.sha256(plaintext.encode()).hexdigest()
        assert api_key.is_active is True

    def test_revoke_api_key(self, db):
        partner = _make_partner(db)
        api_key, _ = _make_api_key(db, partner.id)

        result = PartnerService.revoke_api_key(db, api_key.id)
        assert result is True

        db.refresh(api_key)
        assert api_key.is_active is False


# --- Unit Tests: Partner Session Ingest ---

class TestPartnerSessionIngest:
    def test_ingest_completed_session(self, db):
        """Ingest a completed session and verify it creates a SessionEvent."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db)
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="evj_sess_001",
            partner_driver_id="evj_drv_100",
            status="completed",
            session_start=now - timedelta(minutes=30),
            session_end=now,
            charger_network="ChargePoint",
            connector_type="CCS",
            power_kw=150.0,
            kwh_delivered=38.5,
            lat=30.2672,
            lng=-97.7431,
            battery_start_pct=20,
            battery_end_pct=80,
        )

        assert result["session_event_id"] is not None
        assert result["status"] == "completed"
        assert result["verified"] is True  # trust_tier=2
        assert result["quality_score"] is not None
        assert result["duration_minutes"] == 30
        assert result["_is_new"] is True

        # Verify shadow driver was created
        from app.models.user import User
        shadow = db.query(User).filter(
            User.email == f"partner_evject_evj_drv_100@partner.nerava.network"
        ).first()
        assert shadow is not None
        assert shadow.auth_provider == "partner"

    def test_idempotent_ingest(self, db):
        """Submitting the same partner_session_id should return existing session."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db)
        now = datetime.utcnow()
        kwargs = dict(
            partner=partner,
            partner_session_id="evj_sess_dedup",
            partner_driver_id="evj_drv_200",
            status="completed",
            session_start=now - timedelta(minutes=20),
            session_end=now,
        )

        result1 = PartnerSessionService.ingest_session(db, **kwargs)
        result2 = PartnerSessionService.ingest_session(db, **kwargs)

        assert result1["session_event_id"] == result2["session_event_id"]
        assert result2["_is_new"] is False

    def test_session_with_campaign_grant(self, db):
        """Completed session matching a campaign should produce a grant."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db)
        campaign = _make_campaign(db, allow_partner=True)
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="evj_sess_grant",
            partner_driver_id="evj_drv_300",
            status="completed",
            session_start=now - timedelta(minutes=30),
            session_end=now,
            kwh_delivered=20.0,
        )

        assert result["grant"] is not None
        assert result["grant"]["amount_cents"] == 250
        assert result["grant"]["reward_destination"] == "partner_managed"

    def test_campaign_blocks_partner_sessions(self, db):
        """Campaign with allow_partner_sessions=False should not match."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="blocked_test")
        campaign = _make_campaign(db, allow_partner=False)
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="evj_sess_blocked",
            partner_driver_id="evj_drv_400",
            status="completed",
            session_start=now - timedelta(minutes=30),
            session_end=now,
            kwh_delivered=20.0,
        )

        assert result["grant"] is None

    def test_campaign_partner_id_filter(self, db):
        """Campaign with rule_partner_ids should only match listed partners."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="filtered_test")
        campaign = _make_campaign(db, rule_partner_ids=["some-other-partner-id"])
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="evj_sess_filtered",
            partner_driver_id="evj_drv_500",
            status="completed",
            session_start=now - timedelta(minutes=30),
            session_end=now,
            kwh_delivered=20.0,
        )

        assert result["grant"] is None

    def test_campaign_trust_tier_filter(self, db):
        """Campaign requiring trust_tier=1 should reject tier 3 partners."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="tier3_test", trust_tier=3)
        campaign = _make_campaign(db, rule_min_trust_tier=1)
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="evj_sess_tier",
            partner_driver_id="evj_drv_600",
            status="completed",
            session_start=now - timedelta(minutes=30),
            session_end=now,
            kwh_delivered=20.0,
        )

        assert result["grant"] is None

    def test_update_session_to_completed(self, db):
        """Update an in-progress session to completed."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="update_test")
        now = datetime.utcnow()

        # Create in-progress session
        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="evj_sess_update",
            partner_driver_id="evj_drv_700",
            status="charging",
            session_start=now - timedelta(minutes=30),
        )
        assert result["status"] == "charging"

        # Update to completed
        updated = PartnerSessionService.update_session(
            db,
            partner=partner,
            partner_session_id="evj_sess_update",
            status="completed",
            session_end=now,
            kwh_delivered=25.0,
        )
        assert updated is not None
        assert updated["status"] == "completed"
        assert updated["duration_minutes"] == 30


# --- Integration Tests: Auth Dependency ---

class TestPartnerAuth:
    def test_missing_header_returns_401(self, client):
        resp = client.post("/v1/partners/sessions", json={
            "partner_session_id": "test",
            "partner_driver_id": "drv",
            "status": "completed",
            "session_start": "2026-03-06T14:00:00",
        })
        assert resp.status_code == 401

    def test_invalid_key_returns_401(self, client):
        resp = client.post(
            "/v1/partners/sessions",
            json={
                "partner_session_id": "test",
                "partner_driver_id": "drv",
                "status": "completed",
                "session_start": "2026-03-06T14:00:00",
            },
            headers={"X-Partner-Key": "nrv_pk_invalidkey00000000000000000"},
        )
        assert resp.status_code == 401

    def test_inactive_partner_returns_403(self, client, db):
        partner = _make_partner(db, slug="inactive_test", status="suspended")
        _, plaintext = _make_api_key(db, partner.id)

        resp = client.post(
            "/v1/partners/sessions",
            json={
                "partner_session_id": "test",
                "partner_driver_id": "drv",
                "status": "completed",
                "session_start": "2026-03-06T14:00:00",
            },
            headers={"X-Partner-Key": plaintext},
        )
        assert resp.status_code == 403

    def test_missing_scope_returns_403(self, client, db):
        partner = _make_partner(db, slug="scope_test")
        _, plaintext = _make_api_key(db, partner.id, scopes=["sessions:read"])

        resp = client.post(
            "/v1/partners/sessions",
            json={
                "partner_session_id": "test",
                "partner_driver_id": "drv",
                "status": "completed",
                "session_start": "2026-03-06T14:00:00",
            },
            headers={"X-Partner-Key": plaintext},
        )
        assert resp.status_code == 403


# --- Integration Tests: Full API Flow ---

class TestPartnerAPIFlow:
    def test_full_session_ingest_via_api(self, client, db):
        """Full E2E: create partner → key → submit session → get session."""
        partner = _make_partner(db, slug="e2e_test")
        _, plaintext = _make_api_key(db, partner.id)
        headers = {"X-Partner-Key": plaintext}

        # Submit session
        resp = client.post("/v1/partners/sessions", json={
            "partner_session_id": "e2e_sess_001",
            "partner_driver_id": "e2e_drv_001",
            "status": "completed",
            "session_start": "2026-03-06T14:00:00",
            "session_end": "2026-03-06T14:45:00",
            "charger_network": "ChargePoint",
            "power_kw": 150.0,
            "kwh_delivered": 38.5,
            "lat": 30.2672,
            "lng": -97.7431,
        }, headers=headers)
        assert resp.status_code == 202
        data = resp.json()
        assert data["session_event_id"] is not None
        assert data["verified"] is True

        # Get session
        resp2 = client.get(
            f"/v1/partners/sessions/e2e_sess_001",
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["session_event_id"] == data["session_event_id"]

    def test_idempotent_submit_via_api(self, client, db):
        """Re-submitting same partner_session_id returns existing session."""
        partner = _make_partner(db, slug="idemp_test")
        _, plaintext = _make_api_key(db, partner.id)
        headers = {"X-Partner-Key": plaintext}

        payload = {
            "partner_session_id": "idemp_sess_001",
            "partner_driver_id": "idemp_drv_001",
            "status": "completed",
            "session_start": "2026-03-06T14:00:00",
            "session_end": "2026-03-06T14:30:00",
        }

        resp1 = client.post("/v1/partners/sessions", json=payload, headers=headers)
        resp2 = client.post("/v1/partners/sessions", json=payload, headers=headers)

        assert resp1.json()["session_event_id"] == resp2.json()["session_event_id"]

    def test_list_sessions(self, client, db):
        partner = _make_partner(db, slug="list_test")
        _, plaintext = _make_api_key(db, partner.id)
        headers = {"X-Partner-Key": plaintext}

        # Submit two sessions
        for i in range(2):
            client.post("/v1/partners/sessions", json={
                "partner_session_id": f"list_sess_{i}",
                "partner_driver_id": "list_drv",
                "status": "completed",
                "session_start": "2026-03-06T14:00:00",
                "session_end": "2026-03-06T14:30:00",
            }, headers=headers)

        resp = client.get("/v1/partners/sessions", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["sessions"]) == 2

    def test_partner_profile(self, client, db):
        partner = _make_partner(db, slug="profile_test")
        _, plaintext = _make_api_key(db, partner.id)
        headers = {"X-Partner-Key": plaintext}

        resp = client.get("/v1/partners/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "profile_test"
        assert data["total_sessions"] == 0

    def test_available_campaigns(self, client, db):
        partner = _make_partner(db, slug="campaigns_test")
        _, plaintext = _make_api_key(db, partner.id)
        _make_campaign(db, allow_partner=True)
        headers = {"X-Partner-Key": plaintext}

        resp = client.get("/v1/partners/campaigns/available", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["campaigns"]) >= 1


# --- Gap Fix Tests ---

class TestCandidateSessionState:
    """Tests for Gap 1: Candidate/Pending Session State."""

    def test_candidate_session_not_verified(self, db):
        """Candidate sessions should NOT be verified and should NOT trigger incentive evaluation."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="candidate_test")
        campaign = _make_campaign(db, allow_partner=True)
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="cand_sess_001",
            partner_driver_id="cand_drv_001",
            status="candidate",
            session_start=now - timedelta(minutes=30),
            session_end=now,
            kwh_delivered=20.0,
            signal_confidence=0.6,
        )

        assert result["status"] == "candidate"
        assert result["verified"] is False
        assert result["grant"] is None  # No incentive evaluation for candidates
        assert result["signal_confidence"] == 0.6

    def test_candidate_to_completed_triggers_evaluation(self, db):
        """Transitioning from candidate to completed SHOULD trigger incentive evaluation."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="cand_complete_test")
        campaign = _make_campaign(db, allow_partner=True)
        now = datetime.utcnow()

        # Create candidate session
        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="cand_sess_002",
            partner_driver_id="cand_drv_002",
            status="candidate",
            session_start=now - timedelta(minutes=30),
        )
        assert result["status"] == "candidate"
        assert result["verified"] is False
        assert result["grant"] is None

        # Transition to completed
        updated = PartnerSessionService.update_session(
            db,
            partner=partner,
            partner_session_id="cand_sess_002",
            status="completed",
            session_end=now,
            kwh_delivered=25.0,
        )

        assert updated is not None
        assert updated["status"] == "completed"
        assert updated["verified"] is True  # trust_tier=2
        assert updated["grant"] is not None
        assert updated["grant"]["amount_cents"] == 250
        assert updated["grant"]["reward_destination"] == "partner_managed"

    def test_candidate_to_charging_transition(self, db):
        """Transitioning from candidate to charging should update status and verification."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="cand_charging_test")
        now = datetime.utcnow()

        # Create candidate session
        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="cand_sess_003",
            partner_driver_id="cand_drv_003",
            status="candidate",
            session_start=now - timedelta(minutes=10),
        )
        assert result["status"] == "candidate"
        assert result["verified"] is False

        # Transition to charging
        updated = PartnerSessionService.update_session(
            db,
            partner=partner,
            partner_session_id="cand_sess_003",
            status="charging",
        )
        assert updated["status"] == "charging"
        assert updated["verified"] is True  # trust_tier=2

    def test_signal_confidence_in_response(self, db):
        """Signal confidence should be stored and returned in responses."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="signal_test")
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="sig_sess_001",
            partner_driver_id="sig_drv_001",
            status="charging",
            session_start=now - timedelta(minutes=10),
            signal_confidence=0.85,
        )

        assert result["signal_confidence"] == 0.85


class TestRewardBreakdown:
    """Tests for Gap 3: Reward Breakdown in Response."""

    def test_grant_includes_platform_fee(self, db):
        """Grant response should include platform_fee_cents and net_reward_cents."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="fee_test")
        campaign = _make_campaign(db, allow_partner=True)
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="fee_sess_001",
            partner_driver_id="fee_drv_001",
            status="completed",
            session_start=now - timedelta(minutes=30),
            session_end=now,
            kwh_delivered=20.0,
        )

        assert result["grant"] is not None
        assert result["grant"]["amount_cents"] == 250
        # PLATFORM_FEE_BPS defaults to 2000 (20%)
        assert result["grant"]["platform_fee_cents"] == 50  # 250 * 2000 / 10000
        assert result["grant"]["net_reward_cents"] == 200   # 250 - 50


class TestVehicleInfo:
    """Tests for Gap 4: Vehicle VIN + Make/Model."""

    def test_vehicle_info_passthrough(self, db):
        """Vehicle make, model, year should be stored and returned."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="vehicle_test")
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="veh_sess_001",
            partner_driver_id="veh_drv_001",
            status="completed",
            session_start=now - timedelta(minutes=30),
            session_end=now,
            kwh_delivered=20.0,
            vehicle_vin="5YJ3E1EA1NF123456",
            vehicle_make="Tesla",
            vehicle_model="Model 3",
            vehicle_year=2024,
        )

        assert result["vehicle_vin"] == "5YJ3E1EA1NF123456"
        assert result["vehicle_make"] == "Tesla"
        assert result["vehicle_model"] == "Model 3"
        assert result["vehicle_year"] == 2024

    def test_vehicle_info_optional(self, db):
        """Vehicle info should be optional and not appear in response when absent."""
        from app.services.partner_session_service import PartnerSessionService

        partner = _make_partner(db, slug="no_vehicle_test")
        now = datetime.utcnow()

        result = PartnerSessionService.ingest_session(
            db,
            partner=partner,
            partner_session_id="noveh_sess_001",
            partner_driver_id="noveh_drv_001",
            status="completed",
            session_start=now - timedelta(minutes=30),
            session_end=now,
        )

        assert "vehicle_make" not in result
        assert "vehicle_model" not in result
        assert "vehicle_year" not in result

    def test_vehicle_info_via_api(self, client, db):
        """Vehicle info should pass through the API endpoint."""
        partner = _make_partner(db, slug="veh_api_test")
        _, plaintext = _make_api_key(db, partner.id)
        headers = {"X-Partner-Key": plaintext}

        resp = client.post("/v1/partners/sessions", json={
            "partner_session_id": "veh_api_sess_001",
            "partner_driver_id": "veh_api_drv_001",
            "status": "completed",
            "session_start": "2026-03-06T14:00:00",
            "session_end": "2026-03-06T14:45:00",
            "vehicle_vin": "5YJ3E1EA1NF123456",
            "vehicle_make": "Tesla",
            "vehicle_model": "Model Y",
            "vehicle_year": 2025,
        }, headers=headers)
        assert resp.status_code == 202
        data = resp.json()
        assert data["vehicle_make"] == "Tesla"
        assert data["vehicle_model"] == "Model Y"
        assert data["vehicle_year"] == 2025


class TestCandidateSessionViaAPI:
    """Tests for candidate sessions via the API endpoint."""

    def test_candidate_session_via_api(self, client, db):
        """Candidate session via API should work and not trigger evaluation."""
        partner = _make_partner(db, slug="cand_api_test")
        _, plaintext = _make_api_key(db, partner.id)
        _make_campaign(db, allow_partner=True)
        headers = {"X-Partner-Key": plaintext}

        resp = client.post("/v1/partners/sessions", json={
            "partner_session_id": "cand_api_sess_001",
            "partner_driver_id": "cand_api_drv_001",
            "status": "candidate",
            "session_start": "2026-03-06T14:00:00",
            "signal_confidence": 0.7,
            "charging_state_hint": "proximity_detected",
        }, headers=headers)
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "candidate"
        assert data["verified"] is False
        assert data["grant"] is None
        assert data["signal_confidence"] == 0.7
