/**
 * E2E tests for Analytics Page
 * Tests the complete user journey for viewing analytics
 */

const { test, expect } = require('@playwright/test');

// Test configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const TEST_USER = {
    email: 'test@example.com',
    password: 'TestPassword123!'
};

test.describe('Analytics Page E2E Tests', () => {
    
    test.beforeEach(async ({ page }) => {
        // Login before each test
        await page.goto(`${BASE_URL}/auth/login`);
        await page.fill('input[name="email"]', TEST_USER.email);
        await page.fill('input[name="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');
        
        // Wait for redirect to dashboard
        await page.waitForURL(`${BASE_URL}/dashboard`);
    });

    test('should load analytics page successfully', async ({ page }) => {
        // Navigate to analytics
        await page.goto(`${BASE_URL}/analytics`);
        
        // Check page title
        await expect(page.locator('h1')).toContainText('Analytics');
        
        // Check that main sections are visible
        await expect(page.locator('[data-testid="summary-cards"]')).toBeVisible();
    });

    test('should display summary metrics', async ({ page }) => {
        await page.goto(`${BASE_URL}/analytics`);
        
        // Wait for data to load
        await page.waitForSelector('[data-testid="total-verifications"]', { timeout: 5000 });
        
        // Check summary cards exist
        const totalVerifications = page.locator('[data-testid="total-verifications"]');
        const successRate = page.locator('[data-testid="success-rate"]');
        const totalSpending = page.locator('[data-testid="total-spending"]');
        
        await expect(totalVerifications).toBeVisible();
        await expect(successRate).toBeVisible();
        await expect(totalSpending).toBeVisible();
    });

    test('should display charts', async ({ page }) => {
        await page.goto(`${BASE_URL}/analytics`);
        
        // Wait for charts to render
        await page.waitForSelector('canvas', { timeout: 10000 });
        
        // Check that at least one chart is rendered
        const charts = page.locator('canvas');
        const chartCount = await charts.count();
        expect(chartCount).toBeGreaterThan(0);
    });

    test('should filter by date range', async ({ page }) => {
        await page.goto(`${BASE_URL}/analytics`);
        
        // Wait for page to load
        await page.waitForSelector('[data-testid="date-range-filter"]', { timeout: 5000 });
        
        // Select 7 days filter
        await page.click('[data-testid="date-range-filter"]');
        await page.click('[data-value="7"]');
        
        // Wait for data to reload
        await page.waitForTimeout(1000);
        
        // Verify filter is applied
        const activeFilter = page.locator('[data-testid="date-range-filter"] .active');
        await expect(activeFilter).toContainText('7 days');
    });

    test('should export data as CSV', async ({ page }) => {
        await page.goto(`${BASE_URL}/analytics`);
        
        // Wait for export button
        await page.waitForSelector('[data-testid="export-csv-btn"]', { timeout: 5000 });
        
        // Start waiting for download before clicking
        const downloadPromise = page.waitForEvent('download');
        
        // Click export button
        await page.click('[data-testid="export-csv-btn"]');
        
        // Wait for download
        const download = await downloadPromise;
        
        // Verify download
        expect(download.suggestedFilename()).toMatch(/analytics.*\.csv/);
    });

    test('should handle empty state gracefully', async ({ page }) => {
        // This test assumes a new user with no data
        // You may need to create a fresh test user or mock the API
        
        await page.goto(`${BASE_URL}/analytics`);
        
        // Check for empty state message or zero values
        const totalVerifications = page.locator('[data-testid="total-verifications"]');
        const text = await totalVerifications.textContent();
        
        // Should show 0 or empty state message
        expect(text).toMatch(/0|No data/i);
    });

    test('should be responsive on mobile', async ({ page }) => {
        // Set mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });
        
        await page.goto(`${BASE_URL}/analytics`);
        
        // Check that page is still functional
        await expect(page.locator('h1')).toBeVisible();
        
        // Check that cards stack vertically (mobile layout)
        const summaryCards = page.locator('[data-testid="summary-card"]');
        const firstCard = summaryCards.first();
        const secondCard = summaryCards.nth(1);
        
        const firstBox = await firstCard.boundingBox();
        const secondBox = await secondCard.boundingBox();
        
        // On mobile, second card should be below first card
        if (firstBox && secondBox) {
            expect(secondBox.y).toBeGreaterThan(firstBox.y + firstBox.height);
        }
    });

    test('should navigate back to dashboard', async ({ page }) => {
        await page.goto(`${BASE_URL}/analytics`);
        
        // Click dashboard link in sidebar
        await page.click('a[href="/dashboard"]');
        
        // Verify navigation
        await page.waitForURL(`${BASE_URL}/dashboard`);
        await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
    });

    test('should show loading state while fetching data', async ({ page }) => {
        // Slow down network to see loading state
        await page.route('**/api/analytics/**', async route => {
            await new Promise(resolve => setTimeout(resolve, 2000));
            await route.continue();
        });
        
        await page.goto(`${BASE_URL}/analytics`);
        
        // Check for loading skeleton or spinner
        const loadingIndicator = page.locator('[data-testid="loading-skeleton"], .spinner, .loading');
        await expect(loadingIndicator).toBeVisible();
    });

    test('should handle API errors gracefully', async ({ page }) => {
        // Mock API error
        await page.route('**/api/analytics/summary', route => {
            route.fulfill({
                status: 500,
                body: JSON.stringify({ detail: 'Internal server error' })
            });
        });
        
        await page.goto(`${BASE_URL}/analytics`);
        
        // Check for error message
        const errorMessage = page.locator('[data-testid="error-message"], .error-message');
        await expect(errorMessage).toBeVisible();
        await expect(errorMessage).toContainText(/error|failed/i);
    });
});

test.describe('Analytics Page - Authenticated Access', () => {
    
    test('should redirect to login if not authenticated', async ({ page }) => {
        // Try to access analytics without logging in
        await page.goto(`${BASE_URL}/analytics`);
        
        // Should redirect to login
        await page.waitForURL(/\/auth\/login/);
        await expect(page).toHaveURL(/\/auth\/login/);
    });

    test('should maintain session across page refreshes', async ({ page }) => {
        // Login
        await page.goto(`${BASE_URL}/auth/login`);
        await page.fill('input[name="email"]', TEST_USER.email);
        await page.fill('input[name="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');
        await page.waitForURL(`${BASE_URL}/dashboard`);
        
        // Navigate to analytics
        await page.goto(`${BASE_URL}/analytics`);
        
        // Refresh page
        await page.reload();
        
        // Should still be on analytics page (not redirected to login)
        await expect(page).toHaveURL(`${BASE_URL}/analytics`);
        await expect(page.locator('h1')).toContainText('Analytics');
    });
});
