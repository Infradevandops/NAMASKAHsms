/**
 * Authentication Helpers
 * Centralized auth token management
 */

import { STORAGE_KEYS, TIMEOUTS } from './constants.js';

/**
 * Get the current access token
 * @returns {string|null}
 */
export function getAuthToken() {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

/**
 * Check if user has a valid auth token
 * @returns {boolean}
 */
export function hasAuthToken() {
    const token = getAuthToken();
    return token && token.length > 0;
}

/**
 * Get authorization headers for API requests
 * @returns {Object}
 */
export function getAuthHeaders() {
    const token = getAuthToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

/**
 * Set auth tokens in storage
 * @param {string} accessToken
 * @param {string} [refreshToken]
 * @param {number} [expiresIn] - Seconds until expiry
 */
export function setAuthTokens(accessToken, refreshToken, expiresIn) {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
    
    if (refreshToken) {
        localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
    }
    
    if (expiresIn) {
        const expiresAt = Date.now() + (expiresIn * 1000);
        localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES, expiresAt.toString());
    }
}

/**
 * Clear all auth data from storage
 */
export function clearAuth() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.TOKEN_EXPIRES);
}

/**
 * Check if the current token is expired
 * @returns {boolean}
 */
export function isTokenExpired() {
    const expiresAt = localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRES);
    if (!expiresAt) return false; // No expiry set, assume valid
    return Date.now() > parseInt(expiresAt, 10);
}

/**
 * Check if token needs refresh (within buffer period)
 * @returns {boolean}
 */
export function shouldRefreshToken() {
    const expiresAt = localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRES);
    if (!expiresAt) return false;
    
    const expiryTime = parseInt(expiresAt, 10);
    const bufferTime = Date.now() + TIMEOUTS.TOKEN_REFRESH_BUFFER;
    
    return bufferTime > expiryTime;
}

/**
 * Get refresh token
 * @returns {string|null}
 */
export function getRefreshToken() {
    return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
}

/**
 * Redirect to login page
 * @param {string} [returnUrl] - URL to return to after login
 */
export function redirectToLogin(returnUrl) {
    clearAuth();
    const loginUrl = returnUrl 
        ? `/auth/login?return=${encodeURIComponent(returnUrl)}`
        : '/auth/login';
    window.location.href = loginUrl;
}

/**
 * Check if current page requires authentication
 * @returns {boolean}
 */
export function isProtectedPage() {
    const publicPaths = ['/', '/landing', '/auth/', '/login', '/register', '/pricing', '/about', '/contact'];
    const currentPath = window.location.pathname;
    
    return !publicPaths.some(path => 
        currentPath === path || currentPath.startsWith(path)
    );
}

// For non-module scripts (IIFE compatibility)
if (typeof window !== 'undefined') {
    window.AuthHelpers = {
        getAuthToken,
        hasAuthToken,
        getAuthHeaders,
        setAuthTokens,
        clearAuth,
        isTokenExpired,
        shouldRefreshToken,
        getRefreshToken,
        redirectToLogin,
        isProtectedPage
    };
}
