-- Create admin user directly in production database
-- Run this in Render.com PostgreSQL shell

INSERT INTO users (
    id,
    email,
    password_hash,
    credits,
    free_verifications,
    is_admin,
    is_moderator,
    email_verified,
    subscription_tier,
    bonus_sms_balance,
    monthly_quota_used,
    referral_earnings,
    provider,
    failed_login_attempts,
    language,
    currency,
    is_active,
    is_affiliate,
    created_at
) VALUES (
    gen_random_uuid(),
    'admin@namaskah.app',
    '$2b$12$vFQWKP1CyJa/r8NvF1ZvjeipjzTNhd0AwcENr0tc82WBFdDU4uPfW',
    10000.0,
    1000.0,
    true,
    false,
    true,
    'custom',
    0.0,
    0.0,
    0.0,
    'email',
    0,
    'en',
    'USD',
    true,
    false,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    is_admin = true,
    is_active = true,
    subscription_tier = 'custom',
    credits = GREATEST(users.credits, 10000.0);
