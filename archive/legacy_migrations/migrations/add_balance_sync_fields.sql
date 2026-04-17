-- Add balance sync tracking for admin users
-- Migration: add_balance_sync_fields
-- Date: 2026-03-30

-- Add balance sync timestamp for admin users
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS balance_last_synced TIMESTAMP WITH TIME ZONE;

-- Add metadata column to transactions for richer analytics
ALTER TABLE sms_transactions 
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Create index for faster transaction queries
CREATE INDEX IF NOT EXISTS idx_transactions_user_type 
ON sms_transactions(user_id, type, created_at DESC);

-- Create index for balance sync tracking
CREATE INDEX IF NOT EXISTS idx_users_admin_sync 
ON users(is_admin, balance_last_synced) 
WHERE is_admin = true;

-- Add comment for documentation
COMMENT ON COLUMN users.balance_last_synced IS 'Last time admin balance was synced from TextVerified API';
COMMENT ON COLUMN sms_transactions.metadata IS 'Additional transaction metadata for analytics (JSONB)';
