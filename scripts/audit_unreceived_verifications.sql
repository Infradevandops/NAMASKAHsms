-- CRITICAL: Identify Charged But Unreceived Verifications
-- Run this against production database to find refund candidates

-- 1. PENDING VERIFICATIONS OLDER THAN 10 MINUTES (LIKELY FAILED)
SELECT 
    v.id as verification_id,
    v.user_id,
    u.email as user_email,
    v.service_name,
    v.status,
    v.cost,
    v.phone_number,
    v.created_at,
    EXTRACT(EPOCH FROM (NOW() - v.created_at))/60 as minutes_pending,
    v.activation_id,
    v.requested_area_code,
    v.requested_carrier
FROM verifications v
JOIN users u ON v.user_id = u.id
WHERE v.status = 'pending'
  AND v.cost > 0
  AND v.created_at < NOW() - INTERVAL '10 minutes'
  AND v.created_at > NOW() - INTERVAL '7 days'
ORDER BY v.created_at DESC;

-- Expected: Should be 0 (all should timeout/complete)
-- If > 0: These users were charged but never got SMS


-- 2. FAILED VERIFICATIONS THAT WERE CHARGED
SELECT 
    v.id as verification_id,
    v.user_id,
    u.email as user_email,
    v.service_name,
    v.status,
    v.cost,
    v.created_at,
    v.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(v.completed_at, NOW()) - v.created_at))/60 as duration_minutes
FROM verifications v
JOIN users u ON v.user_id = u.id
WHERE v.status IN ('failed', 'error', 'cancelled')
  AND v.cost > 0
  AND v.created_at > NOW() - INTERVAL '7 days'
ORDER BY v.created_at DESC;

-- Expected: Should have corresponding refund transactions
-- If no refund: User was charged but not refunded


-- 3. VERIFICATIONS WITHOUT SMS CODE AFTER 5+ MINUTES
SELECT 
    v.id as verification_id,
    v.user_id,
    u.email as user_email,
    v.service_name,
    v.status,
    v.cost,
    v.phone_number,
    v.created_at,
    v.sms_code,
    v.sms_text,
    EXTRACT(EPOCH FROM (NOW() - v.created_at))/60 as minutes_elapsed
FROM verifications v
JOIN users u ON v.user_id = u.id
WHERE v.status = 'pending'
  AND v.cost > 0
  AND v.sms_code IS NULL
  AND v.created_at < NOW() - INTERVAL '5 minutes'
  AND v.created_at > NOW() - INTERVAL '24 hours'
ORDER BY v.created_at DESC;

-- Expected: Should be minimal (most SMS arrive within 2 min)
-- If many: Provider issues or service problems


-- 4. CHECK FOR REFUND TRANSACTIONS
SELECT 
    v.id as verification_id,
    v.user_id,
    v.cost as charged_amount,
    v.status,
    v.created_at as verification_time,
    t.id as transaction_id,
    t.amount as refund_amount,
    t.transaction_type,
    t.created_at as refund_time
FROM verifications v
LEFT JOIN transactions t ON (
    t.user_id = v.user_id 
    AND t.transaction_type IN ('refund', 'credit_adjustment')
    AND t.created_at > v.created_at
    AND t.created_at < v.created_at + INTERVAL '1 hour'
    AND ABS(t.amount - v.cost) < 0.01
)
WHERE v.status IN ('failed', 'cancelled', 'error')
  AND v.cost > 0
  AND v.created_at > NOW() - INTERVAL '7 days'
  AND t.id IS NULL  -- No refund found
ORDER BY v.created_at DESC;

-- Expected: Should be 0 (all failures should be refunded)
-- If > 0: CRITICAL - Users charged without refund


-- 5. AGGREGATE STATS - MONEY AT RISK
SELECT 
    COUNT(*) as total_unreceived,
    SUM(v.cost) as total_charged_usd,
    AVG(v.cost) as avg_cost,
    COUNT(DISTINCT v.user_id) as affected_users,
    v.service_name,
    v.status
FROM verifications v
WHERE v.status IN ('pending', 'failed', 'error')
  AND v.cost > 0
  AND v.sms_code IS NULL
  AND v.created_at > NOW() - INTERVAL '7 days'
GROUP BY v.service_name, v.status
ORDER BY total_charged_usd DESC;

-- Shows financial impact by service and status


-- 6. USER IMPACT REPORT
SELECT 
    u.id as user_id,
    u.email,
    COUNT(*) as failed_verifications,
    SUM(v.cost) as total_lost_usd,
    u.credits as current_balance,
    MAX(v.created_at) as last_failure
FROM verifications v
JOIN users u ON v.user_id = u.id
WHERE v.status IN ('pending', 'failed', 'error')
  AND v.cost > 0
  AND v.sms_code IS NULL
  AND v.created_at > NOW() - INTERVAL '7 days'
GROUP BY u.id, u.email, u.credits
HAVING COUNT(*) > 1  -- Users with multiple failures
ORDER BY total_lost_usd DESC;

-- Identifies users most affected by the issue


-- 7. REFUND CANDIDATES (AUTO-REFUND SCRIPT)
-- Use this to generate refund transactions
SELECT 
    v.id as verification_id,
    v.user_id,
    u.email,
    v.cost as refund_amount,
    v.service_name,
    v.status,
    v.created_at,
    CASE 
        WHEN v.status = 'pending' AND v.created_at < NOW() - INTERVAL '10 minutes' 
            THEN 'TIMEOUT_REFUND'
        WHEN v.status IN ('failed', 'error') 
            THEN 'FAILURE_REFUND'
        WHEN v.status = 'cancelled' 
            THEN 'CANCELLATION_REFUND'
    END as refund_reason
FROM verifications v
JOIN users u ON v.user_id = u.id
LEFT JOIN transactions t ON (
    t.user_id = v.user_id 
    AND t.transaction_type = 'refund'
    AND t.created_at > v.created_at
    AND ABS(t.amount - v.cost) < 0.01
)
WHERE v.cost > 0
  AND v.sms_code IS NULL
  AND v.created_at > NOW() - INTERVAL '7 days'
  AND t.id IS NULL  -- Not already refunded
  AND (
    (v.status = 'pending' AND v.created_at < NOW() - INTERVAL '10 minutes')
    OR v.status IN ('failed', 'error', 'cancelled')
  )
ORDER BY v.created_at DESC;

-- Use this list to process refunds
