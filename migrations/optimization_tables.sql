-- ============================================================================
-- Complete Schema Alignment & Optimization Migration (Fixed)
-- Version: 4.4.2
-- Date: 2026-04-17
-- ============================================================================

-- PART 1: Analytics Cache Table (Performance Optimization)
-- ============================================================================
CREATE TABLE IF NOT EXISTS analytics_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL, -- Match users.id type
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

-- PART 2: Carrier Analytics Index Fix
-- ============================================================================
-- Check if carrier_analytics table exists and has carrier_name column
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='carrier_analytics') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='carrier_analytics' AND column_name='carrier_name') THEN
            CREATE INDEX IF NOT EXISTS idx_carrier_analytics_lookup 
            ON carrier_analytics(carrier_name, created_at DESC);
        END IF;
    END IF;
END $$;

-- PART 3: Verification Events Table (Enhanced History)
-- ============================================================================
CREATE TABLE IF NOT EXISTS verification_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_id VARCHAR NOT NULL, -- Match verifications.id type
    event_type VARCHAR NOT NULL, -- created, retry, timeout, completed, refunded, cancelled
    event_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verification_events_verification 
ON verification_events(verification_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_verification_events_type 
ON verification_events(event_type, created_at DESC);

-- PART 4: Custom Reports Table (Future Enhancement)
-- ============================================================================
CREATE TABLE IF NOT EXISTS custom_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL, -- Match users.id type
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

-- PART 5: Scheduled Reports Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID,
    user_id VARCHAR NOT NULL, -- Match users.id type
    report_data JSONB,
    generated_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    status VARCHAR DEFAULT 'pending' -- pending, sent, failed
);

CREATE INDEX IF NOT EXISTS idx_scheduled_reports_user 
ON scheduled_reports(user_id, generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_scheduled_reports_status 
ON scheduled_reports(status, generated_at DESC);

-- PART 6: User Analytics Snapshots (Trend Analysis)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL, -- Match users.id type
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

-- PART 7: Summary Report
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
