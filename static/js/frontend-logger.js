/**
 * Frontend Logging Utility
 * 
 * Provides structured logging for frontend operations including:
 * - API calls and responses
 * - Errors with stack traces
 * - Tier loading success/failure
 * - User interactions
 */

(function(window) {
    'use strict';

    // Log levels
    const LogLevel = {
        DEBUG: 'DEBUG',
        INFO: 'INFO',
        WARN: 'WARN',
        ERROR: 'ERROR'
    };

    // Configuration
    const config = {
        enabled: true,
        minLevel: LogLevel.DEBUG,
        includeTimestamp: true,
        includeStackTrace: true,
        maxLogSize: 1000 // Maximum number of logs to keep in memory
    };

    // In-memory log storage
    const logs = [];

    /**
     * Format timestamp
     */
    function getTimestamp() {
        return new Date().toISOString();
    }

    /**
     * Get stack trace
     */
    function getStackTrace() {
        try {
            throw new Error();
        } catch (e) {
            // Remove first 3 lines (Error, getStackTrace, log function)
            const stack = e.stack.split('\n').slice(3).join('\n');
            return stack;
        }
    }

    /**
     * Core logging function
     */
    function log(level, message, data) {
        if (!config.enabled) return;

        const logEntry = {
            level: level,
            message: message,
            timestamp: config.includeTimestamp ? getTimestamp() : null,
            data: data || null
        };

        // Add stack trace for errors
        if (level === LogLevel.ERROR && config.includeStackTrace) {
            logEntry.stack = getStackTrace();
        }

        // Store in memory
        logs.push(logEntry);
        if (logs.length > config.maxLogSize) {
            logs.shift(); // Remove oldest log
        }

        // Console output with appropriate method
        const consoleMethod = level === LogLevel.ERROR ? 'error' :
                            level === LogLevel.WARN ? 'warn' :
                            level === LogLevel.INFO ? 'info' : 'log';

        const prefix = `[${level}] ${logEntry.timestamp || ''} ${message}`;
        if (data) {
            console[consoleMethod](prefix, data);
        } else {
            console[consoleMethod](prefix);
        }
    }

    /**
     * Public API
     */
    const FrontendLogger = {
        // Log levels
        debug: function(message, data) {
            log(LogLevel.DEBUG, message, data);
        },

        info: function(message, data) {
            log(LogLevel.INFO, message, data);
        },

        warn: function(message, data) {
            log(LogLevel.WARN, message, data);
        },

        error: function(message, data) {
            log(LogLevel.ERROR, message, data);
        },

        // Specialized logging methods
        logApiCall: function(method, url, options) {
            this.info(`API Call: ${method} ${url}`, {
                method: method,
                url: url,
                options: options
            });
        },

        logApiResponse: function(method, url, status, data) {
            const level = status >= 400 ? LogLevel.ERROR : LogLevel.INFO;
            log(level, `API Response: ${method} ${url} - ${status}`, {
                method: method,
                url: url,
                status: status,
                data: data
            });
        },

        logApiError: function(method, url, error) {
            this.error(`API Error: ${method} ${url}`, {
                method: method,
                url: url,
                error: error.message || error,
                stack: error.stack
            });
        },

        logTierLoad: function(success, tierData, error) {
            if (success) {
                this.info('Tier info loaded successfully', {
                    tier: tierData.current_tier,
                    tier_name: tierData.tier_name,
                    quota_used: tierData.quota_used_usd,
                    quota_limit: tierData.quota_usd
                });
            } else {
                this.error('Tier info load failed', {
                    error: error.message || error,
                    stack: error.stack
                });
            }
        },

        logAnalyticsLoad: function(success, data, error) {
            if (success) {
                this.info('Analytics loaded successfully', {
                    total_verifications: data.total_verifications,
                    success_rate: data.success_rate
                });
            } else {
                this.error('Analytics load failed', {
                    error: error.message || error,
                    stack: error.stack
                });
            }
        },

        logActivityLoad: function(success, count, error) {
            if (success) {
                this.info(`Activity loaded successfully: ${count} items`);
            } else {
                this.error('Activity load failed', {
                    error: error.message || error,
                    stack: error.stack
                });
            }
        },

        logUserAction: function(action, details) {
            this.info(`User action: ${action}`, details);
        },

        // Get all logs
        getLogs: function() {
            return logs.slice(); // Return copy
        },

        // Clear logs
        clearLogs: function() {
            logs.length = 0;
            this.info('Logs cleared');
        },

        // Export logs as JSON
        exportLogs: function() {
            return JSON.stringify(logs, null, 2);
        },

        // Configure logger
        configure: function(options) {
            Object.assign(config, options);
        }
    };

    // Expose to window
    window.FrontendLogger = FrontendLogger;

    // Log initialization
    FrontendLogger.info('Frontend logger initialized');

})(window);
