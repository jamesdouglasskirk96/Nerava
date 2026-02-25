"""
Incentive Engine — Rules evaluation for session-to-campaign matching.

Key design decisions per review:
- Evaluate on session END only (called after SessionEventService.end_session)
- One session = one grant max (highest priority campaign wins, no stacking)
- Budget decrement is atomic (prevents overruns)
- Driver caps enforced before grant
- Minimum duration is mandatory for every campaign
"""
import uuid
import math
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.session_event import SessionEvent, IncentiveGrant
from app.services.campaign_service import CampaignService

logger = logging.getLogger(__name__)


class IncentiveEngine:
    """Evaluates completed sessions against active campaigns."""

    @staticmethod
    def evaluate_session(db: Session, session: SessionEvent) -> Optional[IncentiveGrant]:
        """
        Evaluate a completed session against all active campaigns.
        Returns the grant if one was created, else None.

        One session = one grant. Highest priority campaign wins.
        Campaigns are pre-sorted by priority (ascending = higher priority).
        """
        if session.session_end is None:
            logger.debug(f"Session {session.id} not ended yet, skipping evaluation")
            return None

        if not session.duration_minutes or session.duration_minutes < 1:
            logger.debug(f"Session {session.id} too short ({session.duration_minutes}min)")
            return None

        # Check if session already has a grant (idempotency)
        existing = db.query(IncentiveGrant).filter(
            IncentiveGrant.session_event_id == session.id
        ).first()
        if existing:
            logger.debug(f"Session {session.id} already has grant {existing.id}")
            return existing

        # Get active campaigns sorted by priority
        campaigns = CampaignService.get_active_campaigns(db)
        if not campaigns:
            return None

        for campaign in campaigns:
            if IncentiveEngine._session_matches_campaign(db, session, campaign):
                grant = IncentiveEngine._create_grant(db, session, campaign)
                if grant:
                    return grant

        return None

    @staticmethod
    def _session_matches_campaign(
        db: Session,
        session: SessionEvent,
        campaign: Campaign,
    ) -> bool:
        """
        Check if a session matches ALL rules of a campaign.
        All non-null rules are AND-ed.
        """
        # --- Mandatory: minimum duration ---
        if session.duration_minutes < campaign.rule_min_duration_minutes:
            return False

        # --- Optional max duration ---
        if campaign.rule_max_duration_minutes and session.duration_minutes > campaign.rule_max_duration_minutes:
            return False

        # --- Charger IDs ---
        if campaign.rule_charger_ids:
            if session.charger_id not in campaign.rule_charger_ids:
                return False

        # --- Charger networks ---
        if campaign.rule_charger_networks:
            if session.charger_network not in campaign.rule_charger_networks:
                return False

        # --- Zone IDs ---
        if campaign.rule_zone_ids:
            if session.zone_id not in campaign.rule_zone_ids:
                return False

        # --- Geo radius ---
        if campaign.rule_geo_center_lat is not None and campaign.rule_geo_center_lng is not None and campaign.rule_geo_radius_m:
            if session.lat is None or session.lng is None:
                return False
            dist = IncentiveEngine._haversine_m(
                campaign.rule_geo_center_lat, campaign.rule_geo_center_lng,
                session.lat, session.lng,
            )
            if dist > campaign.rule_geo_radius_m:
                return False

        # --- Time of day ---
        if campaign.rule_time_start and campaign.rule_time_end:
            session_hour_min = session.session_start.strftime("%H:%M")
            if not IncentiveEngine._time_in_window(
                session_hour_min, campaign.rule_time_start, campaign.rule_time_end
            ):
                return False

        # --- Day of week ---
        if campaign.rule_days_of_week:
            session_dow = session.session_start.isoweekday()  # 1=Mon, 7=Sun
            if session_dow not in campaign.rule_days_of_week:
                return False

        # --- Min power (DC fast only) ---
        if campaign.rule_min_power_kw:
            if session.power_kw is None or session.power_kw < campaign.rule_min_power_kw:
                return False

        # --- Connector types ---
        if campaign.rule_connector_types:
            if session.connector_type not in campaign.rule_connector_types:
                return False

        # --- Driver session count (for new/repeat driver rules) ---
        if campaign.rule_driver_session_count_min is not None or campaign.rule_driver_session_count_max is not None:
            from app.services.session_event_service import SessionEventService
            count = SessionEventService.count_driver_sessions(db, session.driver_user_id)
            if campaign.rule_driver_session_count_min is not None:
                if count < campaign.rule_driver_session_count_min:
                    return False
            if campaign.rule_driver_session_count_max is not None:
                if count > campaign.rule_driver_session_count_max:
                    return False

        # --- Driver allowlist ---
        if campaign.rule_driver_allowlist:
            from app.models.user import User
            driver = db.query(User).filter(User.id == session.driver_user_id).first()
            if not driver:
                return False
            # Check email or user_id in allowlist
            driver_email = driver.email or ""
            driver_id_str = str(driver.id)
            if driver_email not in campaign.rule_driver_allowlist and driver_id_str not in campaign.rule_driver_allowlist:
                return False

        # --- Driver caps ---
        if not CampaignService.check_driver_caps(db, campaign, session.driver_user_id, session.charger_id):
            return False

        return True

    @staticmethod
    def _create_grant(
        db: Session,
        session: SessionEvent,
        campaign: Campaign,
    ) -> Optional[IncentiveGrant]:
        """
        Create an incentive grant and atomically decrement campaign budget.
        Also creates a Nova transaction for the driver.
        """
        amount = campaign.cost_per_session_cents
        idempotency_key = f"campaign_{campaign.id}_session_{session.id}"

        # Atomic budget decrement — returns False if insufficient
        if not CampaignService.decrement_budget_atomic(db, campaign.id, amount):
            logger.info(f"Campaign {campaign.id} budget insufficient for {amount}c")
            return None

        # Create Nova transaction (atomic with grant)
        from app.services.nova_service import NovaService
        try:
            nova_tx = NovaService.grant_to_driver(
                db,
                driver_id=session.driver_user_id,
                amount=amount,
                type="campaign_grant",
                session_id=str(session.id),
                metadata={
                    "source": "incentive_engine",
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "charger_id": session.charger_id,
                    "duration_minutes": session.duration_minutes,
                },
                idempotency_key=idempotency_key,
                auto_commit=False,
            )
        except Exception as e:
            logger.error(f"Failed to grant Nova for campaign {campaign.id}: {e}")
            return None

        # Create incentive grant record
        grant = IncentiveGrant(
            id=str(uuid.uuid4()),
            session_event_id=session.id,
            campaign_id=campaign.id,
            driver_user_id=session.driver_user_id,
            amount_cents=amount,
            status="granted",
            nova_transaction_id=nova_tx.id if nova_tx else None,
            idempotency_key=idempotency_key,
            granted_at=datetime.utcnow(),
        )
        db.add(grant)
        db.flush()

        logger.info(
            f"Granted {amount}c from campaign '{campaign.name}' to driver {session.driver_user_id} "
            f"for session {session.id} ({session.duration_minutes}min)"
        )
        return grant

    @staticmethod
    def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance in meters between two lat/lng points."""
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _time_in_window(time_str: str, start: str, end: str) -> bool:
        """
        Check if time_str (HH:MM) is within start-end window.
        Handles overnight windows (e.g., 22:00 → 06:00).
        """
        if start <= end:
            return start <= time_str <= end
        else:
            # Overnight window
            return time_str >= start or time_str <= end
