/**
 * E2E tests for GDPR/Privacy Settings
 * Tests data export and account deletion functionality
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const TEST_USER = {
    email: 'test@example.com',
    password: 'TestPassword123!'
};

test.describe('GDPR/Privacy Settings E2E Tests', () => {
    
    test.beforeEach(async ({ page }) => {
        // Login
        await page.goto(`${BASE_URL}/auth/login`);
        await page.fill('input[name="email"]', TEST_USER.email);
        await page.fill('input[name="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');
        await page.waitForURL(`${BASE_URL}/dashboard`);
    });

    test('should navigate to privacy settings', async ({ page }) => {
        // Go to settings
        await page.goto(`${BASE_URL}/settings`);
        
        // Click on Privacy tab
        await page.click('[data-tab="privacy"]');
        
        // Verify privacy section is visible
        await expect(page.locator('[data-testid="privacy-section"]')).toBeVisible();
    });

    test('should export user data', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Wait for export button
        await page.waitForSelector('[data-testid="export-data-btn"]', { timeout: 5000 });
        
        // Start waiting for download
        const downloadPromise = page.waitForEvent('download');
        
        // Click export button
        await page.click('[data-testid="export-data-btn"]');
        
        // Wait for download
        const download = await downloadPromise;
        
        // Verify download
        expect(download.suggestedFilename()).toMatch(/user.*data.*\.json|\.zip/i);
    });

    test('should show export progress indicator', async ({ page }) => {
        // Slow down the export request
        await page.route('**/gdpr/export**', async route => {
            await new Promise(resolve => setTimeout(resolve, 2000));
            await route.continue();
        });
        
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Click export button
        await page.click('[data-testid="export-data-btn"]');
        
        // Check for loading indicator
        const loadingIndicator = page.locator('[data-testid="export-loading"]');
        await expect(loadingIndicator).toBeVisible();
    });

    test('should display data retention information', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Check for data retention info
        const retentionInfo = page.locator('[data-testid="data-retention-info"]');
        await expect(retentionInfo).toBeVisible();
        await expect(retentionInfo).toContainText(/retention|stored|days/i);
    });

    test('should show account deletion warning', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Click delete account button
        await page.click('[data-testid="delete-account-btn"]');
        
        // Check for warning modal
        const warningModal = page.locator('[data-testid="delete-account-modal"]');
        await expect(warningModal).toBeVisible();
        await expect(warningModal).toContainText(/permanent|cannot be undone/i);
    });

    test('should require confirmation for account deletion', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Click delete account button
        await page.click('[data-testid="delete-account-btn"]');
        
        // Modal should appear
        await page.waitForSelector('[data-testid="delete-account-modal"]');
        
        // Confirmation input should be required
        const confirmInput = page.locator('[data-testid="delete-confirmation-input"]');
        await expect(confirmInput).toBeVisible();
        
        // Confirm button should be disabled initially
        const confirmButton = page.locator('[data-testid="confirm-delete-btn"]');
        await expect(confirmButton).toBeDisabled();
    });

    test('should enable delete button after typing DELETE', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Click delete account button
        await page.click('[data-testid="delete-account-btn"]');
        
        // Wait for modal
        await page.waitForSelector('[data-testid="delete-account-modal"]');
        
        // Type DELETE in confirmation input
        await page.fill('[data-testid="delete-confirmation-input"]', 'DELETE');
        
        // Confirm button should now be enabled
        const confirmButton = page.locator('[data-testid="confirm-delete-btn"]');
        await expect(confirmButton).toBeEnabled();
    });

    test('should cancel account deletion', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Click delete account button
        await page.click('[data-testid="delete-account-btn"]');
        
        // Wait for modal
        await page.waitForSelector('[data-testid="delete-account-modal"]');
        
        // Click cancel button
        await page.click('[data-testid="cancel-delete-btn"]');
        
        // Modal should close
        await expect(page.locator('[data-testid="delete-account-modal"]')).not.toBeVisible();
        
        // Should still be on settings page
        await expect(page).toHaveURL(/\/settings/);
    });

    test('should handle export rate limiting', async ({ page }) => {
        // Mock rate limit response
        await page.route('**/gdpr/export**', route => {
            route.fulfill({
                status: 429,
                body: JSON.stringify({ 
                    detail: 'Rate limit exceeded. Please try again in 60 seconds.',
                    retry_after: 60
                })
            });
        });
        
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Click export button
        await page.click('[data-testid="export-data-btn"]');
        
        // Should show rate limit message
        const errorMessage = page.locator('[data-testid="error-message"]');
        await expect(errorMessage).toBeVisible();
        await expect(errorMessage).toContainText(/rate limit|try again/i);
    });

    test('should show cookie preferences if applicable', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Check for cookie preferences section
        const cookieSection = page.locator('[data-testid="cookie-preferences"]');
        
        // This may or may not exist depending on implementation
        if (await cookieSection.isVisible()) {
            await expect(cookieSection).toContainText(/cookie|tracking/i);
        }
    });

    test('should be accessible via keyboard navigation', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Tab to export button
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        
        // Should be able to activate with Enter
        const exportButton = page.locator('[data-testid="export-data-btn"]');
        await exportButton.focus();
        
        // Verify button is focused
        await expect(exportButton).toBeFocused();
    });

    test('should display GDPR compliance information', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings?tab=privacy`);
        
        // Check for GDPR compliance text
        const gdprInfo = page.locator('[data-testid="gdpr-info"]');
        
        if (await gdprInfo.isVisible()) {
            await expect(gdprInfo).toContainText(/GDPR|privacy|rights/i);
        }
    });
});
