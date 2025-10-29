"""
Minimal seed script for GPT endpoints.
Inserts: 1 user, 10 coffee shops, 10 gyms, 6 offers.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from app.db import SessionLocal


def seed_minimal():
    """Seed minimal data for GPT endpoints"""
    db = SessionLocal()
    
    try:
        # 1. Insert one user (id=1, handle="james", email="james@example.com")
        # Handle SQLite vs Postgres differently for ON CONFLICT
        if db.bind.dialect.name == 'postgresql':
            db.execute(text("""
                INSERT INTO users (id, email, handle, is_active, created_at, password_hash)
                VALUES (1, 'james@example.com', 'james', true, CURRENT_TIMESTAMP, 'demo_hash')
                ON CONFLICT(id) DO UPDATE SET handle = 'james', email = 'james@example.com'
            """))
        else:
            # SQLite - check if exists first
            existing = db.execute(text("SELECT id FROM users WHERE id = 1")).first()
            if not existing:
                db.execute(text("""
                    INSERT INTO users (id, email, handle, is_active, created_at, password_hash)
                    VALUES (1, 'james@example.com', 'james', 1, CURRENT_TIMESTAMP, 'demo_hash')
                """))
            else:
                db.execute(text("""
                    UPDATE users SET handle = 'james', email = 'james@example.com' WHERE id = 1
                """))
        
        # 2. Insert 10 coffee shops in Austin
        coffee_shops = [
            ("Starbucks Downtown", 30.2672, -97.7431, "310 E 5th St, Austin, TX"),
            ("Jo's Coffee", 30.2680, -97.7390, "242 West 2nd St, Austin, TX"),
            ("Blue Bottle Coffee", 30.2690, -97.7450, "11500 Rock Rose Ave, Austin, TX"),
            ("Caffe Medici", 30.2700, -97.7400, "1101 W Lynn St, Austin, TX"),
            ("Houndstooth Coffee", 30.2650, -97.7420, "401 Congress Ave, Austin, TX"),
            ("Figure 8 Coffee", 30.2640, -97.7440, "1110 E Cesar Chavez St, Austin, TX"),
            ("Fleet Coffee Co", 30.2630, -97.7460, "2427 E Cesar Chavez St, Austin, TX"),
            ("Merit Coffee", 30.2620, -97.7480, "213 W 4th St, Austin, TX"),
            ("Spokesman Coffee", 30.2610, -97.7500, "4400 S Lamar Blvd, Austin, TX"),
            ("Brew & Brew", 30.2600, -97.7520, "500 E 5th St, Austin, TX"),
        ]
        
        merchant_ids = []
        for name, lat, lng, address in coffee_shops:
            # Insert and get ID
            if db.bind.dialect.name == 'postgresql':
                result = db.execute(text("""
                    INSERT INTO merchants (name, category, lat, lng, address, created_at)
                    VALUES (:name, 'coffee', :lat, :lng, :address, CURRENT_TIMESTAMP)
                    RETURNING id
                """), {"name": name, "lat": lat, "lng": lng, "address": address})
                merchant_id = result.scalar()
            else:
                db.execute(text("""
                    INSERT INTO merchants (name, category, lat, lng, address, created_at)
                    VALUES (:name, 'coffee', :lat, :lng, :address, CURRENT_TIMESTAMP)
                """), {"name": name, "lat": lat, "lng": lng, "address": address})
                merchant_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
            merchant_ids.append(merchant_id)
        
        # 3. Insert 10 gyms in Austin
        gyms = [
            ("24 Hour Fitness", 30.2672, -97.7431, "601 W 2nd St, Austin, TX"),
            ("Gold's Gym", 30.2680, -97.7390, "2600 W Anderson Ln, Austin, TX"),
            ("Planet Fitness", 30.2690, -97.7450, "11100 Research Blvd, Austin, TX"),
            ("CrossFit Central", 30.2700, -97.7400, "1700 S Lamar Blvd, Austin, TX"),
            ("Pure Barre", 30.2650, -97.7420, "2625 W Anderson Ln, Austin, TX"),
            ("Orange Theory", 30.2640, -97.7440, "11601 Domain Dr, Austin, TX"),
            ("Lifetime Fitness", 30.2630, -97.7460, "6800 Austin Center Blvd, Austin, TX"),
            ("Equinox", 30.2620, -97.7480, "301 W 2nd St, Austin, TX"),
            ("Camp Gladiator", 30.2610, -97.7500, "Various locations, Austin, TX"),
            ("Barry's Bootcamp", 30.2600, -97.7520, "11500 Rock Rose Ave, Austin, TX"),
        ]
        
        for name, lat, lng, address in gyms:
            # Insert and get ID
            if db.bind.dialect.name == 'postgresql':
                result = db.execute(text("""
                    INSERT INTO merchants (name, category, lat, lng, address, created_at)
                    VALUES (:name, 'gym', :lat, :lng, :address, CURRENT_TIMESTAMP)
                    RETURNING id
                """), {"name": name, "lat": lat, "lng": lng, "address": address})
                merchant_id = result.scalar()
            else:
                db.execute(text("""
                    INSERT INTO merchants (name, category, lat, lng, address, created_at)
                    VALUES (:name, 'gym', :lat, :lng, :address, CURRENT_TIMESTAMP)
                """), {"name": name, "lat": lat, "lng": lng, "address": address})
                merchant_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
            merchant_ids.append(merchant_id)
        
        # 4. Insert 6 offers tied to some merchants (first 6 coffee shops)
        # Using simple time windows: 14:00-16:00 (2pm-4pm)
        offer_merchant_ids = merchant_ids[:6]  # First 6 coffee shops
        
        for merchant_id in offer_merchant_ids:
            db.execute(text("""
                INSERT INTO offers (merchant_id, title, description, reward_cents, start_time, end_time, active, created_at)
                VALUES (:merchant_id, 'Free Coffee', 'Enjoy a free coffee between 2pm and 4pm', 500, '14:00:00', '16:00:00', 1, CURRENT_TIMESTAMP)
            """), {"merchant_id": merchant_id})
        
        db.commit()
        print(f"✅ Seeded: 1 user, {len(coffee_shops)} coffee shops, {len(gyms)} gyms, {len(offer_merchant_ids)} offers")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    seed_minimal()

