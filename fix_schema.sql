-- Add missing columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS provider VARCHAR(50) DEFAULT 'email';
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS affiliate_id VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS partner_type VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS commission_tier VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_affiliate BOOLEAN DEFAULT false;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_affiliate_id ON users(affiliate_id);
