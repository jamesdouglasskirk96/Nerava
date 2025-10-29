-- Migration: Migrate reward_events to wallet_events
-- Date: 2025-10-26

INSERT INTO wallet_events (id, user_id, kind, source, amount_cents, created_at)
SELECT 
    id,
    user_id,
    'credit' as kind,
    'merchant_reward' as source,
    amount_cents,
    created_at
FROM reward_events
WHERE NOT EXISTS (
    SELECT 1 FROM wallet_events we WHERE we.id = reward_events.id
);

