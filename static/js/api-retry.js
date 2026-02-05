/**
 * API Retry Utility
 * 
 * Provides retry logic with exponential backoff for failed API calls.
 * Features:
 * - Configurable retry count (default: 3)
 * - Exponential backoff between retries
 * - Retry button UI component
 * - Integration with FrontendLogger
 * 
 * Converted to ES6 module - maintains backward compatibility via window attachment
 */

import { TIMEOUTS, HTTP_STATUS } from './constants.js';

// Default configuration
export const DEFAULT_RETRY_CONFIG = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: TIMEOUTS.API_REQUEST,
    backoffMultiplier: 2
};

/**
 * Calculate delay with exponential backoff
 */
export function calculateDelay(attempt, config = DEFAULT_RETRY_CONFIG) {
    const delay = config.baseDelay * Math.pow(config.backoffMultiplier, attempt);
    return Math.min(delay, config.maxDelay);
}

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Fetch with retry logic
 * @param {string} url - The URL to fetch
 * @param {object} options - Fetch options
 * @param {object} retryConfig - Retry configuration
 * @returns {Promise<Response>} - The fetch response
 */
export async function fetchWithRetry(url, options = {}, retryConfig = {}) {
    const config = { ...DEFAULT_RETRY_CONFIG, ...retryConfig };
    let lastError;

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
        try {
            if (attempt > 0) {
                const delay = calculateDelay(attempt - 1, config);
                _log('info', `Retry attempt ${attempt}/${config.maxRetries} for ${url}, waiting ${delay}ms`);
                await sleep(delay);
            }

            const response = await fetch(url, options);

            // Don't retry on client errors (4xx) except for specific cases
            if (response.status >= 400 && response.status < 500 &&
                response.status !== HTTP_STATUS.TIMEOUT &&
                response.status !== HTTP_STATUS.TOO_MANY_REQUESTS) {
                return response;
            }

            // Retry on server errors (5xx) or timeout/rate limit
            if (response.status >= 500 ||
                response.status === HTTP_STATUS.TIMEOUT ||
                response.status === HTTP_STATUS.TOO_MANY_REQUESTS) {
                lastError = new Error(`HTTP ${response.status}`);
                if (attempt < config.maxRetries) {
                    _log('warn', `Request failed with ${response.status}, will retry`, { url, attempt });
                    continue;
                }
                throw lastError; // Final attempt failed
            }

            return response;
        } catch (error) {
            lastError = error;
            _log('warn', `Request failed: ${error.message}, attempt ${attempt + 1}/${config.maxRetries + 1}`, { url });

            if (attempt >= config.maxRetries) {
                throw error;
            }
        }
    }

    throw lastError;
}

/**
 * Create a retry button element
 * @param {function} retryCallback - Function to call when retry is clicked
 * @param {string} message - Error message to display
 * @returns {HTMLElement} - The retry button container
 */
export function createRetryButton(retryCallback, message = 'Failed to load data') {
    const container = document.createElement('div');
    container.className = 'retry-container';
    container.style.cssText = 'text-align: center; padding: 20px; color: var(--text-muted);';

    const errorIcon = document.createElement('div');
    errorIcon.innerHTML = '⚠️';
    errorIcon.style.cssText = 'font-size: 32px; margin-bottom: 12px;';
    errorIcon.setAttribute('aria-hidden', 'true');

    const errorMsg = document.createElement('div');
    errorMsg.textContent = message;
    errorMsg.style.cssText = 'margin-bottom: 16px; color: var(--text-secondary);';
    errorMsg.setAttribute('role', 'alert');

    const retryBtn = document.createElement('button');
    retryBtn.className = 'btn btn-secondary';
    retryBtn.innerHTML = '🔄 Retry';
    retryBtn.style.cssText = 'padding: 8px 16px; cursor: pointer;';
    retryBtn.setAttribute('aria-label', 'Retry loading data');
    retryBtn.onclick = function () {
        retryBtn.disabled = true;
        retryBtn.innerHTML = '<span class="loading-spinner"></span> Retrying...';
        retryBtn.setAttribute('aria-busy', 'true');

        Promise.resolve(retryCallback()).finally(() => {
            retryBtn.disabled = false;
            retryBtn.innerHTML = '🔄 Retry';
            retryBtn.setAttribute('aria-busy', 'false');
        });
    };

    container.appendChild(errorIcon);
    container.appendChild(errorMsg);
    container.appendChild(retryBtn);

    return container;
}

/**
 * Show retry UI in a container element
 * @param {HTMLElement|string} container - Container element or selector
 * @param {function} retryCallback - Function to call when retry is clicked
 * @param {string} message - Error message to display
 */
export function showRetryUI(container, retryCallback, message) {
    const el = typeof container === 'string' ? document.querySelector(container) : container;
    if (!el) return;

    el.innerHTML = '';
    el.appendChild(createRetryButton(retryCallback, message));
}

/**
 * Wrapper for API calls with automatic retry and error handling
 * @param {object} options - Configuration options
 */
export async function apiCall(options) {
    const {
        url,
        fetchOptions = { credentials: 'include' },
        container,
        onSuccess,
        onError,
        errorMessage = 'Failed to load data',
        retryConfig = {}
    } = options;

    const doFetch = async () => {
        try {
            const response = await fetchWithRetry(url, fetchOptions, retryConfig);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (onSuccess) {
                onSuccess(data, response);
            }

            return data;
        } catch (error) {
            _log('error', `API call failed after retries: ${url}`, { error: error.message });

            if (container) {
                showRetryUI(container, doFetch, errorMessage);
            }

            if (onError) {
                onError(error);
            }

            throw error;
        }
    };

    return doFetch();
}

/**
 * Internal logging helper
 */
function _log(level, message, data = null) {
    if (typeof window !== 'undefined' && window.FrontendLogger) {
        window.FrontendLogger[level](message, data);
    } else {
        const logFn = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
        logFn(`[ApiRetry] ${message}`, data || '');
    }
}

// Public API object for backward compatibility
export const ApiRetry = {
    fetchWithRetry,
    createRetryButton,
    showRetryUI,
    apiCall,
    config: DEFAULT_RETRY_CONFIG
};

// Attach to window for legacy scripts
if (typeof window !== 'undefined') {
    window.ApiRetry = ApiRetry;
}
