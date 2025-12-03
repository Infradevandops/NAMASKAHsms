/**
 * Authentication State Check
 * Runs on every page load to verify user is authenticated
 */

(function() {
    'use strict';

    // Check authentication on page load
    async function checkAuthentication() {
        const token = localStorage.getItem('access_token');
        const expiresAt = localStorage.getItem('token_expires_at');
        const now = Date.now();

        // No token - redirect to login
        if (!token) {
            // Only redirect if not already on auth pages
            const currentPath = window.location.pathname;
            if (!currentPath.includes('/auth/') && 
                !currentPath.includes('/login') && 
                !currentPath.includes('/register') &&
                currentPath !== '/' &&
                !currentPath.includes('/landing')) {
                console.log('No token found, redirecting to login');
                window.location.href = '/auth/login';
            }
            return false;
        }

        // Token expired - try to refresh
        if (expiresAt && now > expiresAt) {
            console.log('Token expired, attempting refresh...');
            const refreshed = await refreshToken();
            if (!refreshed) {
                window.location.href = '/auth/login';
            }
            return refreshed;
        }

        // Token valid - verify with server
        try {
            const response = await fetch('/api/user/balance', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Cache-Control': 'no-cache'
                }
            });

            if (response.status === 401) {
                // Token invalid - try refresh
                const refreshed = await refreshToken();
                if (!refreshed) {
                    localStorage.clear();
                    window.location.href = '/auth/login';
                }
                return refreshed;
            }

            if (response.ok) {
                return true;
            }
        } catch (error) {
            console.error('Auth check error:', error);
        }

        return false;
    }

    // Refresh token
    async function refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (!refreshToken) {
            return false;
        }

        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${refreshToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                localStorage.setItem('token_expires_at', Date.now() + (data.expires_in * 1000));
                return true;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
        }

        return false;
    }

    // Run check when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkAuthentication);
    } else {
        checkAuthentication();
    }

    // Export for use in other modules
    window.checkAuthentication = checkAuthentication;
    window.refreshToken = refreshToken;
})();
