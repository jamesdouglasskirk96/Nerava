#!/usr/bin/env python3
"""
Verification script for Domain hub seeding.

Checks that Domain chargers are present in the database with correct fields.

Usage:
    python verify_domain_seed.py
"""
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.db import get_db
from app.models_while_you_charge import Charger
from app.domains.domain_hub import DOMAIN_CHARGERS, HUB_ID, HUB_NAME


def verify_domain_seed():
    """Verify that Domain hub chargers are seeded correctly."""
    db = next(get_db())
    
    try:
        print(f'🔍 Verifying {HUB_NAME} hub seed...\n')
        
        expected_charger_ids = {ch["id"] for ch in DOMAIN_CHARGERS}
        found_chargers = []
        missing_chargers = []
        incorrect_chargers = []
        
        for charger_config in DOMAIN_CHARGERS:
            charger_id = charger_config["id"]
            charger = db.query(Charger).filter(Charger.id == charger_id).first()
            
            if not charger:
                missing_chargers.append(charger_id)
                print(f'  ❌ Missing: {charger_id} ({charger_config["name"]})')
                continue
            
            # Verify key fields
            issues = []
            if charger.name != charger_config["name"]:
                issues.append(f"name mismatch: got '{charger.name}', expected '{charger_config['name']}'")
            if abs(charger.lat - charger_config["lat"]) > 0.0001:
                issues.append(f"lat mismatch: got {charger.lat}, expected {charger_config['lat']}")
            if abs(charger.lng - charger_config["lng"]) > 0.0001:
                issues.append(f"lng mismatch: got {charger.lng}, expected {charger_config['lng']}")
            if charger.network_name != charger_config["network_name"]:
                issues.append(f"network_name mismatch: got '{charger.network_name}', expected '{charger_config['network_name']}'")
            if charger.city != charger_config.get("city", "Austin"):
                issues.append(f"city mismatch: got '{charger.city}', expected 'Austin'")
            
            if issues:
                incorrect_chargers.append((charger_id, issues))
                print(f'  ⚠️  Incorrect: {charger_id} ({charger_config["name"]})')
                for issue in issues:
                    print(f'     - {issue}')
            else:
                found_chargers.append(charger_id)
                print(f'  ✅ Found: {charger_id} ({charger_config["name"]})')
                print(f'     Location: ({charger.lat}, {charger.lng})')
                print(f'     Network: {charger.network_name}')
        
        print(f'\n📊 Verification Summary:')
        print(f'   Total expected: {len(DOMAIN_CHARGERS)}')
        print(f'   ✅ Found and correct: {len(found_chargers)}')
        print(f'   ❌ Missing: {len(missing_chargers)}')
        print(f'   ⚠️  Incorrect: {len(incorrect_chargers)}')
        
        if missing_chargers:
            print(f'\n   Missing charger IDs: {", ".join(missing_chargers)}')
        
        if incorrect_chargers:
            print(f'\n   Incorrect chargers:')
            for charger_id, issues in incorrect_chargers:
                print(f'     - {charger_id}: {", ".join(issues)}')
        
        # Overall result
        if len(found_chargers) == len(DOMAIN_CHARGERS):
            print(f'\n✅ All Domain hub chargers are present and correct!')
            return True
        else:
            print(f'\n❌ Verification failed: {len(missing_chargers) + len(incorrect_chargers)} issue(s) found')
            return False
    
    except Exception as e:
        print(f'❌ Verification error: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == '__main__':
    success = verify_domain_seed()
    sys.exit(0 if success else 1)

