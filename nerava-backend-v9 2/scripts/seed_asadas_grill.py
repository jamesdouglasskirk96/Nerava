"""
Seed Asadas Grill merchant and link to Domain chargers.
"""
import sys
sys.path.insert(0, '.')

from app.db import SessionLocal
from app.models.while_you_charge import Merchant, Charger, ChargerMerchant, MerchantPerk
import json
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters"""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def seed_asadas_grill():
    db = SessionLocal()
    try:
        # Load place details from static file
        with open('merchant_photos_asadas_grill/place_details.json', 'r') as f:
            place_data = json.load(f)

        # Check if Asadas Grill already exists
        existing = db.query(Merchant).filter(
            Merchant.name.ilike('%asadas%grill%')
        ).first()

        # Update or create merchant with full details
        if existing:
            print(f"Asadas Grill already exists: {existing.id}, updating...")
            merchant = existing
        else:
            # Create merchant
            merchant = Merchant(
                id="m_asadas_grill",
                external_id=place_data["place_id"],  # ChIJKV41JMnORIYRu2cBs5CKtBc
                name="Asadas Grill",
                category="Restaurant",
                primary_category="food",
                lat=place_data["location"]["lat"],  # 30.4027969
                lng=place_data["location"]["lng"],  # -97.6719438
                address=place_data["address"],
                rating=place_data.get("rating"),
                price_level=place_data.get("price_level"),
                place_types=["restaurant", "mexican_restaurant", "food"],
                photo_url="/static/merchant_photos_asadas_grill/asadas_grill_01.jpg"
            )
            db.add(merchant)
            db.flush()
            print(f"Created Asadas Grill: {merchant.id}")

        # Update with new fields from place_details.json
        merchant.description = place_data.get("description")
        merchant.user_rating_count = place_data.get("user_rating_count")
        # Only set place_id if it's not already set and not used by another merchant
        target_place_id = place_data.get("place_id")
        if not merchant.place_id and target_place_id:
            # Check if another merchant already has this place_id
            existing_with_place_id = db.query(Merchant).filter(
                Merchant.place_id == target_place_id,
                Merchant.id != merchant.id
            ).first()
            if not existing_with_place_id:
                merchant.place_id = target_place_id
            else:
                print(f"Warning: place_id {target_place_id} already assigned to merchant {existing_with_place_id.id}, skipping")
        
        # Set photo_urls array (can add more URLs later)
        merchant.photo_urls = [
            "/static/merchant_photos_asadas_grill/asadas_grill_01.jpg",
            # Add more photo URLs as needed
        ]
        
        # Set opening_hours from place_data
        if "opening_hours" in place_data:
            opening_hours = place_data["opening_hours"]
            # Normalize weekday_text format (remove special Unicode characters)
            if "weekday_text" in opening_hours:
                normalized_weekday_text = []
                for day_text in opening_hours["weekday_text"]:
                    # Replace Unicode en-dash and non-breaking spaces with standard characters
                    normalized = day_text.replace('\u2013', '–').replace('\u202f', ' ').replace('\u2009', ' ')
                    normalized_weekday_text.append(normalized)
                opening_hours["weekday_text"] = normalized_weekday_text
            
            merchant.opening_hours = opening_hours
        
        db.flush()
        print("Updated Asadas Grill with full details (description, hours, rating, etc.)")

        # Create perk for Asadas Grill
        existing_perk = db.query(MerchantPerk).filter(
            MerchantPerk.merchant_id == merchant.id,
            MerchantPerk.is_active == True
        ).first()

        if not existing_perk:
            perk = MerchantPerk(
                merchant_id=merchant.id,
                title="Free Beverage Exclusive",
                description="Get a free beverage with any meal during charging hours. Show your pass to redeem.",
                nova_reward=50,
                is_active=True
            )
            db.add(perk)
            print("Created Free Beverage Exclusive perk")

        # Link to all Domain chargers
        domain_chargers = db.query(Charger).filter(
            Charger.id.like('ch_domain%')
        ).all()

        # If no Domain chargers, link to test charger
        if not domain_chargers:
            domain_chargers = db.query(Charger).filter(
                Charger.id.like('ch_test%')
            ).all()

        for charger in domain_chargers:
            # Check if link exists
            existing_link = db.query(ChargerMerchant).filter(
                ChargerMerchant.charger_id == charger.id,
                ChargerMerchant.merchant_id == merchant.id
            ).first()

            if existing_link:
                print(f"Link already exists: {charger.id} -> {merchant.id}")
                continue

            # Calculate distance
            distance_m = haversine_distance(
                charger.lat, charger.lng,
                merchant.lat, merchant.lng
            )

            # Estimate walk time (80m per minute)
            walk_duration_s = int((distance_m / 80) * 60)

            link = ChargerMerchant(
                charger_id=charger.id,
                merchant_id=merchant.id,
                distance_m=distance_m,
                walk_duration_s=walk_duration_s,
                walk_distance_m=distance_m * 1.3  # Estimate walking distance is ~30% longer
            )
            db.add(link)
            print(f"Linked {charger.name} -> Asadas Grill ({int(distance_m)}m, {walk_duration_s}s walk)")

        db.commit()
        print("Done! Asadas Grill is now seeded and linked to chargers.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_asadas_grill()

