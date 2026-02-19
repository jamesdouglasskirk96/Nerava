-- Production Database Validation Queries
-- Run these against your production database to catch data integrity issues
--
-- Usage:
--   psql $DATABASE_URL -f scripts/validate_production_db.sql
--
-- All queries should return 0 or empty results for a healthy database

-- ============================================================
-- Rule 1: No UUIDs in merchant_place_id (should be Google Place IDs or NULL)
-- ============================================================
SELECT
    'CRITICAL: UUID in merchant_place_id' as issue,
    COUNT(*) as count
FROM exclusive_sessions
WHERE merchant_place_id IS NOT NULL
  AND merchant_place_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
HAVING COUNT(*) > 0;

-- ============================================================
-- Rule 2: No null island sessions (lat=0, lng=0)
-- ============================================================
SELECT
    'CRITICAL: Null island session' as issue,
    COUNT(*) as count
FROM exclusive_sessions
WHERE lat = 0 AND lng = 0
HAVING COUNT(*) > 0;

-- ============================================================
-- Rule 3: No orphaned sessions (user doesn't exist)
-- ============================================================
SELECT
    'WARNING: Orphaned session' as issue,
    COUNT(*) as count
FROM exclusive_sessions es
LEFT JOIN users u ON es.driver_id = u.id
WHERE u.id IS NULL
HAVING COUNT(*) > 0;

-- ============================================================
-- Rule 4: Active sessions with expired times
-- ============================================================
SELECT
    'WARNING: Expired but still ACTIVE' as issue,
    COUNT(*) as count
FROM exclusive_sessions
WHERE status = 'ACTIVE'
  AND expires_at < NOW()
HAVING COUNT(*) > 0;

-- ============================================================
-- Rule 5: Intent persistence working (for V3)
-- ============================================================
-- This should return recent sessions WITH intent data if V3 is deployed
SELECT
    'INFO: Recent sessions with intent' as info,
    COUNT(*) as count
FROM exclusive_sessions
WHERE intent IS NOT NULL
  AND created_at > NOW() - INTERVAL '7 days';

-- ============================================================
-- Health Summary
-- ============================================================
SELECT
    'SUMMARY' as type,
    (SELECT COUNT(*) FROM exclusive_sessions) as total_sessions,
    (SELECT COUNT(*) FROM exclusive_sessions WHERE status = 'ACTIVE') as active_sessions,
    (SELECT COUNT(*) FROM exclusive_sessions WHERE status = 'COMPLETED') as completed_sessions,
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE auth_provider = 'phone') as otp_verified_users;

-- ============================================================
-- Recent Failures (last 24 hours)
-- ============================================================
-- Check for patterns in failed sessions
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    status,
    COUNT(*) as count
FROM exclusive_sessions
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), status
ORDER BY hour DESC, status;
