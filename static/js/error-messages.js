/**
 * Error Messages Utility
 * 
 * Provides user-friendly error messages with actionable next steps
 */

// Error type mappings
export const ERROR_TYPES = {
    NETWORK: 'network',
    SERVER: 'server',
    AUTH: 'auth',
    VALIDATION: 'validation',
    NOT_FOUND: 'not_found',
    RATE_LIMIT: 'rate_limit',
    TIER_REQUIRED: 'tier_required',
    UNKNOWN: 'unknown'
};

// User-friendly error messages
export const ERROR_MESSAGES = {
    [ERROR_TYPES.NETWORK]: {
        title: 'Connection Problem',
        message: 'Unable to connect to the server. Please check your internet connection.',
        icon: '🌐',
        actions: [
            { text: 'Check your internet connection', type: 'info' },
            { text: 'Try refreshing the page', type: 'action', action: () => window.location.reload() }
        ]
    },
    [ERROR_TYPES.SERVER]: {
        title: 'Server Error',
        message: 'Something went wrong on our end. Our team has been notified.',
        icon: '⚠️',
        actions: [
            { text: 'Try again in a few minutes', type: 'info' },
            { text: 'Contact support if the problem persists', type: 'link', href: '/support' }
        ]
    },
    [ERROR_TYPES.AUTH]: {
        title: 'Authentication Required',
        message: 'Your session may have expired. Please log in again.',
        icon: '🔐',
        actions: [
            { text: 'Log in', type: 'action', action: () => window.location.href = '/login' }
        ]
    },
    [ERROR_TYPES.VALIDATION]: {
        title: 'Invalid Request',
        message: 'The request could not be processed. Please check your input.',
        icon: '📝',
        actions: [
            { text: 'Review your input and try again', type: 'info' }
        ]
    },
    [ERROR_TYPES.NOT_FOUND]: {
        title: 'Not Found',
        message: 'The requested resource could not be found.',
        icon: '🔍',
        actions: [
            { text: 'Go back', type: 'action', action: () => window.history.back() },
            { text: 'Go to dashboard', type: 'link', href: '/dashboard' }
        ]
    },
    [ERROR_TYPES.RATE_LIMIT]: {
        title: 'Too Many Requests',
        message: 'You\'ve made too many requests. Please wait a moment before trying again.',
        icon: '⏱️',
        actions: [
            { text: 'Wait 30 seconds and try again', type: 'info' }
        ]
    },
    [ERROR_TYPES.TIER_REQUIRED]: {
        title: 'Upgrade Required',
        message: 'This feature requires a higher subscription tier.',
        icon: '⭐',
        actions: [
            { text: 'View pricing', type: 'link', href: '/pricing' }
        ]
    },
    [ERROR_TYPES.UNKNOWN]: {
        title: 'Something Went Wrong',
        message: 'An unexpected error occurred. Please try again.',
        icon: '❓',
        actions: [
            { text: 'Refresh the page', type: 'action', action: () => window.location.reload() }
        ]
    }
};

/**
 * Determine error type from error object or HTTP status
 * @param {Error|number} error - Error object or HTTP status code
 * @returns {string} Error type
 */
export function getErrorType(error) {
    // Handle HTTP status codes
    if (typeof error === 'number') {
        if (error === 401 || error === 403) return ERROR_TYPES.AUTH;
        if (error === 402) return ERROR_TYPES.TIER_REQUIRED;
        if (error === 404) return ERROR_TYPES.NOT_FOUND;
        if (error === 422 || error === 400) return ERROR_TYPES.VALIDATION;
        if (error === 429) return ERROR_TYPES.RATE_LIMIT;
        if (error >= 500) return ERROR_TYPES.SERVER;
        return ERROR_TYPES.UNKNOWN;
    }

    // Handle Error objects
    if (error instanceof Error) {
        const message = error.message.toLowerCase();

        if (message.includes('network') || message.includes('fetch') || message.includes('failed to fetch')) {
            return ERROR_TYPES.NETWORK;
        }
        if (message.includes('401') || message.includes('403') || message.includes('unauthorized')) {
            return ERROR_TYPES.AUTH;
        }
        if (message.includes('402')) {
            return ERROR_TYPES.TIER_REQUIRED;
        }
        if (message.includes('404') || message.includes('not found')) {
            return ERROR_TYPES.NOT_FOUND;
        }
        if (message.includes('429') || message.includes('rate limit')) {
            return ERROR_TYPES.RATE_LIMIT;
        }
        if (message.includes('500') || message.includes('server')) {
            return ERROR_TYPES.SERVER;
        }
    }

    return ERROR_TYPES.UNKNOWN;
}

/**
 * Get user-friendly error info
 * @param {Error|number} error - Error object or HTTP status code
 * @param {string} customMessage - Optional custom message
 * @returns {object} Error info with title, message, icon, and actions
 */
export function getErrorInfo(error, customMessage = null) {
    const errorType = getErrorType(error);
    const errorInfo = { ...ERROR_MESSAGES[errorType] };

    if (customMessage) {
        errorInfo.message = customMessage;
    }

    return errorInfo;
}

