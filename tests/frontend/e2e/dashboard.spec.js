const { test, expect } = require('@playwright/test');
const jwt = require('jsonwebtoken');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

test.describe('Dashboard E2E', () => {
    // Run tests serially to prevent DB race conditions
    test.describe.configure({ mode: 'serial' });

    const SECRET = 'b1f2e3d4c5b6a798897a6b5c4d3e2f10';
    const dbPath = path.join(__dirname, '../../../e2e_final.db');

    test.beforeAll(async () => {
        // Setup database with test data
        const db = new sqlite3.Database(dbPath);

        await new Promise((resolve, reject) => {
            db.serialize(() => {
                // Clear existing data to ensure clean state
                db.run("DELETE FROM users WHERE id = '1'");
                db.run("DELETE FROM verifications WHERE user_id = '1'");
                db.run("DELETE FROM transactions WHERE user_id = '1'");

                // Insert User (Pay-As-You-Go Tier)
                db.run(`
                    INSERT INTO users (
                        id, email, password_hash, is_admin, is_moderator, 
                        credits, subscription_tier, created_at, free_verifications,
                        email_verified, bonus_sms_balance, monthly_quota_used,
                        referral_earnings, provider, language, currency,
                        is_affiliate, is_active, is_suspended, is_banned, is_deleted
                    ) VALUES (
                        '1', 'test@namaskah.app', 'hashed_password', 0, 0,
                        10.0, 'payg', datetime('now'), 1.0,
                        1, 0.0, 0.0,
                        0.0, 'email', 'en', 'USD',
                        0, 1, 0, 0, 0
                    )
                `);

                // Insert Verifications (1 Completed, 1 Pending)
                // Completed one
                db.run(`
                    INSERT INTO verifications (
                        id, user_id, service_name, phone_number, country, capability,
                        status, cost, created_at, completed_at, provider
                    ) VALUES (
                        'v1', '1', 'openai', '+15550101', 'US', 'sms',
                        'completed', 0.50, datetime('now', '-1 hour'), datetime('now', '-55 minutes'), 'test_provider'
                    )
                `);

                // Pending one
                db.run(`
                    INSERT INTO verifications (
                        id, user_id, service_name, phone_number, country, capability,
                        status, cost, created_at, provider
                    ) VALUES (
                        'v2', '1', 'google', '+15550102', 'US', 'sms',
                        'pending', 0.00, datetime('now', '-5 minutes'), 'test_provider'
                    )
                `);

                // Insert Transaction for the completed verification (Required for Total Spent analytics)
                db.run(`
                    INSERT INTO transactions (
                        id, user_id, amount, type, description, created_at
                    ) VALUES (
                        'tx1', '1', -0.50, 'SMS Verification', 'Verification for openai', datetime('now', '-55 minutes')
                    )
                `, (err) => {
                    if (err) reject(err);
                    else resolve();
                });
            });
        });

        db.close();
    });

    test.beforeEach(async ({ page }) => {
        const token = jwt.sign({ user_id: '1' }, SECRET, { algorithm: 'HS256' });

        // Add auth cookie
        await page.context().addCookies([
            {
                name: 'access_token',
                value: token,
                url: 'http://localhost:8000',
            }
        ]);

        // Inject token into localStorage
        await page.addInitScript(t => {
            window.localStorage.setItem('access_token', t);
        }, token);

        // Capture logs
        page.on('console', msg => console.log(`PAGE LOG [${msg.type()}]: ${msg.text()}`));
        page.on('pageerror', err => console.log(`PAGE ERROR: ${err.message}`));

        // Navigate
        await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
        await page.waitForLoadState('networkidle');
    });

    test('should display tier information correctly', async ({ page }) => {
        // Wait for Tier Card to load
        await expect(page.locator('#tier-name')).toContainText('Pay-As-You-Go', { timeout: 10000 });

        // Check for specific tier badge class WITHIN the tier card to avoid header badge conflict
        await expect(page.locator('#tier-card .tier-badge.tier-badge-payg')).toBeVisible();

        // Check for Add Credits button (specific to PAYG)
        await expect(page.locator('#add-credits-btn')).toBeVisible();
    });

    test('should display analytics stats from database', async ({ page }) => {
        // Validation of analytics summary
        // Total SMS: 2 (1 completed + 1 pending)
        // Successful: 1 (completed)
        // Total Spent: $0.50

        // Explicitly wait for the API call to populate
        await expect(page.locator('#total-sms')).toHaveText('2', { timeout: 10000 });
        await expect(page.locator('#successful-sms')).toHaveText('1');
        await expect(page.locator('#total-spent')).toContainText('0.50');
    });

    test('should show recent activity table', async ({ page }) => {
        // Wait for activity table to be visible
        await expect(page.locator('#activity-table')).toBeVisible({ timeout: 10000 });

        // Check rows
        const table = page.locator('#activity-table');
        await expect(table).toContainText('openai');
        await expect(table).toContainText('google');

        // Check status colors/text
        await expect(table).toContainText('completed');
        await expect(table).toContainText('pending');
    });
});
