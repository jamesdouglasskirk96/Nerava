#!/usr/bin/env python3
"""
Backfill script to encrypt existing vehicle_tokens that are plaintext.

This script:
- Targets rows where encryption_version IN (0, NULL) OR token not Fernet-looking
- Decrypts (may return plaintext via compat)
- Encrypts using current key
- Verifies by decrypting back and comparing
- Sets encryption_version=1
- Batch commits
- Provides summary: scanned, migrated, skipped, failed

Usage:
    python scripts/backfill_encrypt_vehicle_tokens.py --dry-run
    python scripts/backfill_vehicle_tokens.py --batch-size 100
    python scripts/backfill_encrypt_vehicle_tokens.py --batch-size 100 --force
"""
import argparse
import sys
import os
from datetime import datetime
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.services.token_encryption import encrypt_token, decrypt_token
from app.utils.env import is_local_env


def is_fernet_looking(token: str) -> bool:
    """Check if token looks like Fernet-encrypted (starts with gAAAAA)"""
    return token and token.startswith("gAAAAA")


def backfill_vehicle_tokens(
    dry_run: bool = False,
    batch_size: int = 100,
    force: bool = False
) -> Tuple[int, int, int, int]:
    """
    Backfill vehicle_tokens encryption.
    
    Returns:
        Tuple of (scanned, migrated, skipped, failed)
    """
    # Fail-fast if TOKEN_ENCRYPTION_KEY missing (even in local)
    token_key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not token_key:
        raise ValueError(
            "TOKEN_ENCRYPTION_KEY environment variable is required. "
            "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    
    # Create database connection
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    scanned = 0
    migrated = 0
    skipped = 0
    failed = 0
    errors = []
    
    try:
        # Find rows to migrate
        # Target: encryption_version IN (0, NULL) OR token not Fernet-looking
        rows = db.execute(text("""
            SELECT id, access_token, refresh_token, encryption_version
            FROM vehicle_tokens
            WHERE encryption_version IS NULL 
               OR encryption_version = 0
               OR access_token NOT LIKE 'gAAAAA%'
               OR refresh_token NOT LIKE 'gAAAAA%'
            ORDER BY id
        """)).fetchall()
        
        total_rows = len(rows)
        print(f"Found {total_rows} vehicle_tokens to process")
        
        if dry_run:
            print("DRY RUN MODE - No changes will be made")
        
        batch = []
        for row in rows:
            scanned += 1
            token_id = row[0]
            access_token = row[1]
            refresh_token = row[2]
            encryption_version = row[3]
            
            try:
                # Check if already encrypted
                if (is_fernet_looking(access_token) and 
                    is_fernet_looking(refresh_token) and 
                    encryption_version == 1):
                    skipped += 1
                    continue
                
                # Decrypt (may return plaintext via compat)
                try:
                    decrypted_access = decrypt_token(access_token)
                    decrypted_refresh = decrypt_token(refresh_token)
                except Exception as e:
                    # If decryption fails, assume plaintext
                    decrypted_access = access_token
                    decrypted_refresh = refresh_token
                
                # Encrypt using current key
                encrypted_access = encrypt_token(decrypted_access)
                encrypted_refresh = encrypt_token(decrypted_refresh)
                
                # Verify by decrypting back and compare
                verify_access = decrypt_token(encrypted_access)
                verify_refresh = decrypt_token(encrypted_refresh)
                
                if verify_access != decrypted_access or verify_refresh != decrypted_refresh:
                    raise ValueError("Encryption verification failed")
                
                # Add to batch
                batch.append({
                    "id": token_id,
                    "access_token": encrypted_access,
                    "refresh_token": encrypted_refresh
                })
                
                if len(batch) >= batch_size:
                    # Commit batch
                    if not dry_run:
                        for item in batch:
                            db.execute(text("""
                                UPDATE vehicle_tokens
                                SET access_token = :access_token,
                                    refresh_token = :refresh_token,
                                    encryption_version = 1
                                WHERE id = :id
                            """), item)
                        db.commit()
                    migrated += len(batch)
                    print(f"Migrated batch: {migrated}/{scanned} rows")
                    batch = []
                    
            except Exception as e:
                failed += 1
                error_msg = f"Row {token_id}: {str(e)}"
                errors.append(error_msg)
                if not force:
                    print(f"ERROR: {error_msg}")
                    if not dry_run:
                        db.rollback()
                    raise
                else:
                    print(f"WARNING (continuing): {error_msg}")
        
        # Commit remaining batch
        if batch:
            if not dry_run:
                for item in batch:
                    db.execute(text("""
                        UPDATE vehicle_tokens
                        SET access_token = :access_token,
                            refresh_token = :refresh_token,
                            encryption_version = 1
                        WHERE id = :id
                    """), item)
                db.commit()
            migrated += len(batch)
        
        # Summary
        print("\n" + "="*60)
        print("BACKFILL SUMMARY")
        print("="*60)
        print(f"Scanned:  {scanned}")
        print(f"Migrated: {migrated}")
        print(f"Skipped:  {skipped}")
        print(f"Failed:   {failed}")
        if errors:
            print("\nErrors:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
        
        if failed > 0 and not force:
            print("\nERROR: Failures encountered. Use --force to continue.")
            return (scanned, migrated, skipped, failed)
        
        return (scanned, migrated, skipped, failed)
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Backfill vehicle_tokens encryption")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no changes)")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for commits")
    parser.add_argument("--force", action="store_true", help="Continue on errors")
    
    args = parser.parse_args()
    
    try:
        scanned, migrated, skipped, failed = backfill_vehicle_tokens(
            dry_run=args.dry_run,
            batch_size=args.batch_size,
            force=args.force
        )
        
        # Exit non-zero if failures > 0 unless --force
        if failed > 0 and not args.force:
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


