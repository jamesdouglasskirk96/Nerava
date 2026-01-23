# Reward System Hardening Summary

## ✅ Implemented Features

### 1. Structured Logging (`app/utils/log.py`)
- JSON-like structured logs for reward events
- Format: `{"at":"reward","step":"...","sid":"...","uid":...,"ok":true,"extra":{...},"ts":"..."}`
- Tracks each step: start, idempotency_check, compute_split, reward_event_inserted, wallet_ledger_inserted, pool_inserted/updated, commit

### 2. Atomic Reward Service (`app/services/rewards.py`)
- `award_verify_bonus()` function with atomic transaction
- Idempotency check: queries `reward_events` for existing session_id
- 90/10 split computation
- Runtime schema detection using SQLAlchemy Inspector
- Dialect-safe inserts (SQLite vs Postgres)
- Returns structured result: `{"awarded": bool, "user_delta": int, "pool_delta": int, "reason": str}`

### 3. Database JSON Utilities (`app/utils/dbjson.py`)
- `as_db_json()` - Converts dict to JSON string for SQLite TEXT columns, passes through dict for Postgres JSONB
- `get_table_columns()` - Runtime schema detection

### 4. Updated Sessions Router (`app/routers/sessions.py`)
- Calls `award_verify_bonus()` service function
- Handles errors gracefully (continues even if reward fails)
- Returns rich response with reward details

### 5. Debug Endpoint (`app/routers/meta.py`)
- `GET /debug/rewards?user_id=1&limit=5`
- Shows recent reward events and wallet balance
- Guarded behind `APP_ENV != 'prod'`

### 6. Documentation (`README_DEV.md`)
- Reward system documentation
- Structured logging format explained
- Debug endpoint usage

## Key Improvements

1. **Atomic Transactions**: All reward writes happen in a single transaction
2. **Idempotency**: Prevents double-rewarding via database check
3. **Schema Adaptation**: Runtime detection of reward_events table structure
4. **Dialect Safety**: Works correctly with both SQLite and Postgres
5. **Structured Logging**: Easy to track reward flow and debug issues
6. **Error Handling**: Graceful degradation if reward creation fails

## Files Created/Modified

**New Files:**
- `app/utils/log.py` - Structured logging
- `app/utils/dbjson.py` - Database JSON utilities
- `app/services/rewards.py` - Atomic reward service

**Modified Files:**
- `app/routers/sessions.py` - Uses reward service
- `app/routers/meta.py` - Added debug endpoint
- `app/routers/gpt.py` - Fixed follows table query (followee_id)
- `README_DEV.md` - Documentation updates

## Testing Results

✅ First verify awards reward (90/10 split)
✅ Second verify on same session returns `rewarded: false, reason: "already_rewarded"`
✅ Wallet balance reflects rewards correctly
✅ `/v1/gpt/me` shows updated wallet_cents and month_self_cents
✅ `/debug/rewards` shows reward events correctly
✅ Structured logs show each step of reward flow

## Success Criteria Met

- ✅ Exactly one reward per verified session (idempotent)
- ✅ `/v1/gpt/me` shows wallet including the +90% credit
- ✅ Logs show single "commit ok" with matching sid and deltas
- ✅ No dialect-specific failures on SQLite or Postgres
