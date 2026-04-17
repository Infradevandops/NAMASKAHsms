-- Add refund tracking fields to verifications table
-- Run this BEFORE deploying the refund policy enforcer

-- Add refund tracking columns
ALTER TABLE verifications 
ADD COLUMN IF NOT EXISTS refunded BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS refund_amount FLOAT,
ADD COLUMN IF NOT EXISTS refund_reason VARCHAR(255),
ADD COLUMN IF NOT EXISTS refund_transaction_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMP;

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS ix_verifications_refunded ON verifications(refunded);

-- Verify columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'verifications'
  AND column_name IN ('refunded', 'refund_amount', 'refund_reason', 'refund_transaction_id', 'refunded_at')
ORDER BY column_name;

-- Expected output:
-- column_name            | data_type | is_nullable | column_default
-- ----------------------|-----------|-------------|---------------
-- refund_amount         | double    | YES         | NULL
-- refund_reason         | varchar   | YES         | NULL
-- refund_transaction_id | varchar   | YES         | NULL
-- refunded              | boolean   | NO          | false
-- refunded_at           | timestamp | YES         | NULL
