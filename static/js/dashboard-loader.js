/**
 * Dashboard Loader Utility
 * 
 * Provides consistent loading, error handling, and timeout behavior
 * for all dashboard widgets. Prevents infinite spinners.
 * 
 * Usage:
 *   const loader = new DashboardLoader({
 *       containerId: 'my-widget',
 *       loadingText: 'Loading data...',
 *       timeout: 10000,
 *       onLoad: async () => { return await fetchData(); },
 *       onSuccess: (data) => { renderWidget(data); },
 *       onError: (error) => { showError(error); }
 *   });
 *   loader.load();
 */

(function(window) {
    'use strict';

    // Default configuration
    const DEFAULTS = {
        timeout: 10000,           // 10 seconds
        failsafeTimeout: 15000,   // 15 seconds
        retryAttempts: 3,
        retryDelay: 1000,
        loadingText: 'Loading...',
        errorText: 'Unable to load',
        timeoutText: 'Request timed out',
        unauthText: 'Not logged in',
        sessionExpiredText: 'Session expired'
    };

    // States
    const STATES = {
        INITIAL: 'initial',
        LOADING: 'loading',
        LOADED: 'loaded',
        ERROR: 'error',
        TIMEOUT: 'timeout',
        UNAUTHENTICATED: 'unauthenticated',
        SESSION_EXPIRED: 'session-expired'
    };

    /**
     * Check if user has valid auth token
     */
    function hasAuthToken() {
        const token = localStorage.getItem('access_token');
        return token && token.length > 0;
    }

    /**
     * Get auth headers for API calls
     */
    function getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return token ? { 'Authorization': 'Bearer ' + token } : {};
    }

    /**
     * DashboardLoader class
     */
    class DashboardLoader {
        constructor(options) {
            this.options = { ...DEFAULTS, ...options };
            this.state = STATES.INITIAL;
            this.abortController = null;
            this.timeoutId = null;
            this.failsafeId = null;
            this.retryCount = 0;
            
            // Validate required options
            if (!this.options.containerId) {
                throw new Error('DashboardLoader: containerId is required');
            }
            if (!this.options.onLoad) {
                throw new Error('DashboardLoader: onLoad function is required');
            }
        }

        /**
         * Get the container element
         */
        getContainer() {
            return document.getElementById(this.options.containerId);
        }

        /**
         * Set the current state
         */
        setState(state, data = null) {
            this.state = state;
            
            const container = this.getContainer();
            if (!container) return;

            // Remove all state classes
            Object.values(STATES).forEach(s => {
                container.classList.remove(`loader-state-${s}`);
            });
            
            // Add current state class
            container.classList.add(`loader-state-${state}`);

            // Call state-specific handler if provided
            const handler = this.options[`on${state.charAt(0).toUpperCase() + state.slice(1)}`];
            if (typeof handler === 'function') {
                handler(data);
            }

            // Log state change
            if (window.FrontendLogger) {
                FrontendLogger.info(`[${this.options.containerId}] State: ${state}`, data);
            }
        }

        /**
         * Show loading state
         */
        showLoading() {
            this.setState(STATES.LOADING);
            
            if (this.options.renderLoading) {
                this.options.renderLoading();
            }
        }

        /**
         * Show error state with retry button
         */
        showError(error) {
            this.setState(STATES.ERROR, { error });
            
            if (this.options.renderError) {
                this.options.renderError(error, () => this.load());
            }
        }

        /**
         * Show timeout state
         */
        showTimeout() {
            this.setState(STATES.TIMEOUT);
            
            if (this.options.renderTimeout) {
                this.options.renderTimeout(() => this.load());
            }
        }

        /**
         * Show unauthenticated state
         */
        showUnauthenticated() {
            this.setState(STATES.UNAUTHENTICATED);
            
            if (this.options.renderUnauthenticated) {
                this.options.renderUnauthenticated();
            }
        }

        /**
         * Show session expired state
         */
        showSessionExpired() {
            this.setState(STATES.SESSION_EXPIRED);
            
            if (this.options.renderSessionExpired) {
                this.options.renderSessionExpired();
            }
        }

        /**
         * Clear all timers
         */
        clearTimers() {
            if (this.timeoutId) {
                clearTimeout(this.timeoutId);
                this.timeoutId = null;
            }
            if (this.failsafeId) {
                clearTimeout(this.failsafeId);
                this.failsafeId = null;
            }
        }

        /**
         * Abort current request
         */
        abort() {
            if (this.abortController) {
                this.abortController.abort();
                this.abortController = null;
            }
            this.clearTimers();
        }

        /**
         * Main load function
         */
        async load() {
            // Abort any previous request
            this.abort();

            // Check authentication first
            if (this.options.requiresAuth !== false && !hasAuthToken()) {
                this.showUnauthenticated();
                return;
            }

            // Show loading state
            this.showLoading();

            // Create abort controller
            this.abortController = new AbortController();

            // Set timeout
            this.timeoutId = setTimeout(() => {
                if (window.FrontendLogger) {
                    FrontendLogger.warn(`[${this.options.containerId}] Timeout after ${this.options.timeout}ms`);
                }
                this.abort();
                this.showTimeout();
            }, this.options.timeout);

            // Set failsafe
            this.failsafeId = setTimeout(() => {
                if (this.state === STATES.LOADING) {
                    if (window.FrontendLogger) {
                        FrontendLogger.error(`[${this.options.containerId}] Failsafe triggered after ${this.options.failsafeTimeout}ms`);
                    }
                    this.abort();
                    this.showTimeout();
                }
            }, this.options.failsafeTimeout);

            try {
                // Execute the load function
                const result = await this.options.onLoad({
                    signal: this.abortController.signal,
                    headers: getAuthHeaders()
                });

                // Clear timers on success
                this.clearTimers();

                // Handle 401 specifically
                if (result && result.status === 401) {
                    this.showSessionExpired();
                    return;
                }

                // Call success handler
                this.setState(STATES.LOADED, result);
                
                if (this.options.onSuccess) {
                    this.options.onSuccess(result);
                }

                // Reset retry count on success
                this.retryCount = 0;

            } catch (error) {
                this.clearTimers();

                // Ignore abort errors (handled by timeout)
                if (error.name === 'AbortError') {
                    return;
                }

                if (window.FrontendLogger) {
                    FrontendLogger.error(`[${this.options.containerId}] Load failed`, { error: error.message });
                }

                // Try cached data if available
                if (this.options.getCachedData) {
                    const cached = this.options.getCachedData();
                    if (cached) {
                        this.setState(STATES.LOADED, cached);
                        if (this.options.onSuccess) {
                            this.options.onSuccess(cached, { fromCache: true });
                        }
                        return;
                    }
                }

                // Show error
                this.showError(error);

                // Call error handler
                if (this.options.onError) {
                    this.options.onError(error);
                }
            }
        }

        /**
         * Retry loading
         */
        retry() {
            this.retryCount++;
            
            if (this.retryCount <= this.options.retryAttempts) {
                setTimeout(() => this.load(), this.options.retryDelay);
            } else {
                this.showError(new Error('Max retry attempts reached'));
            }
        }

        /**
         * Destroy the loader
         */
        destroy() {
            this.abort();
            this.state = STATES.INITIAL;
        }
    }

    // Export
    window.DashboardLoader = DashboardLoader;
    window.DashboardLoaderStates = STATES;
    window.hasAuthToken = hasAuthToken;
    window.getAuthHeaders = getAuthHeaders;

})(window);