/**
 * Create an error display element
 * @param {Error|number} error - Error object or HTTP status code
 * @param {object} options - Display options
 * @returns {HTMLElement}
 */
export function createErrorDisplay(error, options = {}) {
    const {
        customMessage = null,
        showActions = true,
        retryCallback = null,
        compact = false
    } = options;

    const errorInfo = getErrorInfo(error, customMessage);
    const container = document.createElement('div');
    container.className = 'error-display' + (compact ? ' compact' : '');
    container.style.cssText = `
        text-align: center;
        padding: ${compact ? '16px' : '32px'};
        color: var(--text-secondary);
    `;

    // Icon
    const icon = document.createElement('div');
    icon.textContent = errorInfo.icon;
    icon.style.cssText = `font-size: ${compact ? '24px' : '40px'}; margin-bottom: 12px;`;
    container.appendChild(icon);

    // Title
    const title = document.createElement('div');
    title.textContent = errorInfo.title;
    title.style.cssText = `
        font-size: ${compact ? '16px' : '18px'};
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
    `;
    container.appendChild(title);

    // Message
    const message = document.createElement('div');
    message.textContent = errorInfo.message;
    message.style.cssText = `
        font-size: 14px;
        color: var(--text-muted);
        margin-bottom: 16px;
        max-width: 400px;
        margin-left: auto;
        margin-right: auto;
    `;
    container.appendChild(message);

    // Actions
    if (showActions) {
        const actionsContainer = document.createElement('div');
        actionsContainer.style.cssText = 'display: flex; flex-direction: column; gap: 8px; align-items: center;';

        // Add retry button if callback provided
        if (retryCallback) {
            const retryBtn = document.createElement('button');
            retryBtn.className = 'btn btn-primary';
            retryBtn.innerHTML = '🔄 Try Again';
            retryBtn.style.cssText = 'padding: 8px 20px;';
            retryBtn.onclick = function () {
                retryBtn.disabled = true;
                retryBtn.innerHTML = '<span class="loading-spinner"></span> Retrying...';
                Promise.resolve(retryCallback()).finally(() => {
                    retryBtn.disabled = false;
                    retryBtn.innerHTML = '🔄 Try Again';
                });
            };
            actionsContainer.appendChild(retryBtn);
        }

        // Add other actions
        errorInfo.actions.forEach(action => {
            if (action.type === 'info') {
                const info = document.createElement('div');
                info.textContent = action.text;
                info.style.cssText = 'font-size: 12px; color: var(--text-muted);';
                actionsContainer.appendChild(info);
            } else if (action.type === 'action') {
                const btn = document.createElement('button');
                btn.className = 'btn btn-secondary';
                btn.textContent = action.text;
                btn.style.cssText = 'padding: 6px 16px; font-size: 13px;';
                btn.onclick = action.action;
                actionsContainer.appendChild(btn);
            } else if (action.type === 'link') {
                const link = document.createElement('a');
                link.href = action.href;
                link.textContent = action.text;
                link.style.cssText = 'color: var(--primary); font-size: 13px; text-decoration: none;';
                link.onmouseover = () => link.style.textDecoration = 'underline';
                link.onmouseout = () => link.style.textDecoration = 'none';
                actionsContainer.appendChild(link);
            }
        });

        container.appendChild(actionsContainer);
    }

    return container;
}

/**
 * Show error in a container
 * @param {HTMLElement|string} container - Container element or selector
 * @param {Error|number} error - Error object or HTTP status code
 * @param {object} options - Display options
 */
export function showError(container, error, options = {}) {
    const el = typeof container === 'string' ? document.querySelector(container) : container;
    if (!el) return;

    el.innerHTML = '';
    el.appendChild(createErrorDisplay(error, options));
}

/**
 * Show a toast notification for errors
 * @param {Error|number} error - Error object or HTTP status code
 * @param {object} options - Toast options
 */
export function showErrorToast(error, options = {}) {
    const { duration = 5000, customMessage = null } = options;
    const errorInfo = getErrorInfo(error, customMessage);

    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--bg-card, #252540);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 8px;
        padding: 16px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        max-width: 400px;
    `;

    toast.innerHTML = `
        <span style="font-size: 20px;">${errorInfo.icon}</span>
        <div>
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 2px;">${escapeHtml(errorInfo.title)}</div>
            <div style="font-size: 13px; color: var(--text-muted);">${escapeHtml(errorInfo.message)}</div>
        </div>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 4px; font-size: 18px;">&times;</button>
    `;

    // Add animation keyframes if not already present
    if (typeof document !== 'undefined' && !document.getElementById('error-toast-styles')) {
        const style = document.createElement('style');
        style.id = 'error-toast-styles';
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

/**
 * Escape HTML to prevent XSS
 */
export function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

export const ErrorMessages = {
    ERROR_TYPES,
    getErrorType,
    getErrorInfo,
    createErrorDisplay,
    showError,
    showErrorToast
};

// Expose to window for backward compatibility
if (typeof window !== 'undefined') {
    window.ErrorMessages = ErrorMessages;
}

export default ErrorMessages;
