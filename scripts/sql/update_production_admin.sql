-- Update Admin User Credentials in Production
-- Run this in Render PostgreSQL console or via psql

-- Step 1: Check current admin user
SELECT id, email, is_admin, credits, subscription_tier
FROM users
WHERE is_admin = true OR email LIKE '%admin%';

-- Step 2: Update admin email and ensure admin privileges
-- Replace 'ADMIN_USER_ID_HERE' with the actual ID from Step 1
UPDATE users
SET
    email = 'admin@vrenum.app',
    is_admin = true,
    email_verified = true,
    is_active = true,
    updated_at = NOW()
WHERE is_admin = true OR email LIKE '%admin%';

-- Step 3: Verify the update
SELECT id, email, is_admin, email_verified, credits, subscription_tier
FROM users
WHERE email = 'admin@vrenum.app';

-- Note: Password must be updated via Python script with bcrypt
-- The password hash for 'Namaskah@Admin2024' needs to be generated and updated separately
