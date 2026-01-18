/**
 * Application Constants
 * Single source of truth for magic numbers and configuration
 */

// Timeouts (milliseconds)
export const TIMEOUTS = {
    API_REQUEST: 10_000,
    FAILSAFE: 15_000,
    TOAST_DISPLAY: 3_000,
    REFRESH_INTERVAL: 60_000,
    DEBOUNCE: 300,
    TOKEN_REFRESH_BUFFER: 60_000 // Refresh token 1 min before expiry
};

// API Endpoints
// API Endpoints
export const ENDPOINTS = {
    TIERS: {
        CURRENT: '/api/tiers/current',
        LIST: '/api/tiers',
        UPGRADE: '/api/tiers/upgrade'
    },
    USER: {
        PROFILE: '/api/user/profile',
        BALANCE: '/api/user/balance',
        ME: '/api/user/me',
        SETTINGS: '/api/user/settings',
        CREDITS_HISTORY: '/api/user/credits/history',
        CREDITS_SUMMARY: '/api/user/credits/summary'
    },
    AUTH: {
        LOGIN: '/api/auth/login',
        LOGOUT: '/api/auth/logout',
        REFRESH: '/api/auth/refresh'
    },
    ANALYTICS: {
        SUMMARY: '/api/analytics/summary'
    },
    DASHBOARD: {
        ACTIVITY: '/api/dashboard/activity/recent'
    },
    BILLING: {
        HISTORY: '/api/billing/history',
        REFUND: '/api/billing/refund',
        REFUNDS: '/api/billing/refunds',
        TRANSACTIONS: '/api/billing/transactions'
    },
    NOTIFICATIONS: {
        LIST: '/api/notifications',
        MARK_READ: '/api/notifications/{id}/read',
        MARK_ALL_READ: '/api/notifications/mark-all-read'
    },
    GDPR: {
        EXPORT: '/api/gdpr/export',
        DELETE: '/api/gdpr/account'
    },
    FORWARDING: {
        CONFIG: '/api/forwarding',
        CONFIGURE: '/api/forwarding/configure',
        TEST: '/api/forwarding/test'
    },
    PROVIDERS: {
        HEALTH: '/api/providers/health'
    }
};

// UI States
export const STATES = {
    INITIAL: 'initial',
    LOADING: 'loading',
    LOADED: 'loaded',
    ERROR: 'error',
    TIMEOUT: 'timeout',
    UNAUTHENTICATED: 'unauthenticated',
    SESSION_EXPIRED: 'session-expired'
};

// Tier Configuration
export const TIERS = {
    FREEMIUM: 'freemium',
    PAYG: 'payg',
    PRO: 'pro',
    CUSTOM: 'custom'
};

export const TIER_DISPLAY_NAMES = {
    [TIERS.FREEMIUM]: 'Freemium',
    [TIERS.PAYG]: 'Pay-As-You-Go',
    [TIERS.PRO]: 'Pro',
    [TIERS.CUSTOM]: 'Custom'
};

export const TIER_BADGE_CLASSES = {
    [TIERS.FREEMIUM]: 'tier-badge-freemium',
    [TIERS.PAYG]: 'tier-badge-payg',
    [TIERS.PRO]: 'tier-badge-pro',
    [TIERS.CUSTOM]: 'tier-badge-custom'
};

export const TIER_FEATURES = {
    [TIERS.FREEMIUM]: [
        { text: 'Basic SMS verification', available: true },
        { text: 'Web dashboard access', available: true },
        { text: 'API access', available: false },
        { text: 'Voice verification', available: false }
    ],
    [TIERS.PAYG]: [
        { text: 'SMS verification', available: true },
        { text: 'API access', available: true },
        { text: 'Voice verification', available: true },
        { text: 'Area code selection', available: true }
    ],
    [TIERS.PRO]: [
        { text: 'All Pay-As-You-Go features', available: true },
        { text: 'Bulk purchase discounts', available: true },
        { text: 'ISP filtering', available: true },
        { text: 'Priority support', available: true }
    ],
    [TIERS.CUSTOM]: [
        { text: 'All Pro features', available: true },
        { text: 'Custom branding', available: true },
        { text: 'Dedicated support', available: true },
        { text: 'Volume discounts', available: true }
    ]
};

export const TIER_CTA_CONFIG = {
    [TIERS.FREEMIUM]: [
        { id: 'upgrade-btn', label: 'Upgrade', href: '/pricing', variant: 'primary' },
        { id: 'compare-plans-btn', label: 'Compare Plans', action: 'showComparePlansModal', variant: 'secondary' }
    ],
    [TIERS.PAYG]: [
        { id: 'add-credits-btn', label: 'Add Credits', href: '/wallet', variant: 'primary' },
        { id: 'upgrade-btn', label: 'Upgrade to Pro', href: '/pricing?plan=pro', variant: 'secondary' },
        { id: 'compare-plans-btn', label: 'Compare Plans', action: 'showComparePlansModal', variant: 'secondary' }
    ],
    [TIERS.PRO]: [
        { id: 'usage-btn', label: 'View Usage', href: '/analytics', variant: 'primary' },
        { id: 'compare-plans-btn', label: 'Compare Plans', action: 'showComparePlansModal', variant: 'secondary' },
        { id: 'manage-btn', label: 'Manage Billing', href: '/settings#billing', variant: 'secondary' }
    ],
    [TIERS.CUSTOM]: [
        { id: 'usage-btn', label: 'View Usage', href: '/analytics', variant: 'primary' },
        { id: 'contact-btn', label: 'Contact Support', href: '/support', variant: 'secondary' },
        { id: 'manage-btn', label: 'Manage Billing', href: '/settings#billing', variant: 'secondary' }
    ]
};

// Local Storage Keys
export const STORAGE_KEYS = {
    ACCESS_TOKEN: 'access_token',
    REFRESH_TOKEN: 'refresh_token',
    TOKEN_EXPIRES: 'token_expires_at',
    CACHED_TIER: 'cached_tier_data',
    THEME: 'theme',
    SIDEBAR_COLLAPSED: 'sidebarCollapsed',
    LANGUAGE: 'language',
    CURRENCY: 'currency'
};

// HTTP Status Codes
export const HTTP_STATUS = {
    OK: 200,
    CREATED: 201,
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    TIMEOUT: 408,
    TOO_MANY_REQUESTS: 429,
    SERVER_ERROR: 500,
    SERVICE_UNAVAILABLE: 503
};

// For non-module scripts (IIFE compatibility)
if (typeof window !== 'undefined') {
    window.APP_CONSTANTS = {
        TIMEOUTS,
        ENDPOINTS,
        STATES,
        TIERS,
        TIER_DISPLAY_NAMES,
        TIER_BADGE_CLASSES,
        TIER_FEATURES,
        TIER_CTA_CONFIG,
        STORAGE_KEYS,
        HTTP_STATUS
    };
}
