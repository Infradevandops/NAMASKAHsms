const { test, expect } = require('@playwright/test');
const jwt = require('jsonwebtoken');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

test.describe('Settings Page', () => {
    const SECRET = 'b1f2e3d4c5b6a798897a6b5c4d3e2f10';
    const dbPath = path.join(__dirname, '../../../e2e_final.db');

    test.beforeAll(async () => {
        // Create test user in database
        const db = new sqlite3.Database(dbPath);

        await new Promise((resolve, reject) => {
            db.run(`
                INSERT OR REPLACE INTO users (
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
            `, (err) => {
                if (err) reject(err);
                else resolve();
            });
        });

        db.close();
    });

    test.beforeEach(async ({ page }) => {
        const token = jwt.sign({ user_id: '1' }, SECRET, { algorithm: 'HS256' });

        // Debug: Log all page console output
        page.on('console', msg => console.log(`PAGE LOG [${msg.type()}]: ${msg.text()}`));
        page.on('pageerror', err => console.log(`PAGE ERROR: ${err.message}`));

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

        // Navigate
        console.log('Navigating to /settings...');
        await page.goto('/settings', { waitUntil: 'domcontentloaded' });

        // Wait for network idle
        await page.waitForLoadState('networkidle');

        // Debug: Inspect DOM state
        const emailExists = await page.locator('#account-email').count();
        console.log(`DEBUG: #account-email elements found: ${emailExists}`);

        // Wait longer for JS execution
        await page.waitForTimeout(3000);
    });

    test('should display account information', async ({ page }) => {
        // Wait for the value to be populated
        await expect(page.locator('#account-email')).toHaveValue('test@namaskah.app', { timeout: 10000 });
        await expect(page.locator('#account-id')).toHaveValue('1', { timeout: 10000 });
    });

    test('should switch tabs correctly', async ({ page }) => {
        // Switch to Security tab
        await page.click('button:has-text("Security")');
        await expect(page.locator('#security-tab')).toBeVisible();
        await expect(page.locator('#account-tab')).not.toBeVisible();

        // Switch to Notifications tab
        await page.click('button:has-text("Notifications")');
        await expect(page.locator('#notifications-tab')).toBeVisible();
    });

    test('should display billing information', async ({ page }) => {
        await page.click('button:has-text("Billing")');
        await expect(page.locator('#billing-tab')).toBeVisible();
    });

    test('should show API keys tab for payg tier', async ({ page }) => {
        // Wait for tier loading to complete and tab to appear
        // The loadUserTierForSettings function runs on page load, we should wait for its result
        await expect(page.locator('button:has-text("API Keys")')).toBeVisible({ timeout: 10000 });
    });
});
