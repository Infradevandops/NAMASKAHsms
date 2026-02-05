import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
  });

  test('should load login page successfully', async ({ page }) => {
    await expect(page).toHaveTitle(/Login/);
    await expect(page.locator('h1, .auth-tab.active')).toContainText(/Login/i);
  });

  test('should display all form elements', async ({ page }) => {
    // Check email input
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#email')).toHaveAttribute('type', 'email');
    
    // Check password input
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('#password')).toHaveAttribute('type', 'password');
    
    // Check remember me checkbox
    await expect(page.locator('#remember')).toBeVisible();
    
    // Check submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toContainText(/Sign In/i);
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    // Try to submit without filling fields
    await page.click('button[type="submit"]');
    
    // Browser validation should prevent submission
    const emailInput = page.locator('#email');
    const isInvalid = await emailInput.evaluate((el) => !el.validity.valid);
    expect(isInvalid).toBeTruthy();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    // Fill in credentials
    await page.fill('#email', 'admin@namaskah.app');
    await page.fill('#password', 'Namaskah@Admin2024');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Wait for navigation to dashboard
    await page.waitForURL(/dashboard/, { timeout: 10000 });
    
    // Verify we're on dashboard
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill in wrong credentials
    await page.fill('#email', 'wrong@example.com');
    await page.fill('#password', 'wrongpassword');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Wait for error message
    await page.waitForSelector('#error-message', { state: 'visible', timeout: 5000 });
    
    // Check error message
    const errorMsg = page.locator('#error-message');
    await expect(errorMsg).toBeVisible();
    await expect(errorMsg).toContainText(/Invalid/i);
  });

  test('should toggle password visibility', async ({ page }) => {
    const passwordInput = page.locator('#password');
    const toggleButton = page.locator('button[title*="password"]');
    
    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click toggle button
    await toggleButton.click();
    
    // Password should now be visible
    await expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click again to hide
    await toggleButton.click();
    
    // Password should be hidden again
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should remember me checkbox work', async ({ page }) => {
    const checkbox = page.locator('#remember');
    
    // Checkbox should be checked by default
    await expect(checkbox).toBeChecked();
    
    // Uncheck it
    await checkbox.uncheck();
    await expect(checkbox).not.toBeChecked();
    
    // Check it again
    await checkbox.check();
    await expect(checkbox).toBeChecked();
  });

  test('should have forgot password link', async ({ page }) => {
    const forgotLink = page.locator('a[href="/auth/forgot-password"]');
    await expect(forgotLink).toBeVisible();
    await expect(forgotLink).toContainText(/Forgot password/i);
  });

  test('should have sign up link', async ({ page }) => {
    const signUpTab = page.locator('.auth-tab').filter({ hasText: /Sign Up/i });
    await expect(signUpTab).toBeVisible();
    
    // Click sign up tab
    await signUpTab.click();
    
    // Should navigate to register page
    await expect(page).toHaveURL(/register/);
  });

  test('should display social login buttons', async ({ page }) => {
    // Check for social login buttons
    const googleButton = page.locator('button[title*="Google"]');
    const facebookButton = page.locator('button[title*="Facebook"]');
    const linkedinButton = page.locator('button[title*="LinkedIn"]');
    
    await expect(googleButton).toBeVisible();
    await expect(facebookButton).toBeVisible();
    await expect(linkedinButton).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that form is still visible and usable
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Form should fit in viewport
    const formContainer = page.locator('.auth-container');
    const boundingBox = await formContainer.boundingBox();
    expect(boundingBox.width).toBeLessThanOrEqual(375);
  });

  test('should handle slow network gracefully', async ({ page }) => {
    // Simulate slow network
    await page.route('**/api/auth/login', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.continue();
    });
    
    // Fill and submit
    await page.fill('#email', 'admin@namaskah.app');
    await page.fill('#password', 'Namaskah@Admin2024');
    await page.click('button[type="submit"]');
    
    // Button should show loading state
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toContainText(/Signing in/i);
    await expect(submitButton).toBeDisabled();
  });
});
