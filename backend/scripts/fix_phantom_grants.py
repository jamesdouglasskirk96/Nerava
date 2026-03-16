"""
One-time fix: Re-evaluate sessions that had phantom budget decrements
(campaign budget was spent but Nova grant + wallet credit failed due to
missing nova_transactions.campaign_id column).

Sessions affected (2026-03-12):
- cea3c2eb-1765-47ac-b5f3-dff0668fbec8 (driver 8)
- 3435562d-31ca-4cf5-88e4-5da8c148b499 (driver 8)

These sessions already had their campaign budget decremented but no
IncentiveGrant was created and no wallet credit happened. We need to:
1. Check if IncentiveGrant already exists (skip if so)
2. Re-run IncentiveEngine.evaluate_session() which will create the grant
   and credit the wallet (the budget is already spent so it will try to
   decrement again — we need to handle this)

Alternative approach: directly create the grant + wallet credit without
re-decrementing the budget.

Usage: DATABASE_URL=postgresql://... python scripts/fix_phantom_grants.py
"""
import os
import sys
import uuid
import logging
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

PHANTOM_SESSION_IDS = [
    "cea3c2eb-1765-47ac-b5f3-dff0668fbec8",
    "3435562d-31ca-4cf5-88e4-5da8c148b499",
]

CAMPAIGN_ID = "004a944e-11d3-497a-a6a6-44d4997f7e02"


def fix():
    from app.db import SessionLocal
    from app.models.session_event import SessionEvent, IncentiveGrant
    from app.models.campaign import Campaign
    from app.models.driver_wallet import DriverWallet, WalletLedger

    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == CAMPAIGN_ID).first()
        if not campaign:
            logger.error(f"Campaign {CAMPAIGN_ID} not found")
            return

        for session_id in PHANTOM_SESSION_IDS:
            session = db.query(SessionEvent).filter(SessionEvent.id == session_id).first()
            if not session:
                logger.warning(f"Session {session_id} not found, skipping")
                continue

            # Check if grant already exists
            existing = db.query(IncentiveGrant).filter(
                IncentiveGrant.session_event_id == session_id
            ).first()
            if existing:
                logger.info(f"Grant already exists for session {session_id}: {existing.id}")
                continue

            if not session.session_end:
                logger.warning(f"Session {session_id} not ended, skipping")
                continue

            amount = campaign.cost_per_session_cents
            logger.info(
                f"Fixing session {session_id}: driver={session.driver_user_id}, "
                f"duration={session.duration_minutes}min, amount={amount}c"
            )

            # Create the IncentiveGrant (budget already decremented)
            grant = IncentiveGrant(
                id=str(uuid.uuid4()),
                session_event_id=session.id,
                campaign_id=campaign.id,
                driver_user_id=session.driver_user_id,
                amount_cents=amount,
                status="granted",
                reward_destination="nerava_wallet",
                idempotency_key=f"campaign_{campaign.id}_session_{session.id}",
                granted_at=datetime.utcnow(),
            )
            db.add(grant)
            db.flush()
            logger.info(f"Created grant {grant.id}")

            # Credit wallet
            wallet = db.query(DriverWallet).filter(
                DriverWallet.driver_id == session.driver_user_id
            ).first()
            if not wallet:
                wallet = DriverWallet(
                    id=str(uuid.uuid4()),
                    driver_id=session.driver_user_id,
                    balance_cents=0,
                    pending_balance_cents=0,
                )
                db.add(wallet)
                db.flush()

            wallet.balance_cents += amount
            wallet.total_earned_cents += amount
            wallet.updated_at = datetime.utcnow()

            ledger_entry = WalletLedger(
                id=str(uuid.uuid4()),
                wallet_id=wallet.id,
                driver_id=session.driver_user_id,
                amount_cents=amount,
                balance_after_cents=wallet.balance_cents,
                transaction_type="credit",
                reference_type="campaign_grant",
                reference_id=grant.id,
                description=f"Fix: earned from {campaign.name} (phantom grant recovery)",
            )
            db.add(ledger_entry)
            logger.info(
                f"Credited {amount}c to driver {session.driver_user_id} wallet "
                f"(new balance: {wallet.balance_cents}c)"
            )

        db.commit()
        logger.info("Done — all phantom grants fixed")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix()
