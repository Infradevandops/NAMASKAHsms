-- Create admin user directly in database
-- Run this in your production database

INSERT INTO users (id, email, password_hash, credits, is_admin, email_verified, created_at)
VALUES (
    'user_admin_' || substr(md5(random()::text), 1, 16),
    'admin@namaskah.app',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfQC0mQeyy', -- Hash for: NamaskahAdmin2024!
    1000.0,
    true,
    true,
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    is_admin = true,
    credits = 1000.0,
    email_verified = true;
