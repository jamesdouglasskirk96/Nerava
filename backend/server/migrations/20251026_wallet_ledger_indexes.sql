-- Migration: Create wallet_events indexes
-- Date: 2025-10-26

CREATE INDEX IF NOT EXISTS idx_wallet_events_user_kind ON wallet_events(user_id, kind);
CREATE INDEX IF NOT EXISTS idx_wallet_events_user_created ON wallet_events(user_id, created_at DESC);

