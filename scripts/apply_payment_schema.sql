-- Payment Hardening: Add Idempotency and State Machine
-- Phase 1: Database Schema Updates

BEGIN;

-- Add to transactions table
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS reference VARCHAR UNIQUE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR UNIQUE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS payment_log_id VARCHAR;

CREATE INDEX IF NOT EXISTS ix_transactions_reference ON transactions(reference);
CREATE INDEX IF NOT EXISTS ix_transactions_idempotency_key ON transactions(idempotency_key);
CREATE INDEX IF NOT EXISTS ix_transactions_payment_log_id ON transactions(payment_log_id);

-- Add to payment_logs table
ALTER TABLE payment_logs ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR UNIQUE;
ALTER TABLE payment_logs ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP;
ALTER TABLE payment_logs ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP;
ALTER TABLE payment_logs ADD COLUMN IF NOT EXISTS state VARCHAR(20) DEFAULT 'pending';
ALTER TABLE payment_logs ADD COLUMN IF NOT EXISTS state_transitions JSONB;
ALTER TABLE payment_logs ADD COLUMN IF NOT EXISTS lock_version INTEGER DEFAULT 0 NOT NULL;

CREATE INDEX IF NOT EXISTS ix_payment_logs_idempotency_key ON payment_logs(idempotency_key);
CREATE INDEX IF NOT EXISTS ix_payment_logs_state ON payment_logs(state);

COMMIT;

-- Verify changes
SELECT 'transactions columns:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'transactions' 
AND column_name IN ('reference', 'idempotency_key', 'payment_log_id');

SELECT 'payment_logs columns:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'payment_logs' 
AND column_name IN ('idempotency_key', 'processing_started_at', 'processing_completed_at', 'state', 'state_transitions', 'lock_version');
