const { test, expect } = require('@playwright/test');

describe('Service Loading Error Flow - E2E', () => {
    beforeEach(async ({ page }) => {
        // Mock API to fail
        await page.route('**/api/countries/US/services', route => {
            route.fulfill({
                status: 503,
                body: JSON.stringify({error: 'Service unavailable'})
            });
        });
        
        await page.goto('/verify');
    });
    
    test('should show error toast on page load', async ({ page }) => {
        const toast = await page.locator('.toast-error').textContent();
        expect(toast).toContain('Unable to load services from provider');
    });
    
    test('should disable service input', async ({ page }) => {
        const input = await page.locator('#service-search-input');
        expect(await input.isDisabled()).toBe(true);
    });
    
    test('should not open modal when clicking disabled input', async ({ page }) => {
        await page.click('#service-search-input');
        
        const modal = await page.locator('#immersive-modal-container');
        expect(await modal.innerHTML()).toBe('');
    });
    
    test('should show retry button after enabling API', async ({ page }) => {
        // Enable API
        await page.route('**/api/countries/US/services', route => {
            route.fulfill({
                status: 200,
                body: JSON.stringify({
                    services: [{id: 'telegram', name: 'Telegram', price: 2.50}],
                    total: 1
                })
            });
        });
        
        // Manually trigger retry (simulate user action)
        await page.evaluate(() => retryLoadServices());
        
        // Wait for services to load
        await page.waitForTimeout(1000);
        
        const input = await page.locator('#service-search-input');
        expect(await input.isDisabled()).toBe(false);
    });
    
    test('should open modal successfully after retry', async ({ page }) => {
        // Enable API and retry
        await page.route('**/api/countries/US/services', route => {
            route.fulfill({
                status: 200,
                body: JSON.stringify({
                    services: [{id: 'telegram', name: 'Telegram', price: 2.50}],
                    total: 1
                })
            });
        });
        
        await page.evaluate(() => retryLoadServices());
        await page.waitForTimeout(1000);
        
        await page.click('#service-search-input');
        
        const modal = await page.locator('#immersive-modal-container');
        expect(await modal.innerHTML()).not.toBe('');
    });
});
