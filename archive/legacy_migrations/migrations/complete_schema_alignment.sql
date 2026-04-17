-- ============================================================================
-- Complete Schema Alignment & Optimization Migration
-- Version: 4.4.2
-- Date: 2026-04-17
-- ============================================================================

-- PART 1: Missing Verification Fields
-- ============================================================================
ALTER TABLE verifications 
ADD COLUMN IF NOT EXISTS selected_from_alternatives BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS original_request VARCHAR,
ADD COLUMN IF NOT EXISTS routing_reason VARCHAR,
ADD COLUMN IF NOT EXISTS city_honoured BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS city_note VARCHAR;

-- Verify refund fields exist (from previous migration)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='verifications' AND column_name='refunded') THEN
        ALTER TABLE verifications 
        ADD COLUMN refunded BOOLEAN DEFAULT FALSE NOT NULL,
        ADD COLUMN refund_amount DOUBLE PRECISION,
        ADD COLUMN refund_reason VARCHAR,
        ADD COLUMN refund_transaction_id VARCHAR,
        ADD COLUMN refunded_at TIMESTAMP;
        
        CREATE INDEX IF NOT EXISTS idx_verifications_refunded ON verifications(refunded);
    END IF;
END $$;

-- PART 2: Analytics Cache Table (Performance Optimization)
-- ============================================================================
CREATE TABLE IF NOT EXISTS analytics_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_verifications INT DEFAULT 0,
    successful_verifications INT DEFAULT 0,
    failed_verifications INT DEFAULT 0,
    pending_verifications INT DEFAULT 0,
    total_spent NUMERIC(10,4) DEFAULT 0,
    avg_cost NUMERIC(10,4) DEFAULT 0,
    success_rate NUMERIC(5,2) DEFAULT 0,
    computed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_analytics_cache_user_period 
ON analytics_cache(user_id, period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_analytics_cache_computed 
ON analytics_cache(computed_at DESC);

-- PART 3: Performance Indexes
-- ============================================================================

-- History page optimization
CREATE INDEX IF NOT EXISTS idx_verifications_user_created 
ON verifications(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_verifications_user_status_created 
ON verifications(user_id, status, created_at DESC);

-- Carrier analytics optimization
CREATE INDEX IF NOT EXISTS idx_verifications_carrier_status 
ON verifications(assigned_carrier, status) 
WHERE assigned_carrier IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_verifications_area_code_matched 
ON verifications(area_code_matched, created_at) 
WHERE area_code_matched IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_carrier_analytics_lookup 
ON carrier_analytics(carrier_name, created_at DESC);

-- Refund queries optimization
CREATE INDEX IF NOT EXISTS idx_verifications_refund_status 
ON verifications(refunded, status, created_at DESC);

-- PART 4: Verification Events Table (Enhanced History)
-- ============================================================================
CREATE TABLE IF NOT EXISTS verification_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id UUID REFERENCES verifications(id) ON DELETE CASCADE,
    event_type VARCHAR NOT NULL, -- created, retry, timeout, completed, refunded, cancelled
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verification_events_verification 
ON verification_events(verification_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_verification_events_type 
ON verification_events(event_type, created_at DESC);

-- PART 5: Custom Reports Table (Future Enhancement)
-- ============================================================================
CREATE TABLE IF NOT EXISTS custom_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    report_name VARCHAR NOT NULL,
    report_type VARCHAR NOT NULL, -- daily, weekly, monthly, custom
    filters JSONB,
    schedule VARCHAR, -- cron expression
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_custom_reports_user 
ON custom_reports(user_id, enabled);

CREATE INDEX IF NOT EXISTS idx_custom_reports_schedule 
ON custom_reports(next_run) 
WHERE enabled = TRUE;

-- PART 6: Scheduled Reports Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES custom_reports(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    report_data JSONB,
    generated_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    status VARCHAR DEFAULT 'pending' -- pending, sent, failed
);

CREATE INDEX IF NOT EXISTS idx_scheduled_reports_user 
ON scheduled_reports(user_id, generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_scheduled_reports_status 
ON scheduled_reports(status, generated_at DESC);

-- PART 7: User Analytics Snapshots (Trend Analysis)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_verifications INT DEFAULT 0,
    successful_verifications INT DEFAULT 0,
    failed_verifications INT DEFAULT 0,
    total_spent NUMERIC(10,4) DEFAULT 0,
    avg_cost NUMERIC(10,4) DEFAULT 0,
    success_rate NUMERIC(5,2) DEFAULT 0,
    top_service VARCHAR,
    top_carrier VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_user_analytics_snapshots_user_date 
ON user_analytics_snapshots(user_id, snapshot_date DESC);

-- PART 8: Verification Statistics (Materialized View Alternative)
-- ============================================================================
CREATE TABLE IF NOT EXISTS verification_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stat_date DATE NOT NULL,
    total_verifications INT DEFAULT 0,
    successful_verifications INT DEFAULT 0,
    failed_verifications INT DEFAULT 0,
    total_revenue NUMERIC(10,4) DEFAULT 0,
    avg_cost NUMERIC(10,4) DEFAULT 0,
    unique_users INT DEFAULT 0,
    top_service VARCHAR,
    top_country VARCHAR,
    computed_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stat_date)
);

CREATE INDEX IF NOT EXISTS idx_verification_statistics_date 
ON verification_statistics(stat_date DESC);

-- PART 9: Data Validation
-- ============================================================================

-- Verify all critical columns exist
DO $$ 
DECLARE
    missing_cols TEXT[];
BEGIN
    SELECT ARRAY_AGG(col) INTO missing_cols
    FROM (
        SELECT unnest(ARRAY[
            'refunded', 'refund_amount', 'refund_reason', 'refund_transaction_id', 'refunded_at',
            'selected_from_alternatives', 'original_request', 'routing_reason', 
            'city_honoured', 'city_note'
        ]) AS col
    ) expected
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='verifications' AND column_name=col
    );
    
    IF array_length(missing_cols, 1) > 0 THEN
        RAISE EXCEPTION 'Missing columns in verifications table: %', array_to_string(missing_cols, ', ');
    END IF;
    
    RAISE NOTICE 'All verification columns verified successfully';
END $$;

-- PART 10: Summary Report
-- ============================================================================
SELECT 
    'Migration Complete' AS status,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name='verifications') AS verification_columns,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE') AS total_tables,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname='public') AS total_indexes;

-- Show new tables created
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name=t.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema='public' 
  AND table_type='BASE TABLE'
  AND table_name IN (
      'analytics_cache', 
      'verification_events', 
      'custom_reports', 
      'scheduled_reports',
      'user_analytics_snapshots',
      'verification_statistics'
  )
ORDER BY table_name;
