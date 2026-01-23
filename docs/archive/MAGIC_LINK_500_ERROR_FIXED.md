# Magic-Link 500 Error - FIXED ✅

## Issue
Getting 500 Internal Server Error when requesting a magic link.

## Root Cause
The error was caused by a **broken SQLAlchemy relationship** in the `DriverWallet` model:

```
NoForeignKeysError: Could not determine join condition between parent/child tables on relationship DriverWallet.transactions - there are no foreign keys linking these tables.
```

The `DriverWallet` model had a relationship `transactions = relationship("NovaTransaction", back_populates="driver")` that was trying to link to `NovaTransaction`, but:
- There's no direct foreign key between `driver_wallets` and `nova_transactions` tables
- SQLAlchemy couldn't determine how to join them
- This caused ALL database queries to fail during model initialization, including the User query needed for magic-link auth

## Fix Applied
Removed the broken relationship from `DriverWallet` model in `nerava-backend-v9/app/models_domain.py`:

**Before:**
```python
transactions = relationship("NovaTransaction", back_populates="driver")
```

**After:**
```python
# Note: transactions relationship removed - query NovaTransaction directly via driver_user_id
# transactions = relationship("NovaTransaction", back_populates="driver")  # BROKEN: no direct FK
```

## Verification
✅ Endpoint now works successfully:
```python
# Test result:
{'message': 'Magic link sent to your email', 'email': 'test@example.com'}
```

## Next Steps
1. The server should have auto-reloaded with the fix
2. Try entering your email again in the frontend - it should work now!
3. The magic link URL will be logged in the backend terminal (dev mode)

## Notes
- If you need to query transactions for a driver wallet in the future, use:
  ```python
  db.query(NovaTransaction).filter(NovaTransaction.driver_user_id == wallet.user_id).all()
  ```
- This avoids the broken relationship and works correctly.

