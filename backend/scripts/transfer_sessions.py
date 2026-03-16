"""
One-off script to transfer charging sessions from one user to another.
Usage: DATABASE_URL=postgresql://... python -m scripts.transfer_sessions --from-user 17 --to-phone 7133056318
"""
import argparse
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def main():
    parser = argparse.ArgumentParser(description="Transfer sessions between users")
    parser.add_argument("--from-user", type=int, required=True, help="Source user ID")
    parser.add_argument("--to-phone", type=str, help="Target user phone number")
    parser.add_argument("--to-user", type=int, help="Target user ID (alternative to --to-phone)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Show what would change (default)")
    parser.add_argument("--execute", action="store_true", help="Actually perform the transfer")
    args = parser.parse_args()

    if not args.to_phone and not args.to_user:
        parser.error("Must specify --to-phone or --to-user")

    db_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Find source user
        src = conn.execute(text("SELECT id, phone, email, auth_provider, display_name FROM users WHERE id = :id"), {"id": args.from_user}).fetchone()
        if not src:
            print(f"Source user {args.from_user} not found!")
            return

        print(f"Source user: id={src.id}, phone={src.phone}, email={src.email}, provider={src.auth_provider}, name={src.display_name}")

        # Find target user
        if args.to_user:
            tgt = conn.execute(text("SELECT id, phone, email, auth_provider, display_name FROM users WHERE id = :id"), {"id": args.to_user}).fetchone()
        else:
            tgt = conn.execute(text("SELECT id, phone, email, auth_provider, display_name FROM users WHERE phone = :phone"), {"phone": args.to_phone}).fetchone()

        if not tgt:
            print(f"Target user not found!")
            return

        print(f"Target user: id={tgt.id}, phone={tgt.phone}, email={tgt.email}, provider={tgt.auth_provider}, name={tgt.display_name}")

        # Count sessions
        sessions = conn.execute(text("SELECT COUNT(*) FROM session_events WHERE driver_user_id = :uid"), {"uid": args.from_user}).scalar()
        grants = conn.execute(text("SELECT COUNT(*) FROM incentive_grants WHERE driver_user_id = :uid"), {"uid": args.from_user}).scalar()
        print(f"\nSessions to transfer: {sessions}")
        print(f"Grants to transfer: {grants}")

        # Check Tesla connection
        tesla = conn.execute(text("SELECT id, vehicle_id, vin FROM tesla_connections WHERE user_id = :uid"), {"uid": args.from_user}).fetchone()
        if tesla:
            print(f"Tesla connection: id={tesla.id}, vehicle_id={tesla.vehicle_id}, vin={tesla.vin}")

        # Check wallet
        wallet = conn.execute(text("SELECT id, balance_cents, nova_balance FROM driver_wallets WHERE driver_id = :uid"), {"uid": args.from_user}).fetchone()
        if wallet:
            print(f"Wallet: balance_cents={wallet.balance_cents}, nova={wallet.nova_balance}")

        # Check device tokens
        devices = conn.execute(text("SELECT COUNT(*) FROM device_tokens WHERE user_id = :uid"), {"uid": args.from_user}).scalar()
        print(f"Device tokens: {devices}")

        if not args.execute:
            print("\n--- DRY RUN --- Add --execute to perform the transfer")
            return

        print("\nExecuting transfer...")

        # Transfer sessions
        r = conn.execute(text("UPDATE session_events SET driver_user_id = :to, user_id = :to WHERE driver_user_id = :from_id"),
                         {"to": tgt.id, "from_id": args.from_user})
        print(f"  Sessions updated: {r.rowcount}")

        # Transfer grants
        r = conn.execute(text("UPDATE incentive_grants SET driver_user_id = :to WHERE driver_user_id = :from_id"),
                         {"to": tgt.id, "from_id": args.from_user})
        print(f"  Grants updated: {r.rowcount}")

        # Transfer Tesla connection (if target doesn't already have one)
        if tesla:
            existing = conn.execute(text("SELECT id FROM tesla_connections WHERE user_id = :uid"), {"uid": tgt.id}).fetchone()
            if not existing:
                r = conn.execute(text("UPDATE tesla_connections SET user_id = :to WHERE user_id = :from_id"),
                                 {"to": tgt.id, "from_id": args.from_user})
                print(f"  Tesla connection transferred: {r.rowcount}")
            else:
                print(f"  Target already has Tesla connection — skipping")

        # Transfer wallet balance (merge if target has wallet)
        if wallet and wallet.balance_cents > 0:
            tgt_wallet = conn.execute(text("SELECT id, balance_cents, nova_balance FROM driver_wallets WHERE driver_id = :uid"), {"uid": tgt.id}).fetchone()
            if tgt_wallet:
                conn.execute(text("UPDATE driver_wallets SET balance_cents = balance_cents + :amt, nova_balance = nova_balance + :nova WHERE driver_id = :uid"),
                             {"amt": wallet.balance_cents, "nova": wallet.nova_balance or 0, "uid": tgt.id})
                conn.execute(text("UPDATE driver_wallets SET balance_cents = 0, nova_balance = 0 WHERE driver_id = :uid"),
                             {"uid": args.from_user})
                print(f"  Wallet balance merged: +{wallet.balance_cents}c, +{wallet.nova_balance} nova")
            else:
                conn.execute(text("UPDATE driver_wallets SET driver_id = :to WHERE driver_id = :from_id"),
                             {"to": tgt.id, "from_id": args.from_user})
                print(f"  Wallet transferred")

        conn.commit()
        print("\nTransfer complete!")


if __name__ == "__main__":
    main()
