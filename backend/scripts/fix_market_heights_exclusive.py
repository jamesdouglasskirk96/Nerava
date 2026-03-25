#!/usr/bin/env python3
"""
Fix Market Heights Tesla Supercharger data:
1. Find the charger at 201 E Central Texas Expy, Harker Heights, TX 76548
2. Set "Free Garlic Knots" exclusive on The Heights Pizzeria & Drafthouse link
3. Remove the "Test" merchant link

Run: cd backend && python -m scripts.fix_market_heights_exclusive
Or:  cd backend && DATABASE_URL=<prod_url> python -m scripts.fix_market_heights_exclusive
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import SessionLocal
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant


def main():
    db = SessionLocal()
    try:
        # 1. Find the Market Heights charger
        charger = (
            db.query(Charger)
            .filter(Charger.name.ilike("%market heights%"))
            .first()
        )
        if not charger:
            # Try by address
            charger = (
                db.query(Charger)
                .filter(Charger.address.ilike("%201 E Central Texas%"))
                .first()
            )
        if not charger:
            # Try broader match
            chargers = db.query(Charger).filter(Charger.name.ilike("%harker heights%")).all()
            if chargers:
                charger = chargers[0]

        if not charger:
            print("ERROR: Could not find Market Heights charger. Listing all chargers with 'market' or 'heights':")
            for c in db.query(Charger).filter(
                Charger.name.ilike("%market%") | Charger.name.ilike("%heights%")
            ).all():
                print(f"  id={c.id}  name={c.name}  address={c.address}")
            return

        print(f"Found charger: id={charger.id}  name={charger.name}")
        print(f"  address={charger.address}")

        # 2. List all current merchant links for this charger
        links = (
            db.query(ChargerMerchant, Merchant.name)
            .outerjoin(Merchant, ChargerMerchant.merchant_id == Merchant.id)
            .filter(ChargerMerchant.charger_id == charger.id)
            .order_by(ChargerMerchant.distance_m)
            .all()
        )

        print(f"\nCurrent merchant links ({len(links)}):")
        heights_link = None
        test_links = []
        for link, merchant_name in links:
            exclusive = link.exclusive_title or "(none)"
            print(f"  link_id={link.id}  merchant_id={link.merchant_id}  name={merchant_name}  exclusive={exclusive}  distance={link.distance_m}m")
            if merchant_name and "heights pizzeria" in merchant_name.lower():
                heights_link = link
            if merchant_name and merchant_name.lower().strip() == "test":
                test_links.append(link)

        # 3. Set exclusive on Heights Pizzeria
        if heights_link:
            if heights_link.exclusive_title == "Free Garlic Knots":
                print(f"\nHeights Pizzeria link already has 'Free Garlic Knots' exclusive.")
            else:
                heights_link.exclusive_title = "Free Garlic Knots"
                heights_link.exclusive_description = "Free order of garlic knots with any purchase while you charge"
                db.commit()
                print(f"\nSET exclusive 'Free Garlic Knots' on Heights Pizzeria link (id={heights_link.id})")
        else:
            print("\nWARNING: No Heights Pizzeria link found on this charger.")
            print("  Available merchants above — you may need to create the link manually.")

        # 4. Remove Test merchant links
        if test_links:
            for link in test_links:
                print(f"\nREMOVING 'Test' merchant link (id={link.id}, merchant_id={link.merchant_id})")
                db.delete(link)
            db.commit()
            print(f"Removed {len(test_links)} test merchant link(s).")
        else:
            print("\nNo 'Test' merchant links found (already clean).")

        # 5. Also check for this exclusive on OTHER chargers and remove it
        # (the exclusive should only be on the Market Heights charger)
        other_exclusive_links = (
            db.query(ChargerMerchant)
            .filter(
                ChargerMerchant.exclusive_title == "Free Garlic Knots",
                ChargerMerchant.charger_id != charger.id,
            )
            .all()
        )
        if other_exclusive_links:
            print(f"\nFound 'Free Garlic Knots' exclusive on {len(other_exclusive_links)} OTHER charger(s):")
            for link in other_exclusive_links:
                other_charger = db.query(Charger).filter(Charger.id == link.charger_id).first()
                charger_name = other_charger.name if other_charger else "unknown"
                print(f"  charger_id={link.charger_id}  charger_name={charger_name}  link_id={link.id}")
                link.exclusive_title = None
                link.exclusive_description = None
            db.commit()
            print("Cleared exclusive from other chargers.")

        # Final state
        print("\n--- Final state ---")
        links = (
            db.query(ChargerMerchant, Merchant.name)
            .outerjoin(Merchant, ChargerMerchant.merchant_id == Merchant.id)
            .filter(ChargerMerchant.charger_id == charger.id)
            .order_by(ChargerMerchant.distance_m)
            .all()
        )
        for link, merchant_name in links:
            exclusive = link.exclusive_title or "(none)"
            is_nerava = "YES" if link.exclusive_title else "no"
            print(f"  {merchant_name}: exclusive={exclusive}  is_nerava={is_nerava}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
