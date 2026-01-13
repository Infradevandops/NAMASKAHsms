/**
 * Unified API Client
 * Single source of truth for all API calls with:
 * - Automatic auth headers
 * - Request timeouts
 * - Retry logic with exponential backoff
 * - Centralized error handling
 */

import { TIMEOUTS, HTTP_STATUS, STORAGE_KEYS } from './constants.js';
import { getAuthHeaders, hasAuthToken, clearAuth } from './auth-helpers.js';

/**
 * Custom API Error class
 */
export class ApiError extends Error {
    constructor(message, status, data = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }

    isUnauthorized() {
        return this.status === HTTP_STATUS.UNAUTHORIZED;
    }

    isTimeout() {
        return this.status === HTTP_STATUS.TIMEOUT;
    }

    isServerError() {
        return this.status >= 500;
    }
}

/**
 * API Client class
 */
class ApiClient {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || '';
        this.defaultTimeout = options.timeout || TIMEOUTS.API_REQUEST;
        this.maxRetries = options.maxRetries || 3;
        this.retryDelay = options.retryDelay || 1000;
        this.onUnauthorized = options.onUnauthorized || this._defaultUnauthorizedHandler;
    }

    /**
     * Default handler for 401 responses
     */
    _defaultUnauthorizedHandler() {
        clearAuth();
        window.location.href = '/auth/login';
    }

    /**
     * Calculate retry delay with exponential backoff
     */
    _getRetryDelay(attempt) {
        return Math.min(this.retryDelay * Math.pow(2, attempt), 10000);
    }

    /**
     * Sleep for specified milliseconds
     */
    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Make an API request
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Request options
     * @returns {Promise<any>}
     */
    async request(endpoint, options = {}) {
        const {
            method = 'GET',
            body,
            headers = {},
            timeout = this.defaultTimeout,
            retry = true,
            maxRetries = this.maxRetries,
            requiresAuth = true
        } = options;

        // Check auth if required
        if (requiresAuth && !hasAuthToken()) {
            throw new ApiError('No authentication token', HTTP_STATUS.UNAUTHORIZED);
        }

        const url = `${this.baseUrl}${endpoint}`;
        let lastError;

        for (let attempt = 0; attempt <= (retry ? maxRetries : 0); attempt++) {
            // Wait before retry (skip first attempt)
            if (attempt > 0) {
                const delay = this._getRetryDelay(attempt - 1);
                if (window.FrontendLogger) {
                    window.FrontendLogger.info(`API retry ${attempt}/${maxRetries} for ${url}, waiting ${delay}ms`);
                }
                await this._sleep(delay);
            }

            // Create abort controller for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);

            try {
                const requestHeaders = {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders(),
                    ...headers
                };

                const requestOptions = {
                    method,
                    headers: requestHeaders,
                    credentials: 'include',
                    signal: controller.signal
                };

                if (body && method !== 'GET') {
                    requestOptions.body = typeof body === 'string' ? body : JSON.stringify(body);
                }

                if (window.FrontendLogger) {
                    window.FrontendLogger.logApiCall(method, url);
                }

                const response = await fetch(url, requestOptions);
                clearTimeout(timeoutId);

                if (window.FrontendLogger) {
                    window.FrontendLogger.logApiResponse(method, url, response.status);
                }

                // Handle 401 Unauthorized
                if (response.status === HTTP_STATUS.UNAUTHORIZED) {
                    this.onUnauthorized();
                    throw new ApiError('Unauthorized', HTTP_STATUS.UNAUTHORIZED);
                }

                // Don't retry client errors (except 408, 429)
                if (response.status >= 400 && response.status < 500 && 
                    response.status !== HTTP_STATUS.TIMEOUT && 
                    response.status !== HTTP_STATUS.TOO_MANY_REQUESTS) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new ApiError(
                        errorData.detail || `HTTP ${response.status}`,
                        response.status,
                        errorData
                    );
                }

                // Retry on server errors
                if (response.status >= 500 || 
                    response.status === HTTP_STATUS.TIMEOUT || 
                    response.status === HTTP_STATUS.TOO_MANY_REQUESTS) {
                    lastError = new ApiError(`HTTP ${response.status}`, response.status);
                    if (attempt < maxRetries) continue;
                    throw lastError;
                }

                // Success - parse response
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                }
                return await response.text();

            } catch (error) {
                clearTimeout(timeoutId);

                // Handle abort (timeout)
                if (error.name === 'AbortError') {
                    lastError = new ApiError('Request timeout', HTTP_STATUS.TIMEOUT);
                    if (attempt < maxRetries) continue;
                    throw lastError;
                }

                // Re-throw ApiErrors
                if (error instanceof ApiError) {
                    throw error;
                }

                // Network errors - retry
                lastError = new ApiError(error.message || 'Network error', 0);
                if (attempt < maxRetries) continue;
                throw lastError;
            }
        }

        throw lastError;
    }

    /**
     * GET request
     */
    get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    }

    /**
     * POST request
     */
    post(endpoint, body, options = {}) {
        return this.request(endpoint, { ...options, method: 'POST', body });
    }

    /**
     * PUT request
     */
    put(endpoint, body, options = {}) {
        return this.request(endpoint, { ...options, method: 'PUT', body });
    }

    /**
     * PATCH request
     */
    patch(endpoint, body, options = {}) {
        return this.request(endpoint, { ...options, method: 'PATCH', body });
    }

    /**
     * DELETE request
     */
    delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    }
}

// Create default instance
export const api = new ApiClient();

// Export class for custom instances
export { ApiClient };

// For non-module scripts (IIFE compatibility)
if (typeof window !== 'undefined') {
    window.ApiClient = ApiClient;
    window.ApiError = ApiError;
    window.api = api;
}
