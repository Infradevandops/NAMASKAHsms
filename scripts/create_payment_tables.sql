-- Create payment_logs table with idempotency and state machine
-- Phase 1: Database Schema Updates

BEGIN;

-- Create payment_logs table if not exists
CREATE TABLE IF NOT EXISTS payment_logs (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL,
    email VARCHAR,
    reference VARCHAR UNIQUE NOT NULL,
    amount_ngn FLOAT,
    amount_usd FLOAT,
    namaskah_amount FLOAT,
    status VARCHAR,
    payment_method VARCHAR,
    webhook_received BOOLEAN DEFAULT FALSE NOT NULL,
    credited BOOLEAN DEFAULT FALSE NOT NULL,
    error_message VARCHAR,
    
    -- Idempotency and state machine
    idempotency_key VARCHAR UNIQUE,
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    state VARCHAR(20) DEFAULT 'pending',
    state_transitions JSONB,
    lock_version INTEGER DEFAULT 0 NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_payment_logs_user_id ON payment_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_payment_logs_reference ON payment_logs(reference);
CREATE INDEX IF NOT EXISTS ix_payment_logs_status ON payment_logs(status);
CREATE INDEX IF NOT EXISTS ix_payment_logs_idempotency_key ON payment_logs(idempotency_key);
CREATE INDEX IF NOT EXISTS ix_payment_logs_state ON payment_logs(state);

-- Update existing transactions table (SMS platform)
-- Note: This is separate from the card transactions table
CREATE TABLE IF NOT EXISTS sms_transactions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL,
    amount FLOAT NOT NULL,
    type VARCHAR NOT NULL,
    description VARCHAR,
    tier VARCHAR,
    service VARCHAR,
    filters VARCHAR,
    status VARCHAR DEFAULT 'completed',
    
    -- Idempotency and linking
    reference VARCHAR UNIQUE,
    idempotency_key VARCHAR UNIQUE,
    payment_log_id VARCHAR,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_sms_transactions_user_id ON sms_transactions(user_id);
CREATE INDEX IF NOT EXISTS ix_sms_transactions_type ON sms_transactions(type);
CREATE INDEX IF NOT EXISTS ix_sms_transactions_reference ON sms_transactions(reference);
CREATE INDEX IF NOT EXISTS ix_sms_transactions_idempotency_key ON sms_transactions(idempotency_key);
CREATE INDEX IF NOT EXISTS ix_sms_transactions_payment_log_id ON sms_transactions(payment_log_id);

COMMIT;

-- Verify
SELECT 'payment_logs table created' as status;
SELECT 'sms_transactions table created' as status;
