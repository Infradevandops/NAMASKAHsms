import { test, expect } from '@playwright/test';

test.describe('Authentication Page', () => {
    test('should display login form', async ({ page }) => {
        await page.goto('/auth/login');
        await expect(page.locator('#login-form')).toBeVisible();
        await expect(page.locator('#email')).toBeVisible();
        await expect(page.locator('#password')).toBeVisible();
    });

    test('should show error on invalid credentials', async ({ page }) => {
        await page.goto('/auth/login');
        await page.fill('#email', 'wrong@example.com');
        await page.fill('#password', 'wrongpass');
        await page.click('#login-btn');

        // Expect error message
        await expect(page.locator('#error-message')).toBeVisible();
        await expect(page.locator('#error-message')).toContainText('Invalid credentials');
    });
});
