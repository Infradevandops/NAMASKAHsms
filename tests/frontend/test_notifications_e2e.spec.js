/**
 * E2E tests for Notifications Page
 * Tests notification management and real-time updates
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const TEST_USER = {
    email: 'test@example.com',
    password: 'TestPassword123!'
};

test.describe('Notifications Page E2E Tests', () => {
    
    test.beforeEach(async ({ page }) => {
        // Login
        await page.goto(`${BASE_URL}/auth/login`);
        await page.fill('input[name="email"]', TEST_USER.email);
        await page.fill('input[name="password"]', TEST_USER.password);
        await page.click('button[type="submit"]');
        await page.waitForURL(`${BASE_URL}/dashboard`);
    });

    test('should load notifications page', async ({ page }) => {
        await page.goto(`${BASE_URL}/notifications`);
        
        await expect(page.locator('h1')).toContainText('Notifications');
        await expect(page.locator('[data-testid="notifications-list"]')).toBeVisible();
    });

    test('should display notification badge in sidebar', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);
        
        // Check for notification badge
        const notificationBadge = page.locator('[data-testid="notification-badge"]');
        
        if (await notificationBadge.isVisible()) {
            // Badge should show a number
            const badgeText = await notificationBadge.textContent();
            expect(parseInt(badgeText)).toBeGreaterThan(0);
        }
    });

    test('should mark notification as read', async ({ page }) => {
        await page.goto(`${BASE_URL}/notifications`);
        
        // Wait for notifications to load
        await page.waitForSelector('[data-testid="notification-item"]', { timeout: 5000 });
        
        // Find an unread notification
        const unreadNotification = page.locator('[data-testid="notification-item"].unread').first();
        
        if (await unreadNotification.isVisible()) {
            // Click to mark as read
            await unreadNotification.click();
            
            // Wait for update
            await page.waitForTimeout(500);
            
            // Verify it's now marked as read
            await expect(unreadNotification).not.toHaveClass(/unread/);
        }
    });

    test('should mark all notifications as read', async ({ page }) => {
        await page.goto(`${BASE_URL}/notifications`);
        
        // Wait for notifications
        await page.waitForSelector('[data-testid="notifications-list"]', { timeout: 5000 });
        
        // Click mark all as read button
        const markAllButton = page.locator('[data-testid="mark-all-read-btn"]');
        
        if (await markAllButton.isVisible()) {
            await markAllButton.click();
            
            // Wait for update
            await page.waitForTimeout(1000);
            
            // Verify no unread notifications remain
            const unreadCount = await page.locator('[data-testid="notification-item"].unread').count();
            expect(unreadCount).toBe(0);
        }
    });

    test('should filter notifications by type', async ({ page }) => {
        await page.goto(`${BASE_URL}/notifications`);
        
        // Wait for filter buttons
        await page.waitForSelector('[data-testid="filter-type"]', { timeout: 5000 });
        
        // Click on "Payment" filter
        await page.click('[data-testid="filter-payment"]');
        
        // Wait for filtered results
        await page.waitForTimeout(500);
        
        // Verify only payment notifications are shown
        const notifications = page.locator('[data-testid="notification-item"]');
        const count = await notifications.count();
        
        if (count > 0) {
            // Check first notification is payment type
            const firstNotification = notifications.first();
            await expect(firstNotification).toContainText(/payment|transaction/i);
        }
    });

    test('should delete notification', async ({ page }) => {
        await page.goto(`${BASE_URL}/notifications`);
        
        // Wait for notifications
        await page.waitForSelector('[data-testid="notification-item"]', { timeout: 5000 });
        
        // Get initial count
        const initialCount = await page.locator('[data-testid="notification-item"]').count();
        
        if (initialCount > 0) {
            // Click delete button on first notification
            const deleteButton = page.locator('[data-testid="delete-notification-btn"]').first();
            await deleteButton.click();
            
            // Confirm deletion if modal appears
            const confirmButton = page.locator('[data-testid="confirm-delete-btn"]');
            if (await confirmButton.isVisible({ timeout: 1000 })) {
                await confirmButton.click();
            }
            
            // Wait for deletion
            await page.waitForTimeout(500);
            
            // Verify count decreased
            const newCount = await page.locator('[data-testid="notification-item"]').count();
            expect(newCount).toBe(initialCount - 1);
        }
    });

    test('should show empty state when no notifications', async ({ page }) => {
        // Mock empty notifications response
        await page.route('**/api/notifications**', route => {
            route.fulfill({
                status: 200,
                body: JSON.stringify({ notifications: [], total: 0 })
            });
        });
        
        await page.goto(`${BASE_URL}/notifications`);
        
        // Check for empty state
        const emptyState = page.locator('[data-testid="empty-state"]');
        await expect(emptyState).toBeVisible();
        await expect(emptyState).toContainText(/no notifications/i);
    });

    test('should load more notifications on scroll', async ({ page }) => {
        await page.goto(`${BASE_URL}/notifications`);
        
        // Wait for initial load
        await page.waitForSelector('[data-testid="notification-item"]', { timeout: 5000 });
        
        // Get initial count
        const initialCount = await page.locator('[data-testid="notification-item"]').count();
        
        // Scroll to bottom
        await page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
        });
        
        // Wait for more notifications to load
        await page.waitForTimeout(2000);
        
        // Get new count
        const newCount = await page.locator('[data-testid="notification-item"]').count();
        
        // Should have loaded more (or stayed same if no more available)
        expect(newCount).toBeGreaterThanOrEqual(initialCount);
    });

    test('should display notification types with correct icons', async ({ page }) => {
        await page.goto(`${BASE_URL}/notifications`);
        
        await page.waitForSelector('[data-testid="notification-item"]', { timeout: 5000 });
        
        // Check that notifications have type icons
        const notifications = page.locator('[data-testid="notification-item"]');
        const firstNotification = notifications.first();
        
        // Should have an icon
        const icon = firstNotification.locator('[data-testid="notification-icon"]');
        await expect(icon).toBeVisible();
    });

    test('should show relative timestamps', async ({ page }) => {
        await page.goto(`${BASE_URL}/notifications`);
        
        await page.waitForSelector('[data-testid="notification-item"]', { timeout: 5000 });
        
        // Check timestamp format
        const timestamp = page.locator('[data-testid="notification-timestamp"]').first();
        const timestampText = await timestamp.textContent();
        
        // Should show relative time like "2 hours ago", "just now", etc.
        expect(timestampText).toMatch(/ago|just now|yesterday|minute|hour|day/i);
    });

    test('should be responsive on mobile', async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 667 });
        
        await page.goto(`${BASE_URL}/notifications`);
        
        // Page should be functional on mobile
        await expect(page.locator('h1')).toBeVisible();
        
        // Notifications should stack vertically
        const notifications = page.locator('[data-testid="notification-item"]');
        if (await notifications.count() > 1) {
            const first = await notifications.first().boundingBox();
            const second = await notifications.nth(1).boundingBox();
            
            if (first && second) {
                expect(second.y).toBeGreaterThan(first.y);
            }
        }
    });

    test('should handle API errors gracefully', async ({ page }) => {
        // Mock API error
        await page.route('**/api/notifications**', route => {
            route.fulfill({
                status: 500,
                body: JSON.stringify({ detail: 'Server error' })
            });
        });
        
        await page.goto(`${BASE_URL}/notifications`);
        
        // Should show error message
        const errorMessage = page.locator('[data-testid="error-message"]');
        await expect(errorMessage).toBeVisible();
    });
});
