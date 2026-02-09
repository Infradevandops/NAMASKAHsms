/**
 * Global Error Handler & Network Manager
 * Handles errors, offline detection, and retry logic across all dashboard pages
 */

class ErrorHandler {
    constructor() {
        this.isOnline = navigator.onLine;
        this.retryQueue = [];
        this.errorLog = [];
        this.maxErrorLog = 50;
        this.setupListeners();
        this.showConnectionStatus();
    }

    setupListeners() {
        // Online/Offline detection
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());

        // Global error handler
        window.addEventListener('error', (e) => this.handleGlobalError(e));
        window.addEventListener('unhandledrejection', (e) => this.handleUnhandledRejection(e));
    }

    handleOnline() {
        this.isOnline = true;
        this.showToast('Connection restored', 'success');
        this.hideOfflineBanner();
        this.processRetryQueue();
    }

    handleOffline() {
        this.isOnline = false;
        this.showToast('No internet connection', 'error');
        this.showOfflineBanner();
    }

    showOfflineBanner() {
        const existing = document.getElementById('offline-banner');
        if (existing) return;

        const banner = document.createElement('div');
        banner.id = 'offline-banner';
        banner.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            padding: 12px 20px;
            text-align: center;
            z-index: 10001;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            animation: slideDown 0.3s ease;
        `;
        banner.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
                <span>⚠️</span>
                <span>You're offline. Some features may not work.</span>
                <button onclick="window.errorHandler.checkConnection()" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                    Retry
                </button>
            </div>
        `;
        document.body.prepend(banner);
    }

    hideOfflineBanner() {
        const banner = document.getElementById('offline-banner');
        if (banner) {
            banner.style.animation = 'slideUp 0.3s ease';
            setTimeout(() => banner.remove(), 300);
        }
    }

    async checkConnection() {
        try {
            const response = await fetch('/api/health', { method: 'HEAD', cache: 'no-cache' });
            if (response.ok) {
                this.handleOnline();
            }
        } catch (e) {
            this.showToast('Still offline', 'warning');
        }
    }

    showConnectionStatus() {
        if (!this.isOnline) {
            this.showOfflineBanner();
        }
    }

    handleGlobalError(event) {
        console.error('Global error:', event.error);
        this.logError({
            type: 'error',
            message: event.error?.message || 'Unknown error',
            stack: event.error?.stack,
            timestamp: new Date().toISOString()
        });
    }

    handleUnhandledRejection(event) {
        console.error('Unhandled rejection:', event.reason);
        this.logError({
            type: 'rejection',
            message: event.reason?.message || 'Promise rejection',
            timestamp: new Date().toISOString()
        });
    }

    logError(error) {
        this.errorLog.push(error);
        if (this.errorLog.length > this.maxErrorLog) {
            this.errorLog.shift();
        }
    }

    // API Error Handler
    async handleAPIError(error, options = {}) {
        const { showToast = true, allowRetry = true, context = '' } = options;

        // Network error
        if (!this.isOnline || error.message?.includes('fetch')) {
            if (showToast) {
                this.showToast('No internet connection. Please check your network.', 'error');
            }
            if (allowRetry) {
                return this.showRetryDialog(error, context);
            }
            return null;
        }

        // HTTP errors
        if (error.response) {
            const status = error.response.status;
            const data = error.response.data;

            // Authentication errors
            if (status === 401) {
                this.showToast('Session expired. Please login again.', 'warning');
                setTimeout(() => window.location.href = '/auth/login', 2000);
                return null;
            }

            // Permission errors
            if (status === 403) {
                this.showToast('You don\'t have permission for this action.', 'error');
                return null;
            }

            // Not found
            if (status === 404) {
                this.showToast('Resource not found.', 'error');
                return null;
            }

            // Rate limiting
            if (status === 429) {
                const retryAfter = error.response.headers?.['retry-after'] || 60;
                this.showToast(`Too many requests. Please wait ${retryAfter} seconds.`, 'warning');
                return null;
            }

            // Server errors
            if (status >= 500) {
                const message = this.getUserFriendlyError(data?.detail || 'Server error');
                if (showToast) {
                    this.showToast(message, 'error');
                }
                if (allowRetry) {
                    return this.showRetryDialog(error, context);
                }
                return null;
            }

            // Client errors
            if (status >= 400) {
                const message = this.getUserFriendlyError(data?.detail || 'Request failed');
                if (showToast) {
                    this.showToast(message, 'error');
                }
                return null;
            }
        }

        // Unknown error
        if (showToast) {
            this.showToast('An unexpected error occurred. Please try again.', 'error');
        }
        return null;
    }

    getUserFriendlyError(errorDetail) {
        const errorMap = {
            'User not found': 'Your session has expired. Please login again.',
            'Invalid token': 'Your session has expired. Please login again.',
            'Insufficient balance': 'You don\'t have enough credits. Please add credits to continue.',
            'Service unavailable': 'This service is temporarily unavailable. Please try another service.',
            'Payment initialization failed': 'Unable to connect to payment provider. Please try again.',
            'Verification failed': 'SMS verification failed. You have been refunded.',
            'Rate limit exceeded': 'You\'re making too many requests. Please slow down.',
            'Invalid request': 'Invalid request. Please check your input and try again.',
            'Database error': 'A temporary error occurred. Please try again.',
            'Network error': 'Network error. Please check your connection.'
        };

        // Check for partial matches
        for (const [key, value] of Object.entries(errorMap)) {
            if (errorDetail?.includes(key)) {
                return value;
            }
        }

        return errorDetail || 'An error occurred. Please try again.';
    }

    showRetryDialog(error, context) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10002;
                animation: fadeIn 0.2s ease;
            `;

            modal.innerHTML = `
                <div style="background: white; border-radius: 12px; padding: 24px; max-width: 400px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 48px; margin-bottom: 12px;">⚠️</div>
                        <h3 style="margin: 0 0 8px 0; font-size: 18px; color: #1f2937;">Something went wrong</h3>
                        <p style="margin: 0; font-size: 14px; color: #6b7280;">
                            ${context ? `Failed to ${context}. ` : ''}Would you like to try again?
                        </p>
                    </div>
                    <div style="display: flex; gap: 12px;">
                        <button id="retry-cancel" style="flex: 1; padding: 12px; border: 1px solid #d1d5db; background: white; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; color: #6b7280;">
                            Cancel
                        </button>
                        <button id="retry-confirm" style="flex: 1; padding: 12px; border: none; background: #3b82f6; color: white; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500;">
                            Retry
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            document.getElementById('retry-cancel').onclick = () => {
                modal.remove();
                resolve(false);
            };

            document.getElementById('retry-confirm').onclick = () => {
                modal.remove();
                resolve(true);
            };
        });
    }

    showToast(message, type = 'info', duration = 5000) {
        // Remove existing toasts
        document.querySelectorAll('.error-toast').forEach(t => t.remove());

        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease;
            max-width: 400px;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 12px;
        `;
        toast.innerHTML = `
            <span style="font-size: 18px;">${icons[type]}</span>
            <span style="flex: 1;">${message}</span>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    addToRetryQueue(fn, context) {
        this.retryQueue.push({ fn, context });
    }

    async processRetryQueue() {
        if (this.retryQueue.length === 0) return;

        this.showToast(`Retrying ${this.retryQueue.length} failed action(s)...`, 'info');

        const queue = [...this.retryQueue];
        this.retryQueue = [];

        for (const item of queue) {
            try {
                await item.fn();
            } catch (e) {
                console.error('Retry failed:', e);
            }
        }
    }

    getErrorLog() {
        return this.errorLog;
    }

    clearErrorLog() {
        this.errorLog = [];
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
    @keyframes slideDown {
        from { transform: translateY(-100%); }
        to { transform: translateY(0); }
    }
    @keyframes slideUp {
        from { transform: translateY(0); }
        to { transform: translateY(-100%); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
`;
document.head.appendChild(style);

// Initialize global error handler
window.errorHandler = new ErrorHandler();

// Export for use in other scripts
window.ErrorHandler = ErrorHandler;

console.log('✅ Global error handler initialized');
