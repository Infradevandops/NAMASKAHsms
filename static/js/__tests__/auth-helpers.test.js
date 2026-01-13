/**
 * Unit Tests for auth-helpers.js
 */

import {
    getAuthToken,
    hasAuthToken,
    getAuthHeaders,
    setAuthTokens,
    clearAuth,
    isTokenExpired,
    shouldRefreshToken,
    getRefreshToken,
    isProtectedPage
} from '../auth-helpers.js';
import { STORAGE_KEYS } from '../constants.js';

describe('auth-helpers.js', () => {
    
    beforeEach(() => {
        // Clear localStorage before each test
        localStorage.clear();
    });

    describe('getAuthToken', () => {
        it('should return null when no token exists', () => {
            expect(getAuthToken()).toBeNull();
        });

        it('should return token when it exists', () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'test-token-123');
            expect(getAuthToken()).toBe('test-token-123');
        });
    });

    describe('hasAuthToken', () => {
        it('should return false when no token exists', () => {
            expect(hasAuthToken()).toBe(false);
        });

        it('should return false for empty token', () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, '');
            expect(hasAuthToken()).toBe(false);
        });

        it('should return true when valid token exists', () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'valid-token');
            expect(hasAuthToken()).toBe(true);
        });
    });

    describe('getAuthHeaders', () => {
        it('should return empty object when no token', () => {
            expect(getAuthHeaders()).toEqual({});
        });

        it('should return Authorization header when token exists', () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'my-token');
            expect(getAuthHeaders()).toEqual({
                'Authorization': 'Bearer my-token'
            });
        });
    });

    describe('setAuthTokens', () => {
        it('should set access token', () => {
            setAuthTokens('access-123');
            expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBe('access-123');
        });

        it('should set refresh token when provided', () => {
            setAuthTokens('access-123', 'refresh-456');
            expect(localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)).toBe('refresh-456');
        });

        it('should set expiry when provided', () => {
            const now = Date.now();
            setAuthTokens('access-123', null, 3600); // 1 hour
            
            const expiresAt = parseInt(localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRES), 10);
            expect(expiresAt).toBeGreaterThan(now);
            expect(expiresAt).toBeLessThanOrEqual(now + 3600 * 1000 + 100); // Allow 100ms tolerance
        });
    });

    describe('clearAuth', () => {
        it('should remove all auth data', () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'token');
            localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, 'refresh');
            localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES, '12345');

            clearAuth();

            expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBeNull();
            expect(localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)).toBeNull();
            expect(localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRES)).toBeNull();
        });
    });

    describe('isTokenExpired', () => {
        it('should return false when no expiry is set', () => {
            expect(isTokenExpired()).toBe(false);
        });

        it('should return true when token is expired', () => {
            const pastTime = Date.now() - 10000; // 10 seconds ago
            localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES, pastTime.toString());
            expect(isTokenExpired()).toBe(true);
        });

        it('should return false when token is not expired', () => {
            const futureTime = Date.now() + 3600000; // 1 hour from now
            localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES, futureTime.toString());
            expect(isTokenExpired()).toBe(false);
        });
    });

    describe('getRefreshToken', () => {
        it('should return null when no refresh token', () => {
            expect(getRefreshToken()).toBeNull();
        });

        it('should return refresh token when it exists', () => {
            localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, 'refresh-token-xyz');
            expect(getRefreshToken()).toBe('refresh-token-xyz');
        });
    });

    describe('isProtectedPage', () => {
        const originalLocation = window.location;

        beforeEach(() => {
            delete window.location;
        });

        afterEach(() => {
            window.location = originalLocation;
        });

        it('should return false for public pages', () => {
            window.location = { pathname: '/' };
            expect(isProtectedPage()).toBe(false);

            window.location = { pathname: '/landing' };
            expect(isProtectedPage()).toBe(false);

            window.location = { pathname: '/auth/login' };
            expect(isProtectedPage()).toBe(false);

            window.location = { pathname: '/pricing' };
            expect(isProtectedPage()).toBe(false);
        });

        it('should return true for protected pages', () => {
            window.location = { pathname: '/dashboard' };
            expect(isProtectedPage()).toBe(true);

            window.location = { pathname: '/settings' };
            expect(isProtectedPage()).toBe(true);

            window.location = { pathname: '/wallet' };
            expect(isProtectedPage()).toBe(true);
        });
    });
});
