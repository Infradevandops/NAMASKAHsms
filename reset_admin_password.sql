-- Reset admin password to Admin123!
-- Password hash for: Admin123!
UPDATE users 
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfQC0mQeyy',
    is_admin = true,
    email_verified = true,
    credits = 1000.0
WHERE email = 'admin@namaskah.app';
