/**
 * Unit Tests for constants.js
 */

import { 
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
} from '../constants.js';

describe('constants.js', () => {
    
    describe('TIMEOUTS', () => {
        it('should have API_REQUEST timeout', () => {
            expect(TIMEOUTS.API_REQUEST).toBe(10000);
        });

        it('should have FAILSAFE timeout', () => {
            expect(TIMEOUTS.FAILSAFE).toBe(15000);
        });

        it('should have REFRESH_INTERVAL', () => {
            expect(TIMEOUTS.REFRESH_INTERVAL).toBe(60000);
        });

        it('should have all required timeout values', () => {
            expect(TIMEOUTS).toHaveProperty('API_REQUEST');
            expect(TIMEOUTS).toHaveProperty('FAILSAFE');
            expect(TIMEOUTS).toHaveProperty('TOAST_DISPLAY');
            expect(TIMEOUTS).toHaveProperty('REFRESH_INTERVAL');
            expect(TIMEOUTS).toHaveProperty('DEBOUNCE');
        });
    });

    describe('ENDPOINTS', () => {
        it('should have TIERS endpoints', () => {
            expect(ENDPOINTS.TIERS.CURRENT).toBe('/api/tiers/current');
            expect(ENDPOINTS.TIERS.LIST).toBe('/api/tiers');
            expect(ENDPOINTS.TIERS.UPGRADE).toBe('/api/tiers/upgrade');
        });

        it('should have USER endpoints', () => {
            expect(ENDPOINTS.USER.PROFILE).toBe('/api/user/profile');
            expect(ENDPOINTS.USER.BALANCE).toBe('/api/user/balance');
        });

        it('should have AUTH endpoints', () => {
            expect(ENDPOINTS.AUTH.LOGIN).toBe('/auth/login');
            expect(ENDPOINTS.AUTH.LOGOUT).toBe('/api/auth/logout');
        });
    });

    describe('STATES', () => {
        it('should have all UI states', () => {
            expect(STATES.INITIAL).toBe('initial');
            expect(STATES.LOADING).toBe('loading');
            expect(STATES.LOADED).toBe('loaded');
            expect(STATES.ERROR).toBe('error');
            expect(STATES.TIMEOUT).toBe('timeout');
            expect(STATES.UNAUTHENTICATED).toBe('unauthenticated');
            expect(STATES.SESSION_EXPIRED).toBe('session-expired');
        });
    });

    describe('TIERS', () => {
        it('should have all tier codes', () => {
            expect(TIERS.FREEMIUM).toBe('freemium');
            expect(TIERS.PAYG).toBe('payg');
            expect(TIERS.PRO).toBe('pro');
            expect(TIERS.CUSTOM).toBe('custom');
        });
    });

    describe('TIER_DISPLAY_NAMES', () => {
        it('should have display names for all tiers', () => {
            expect(TIER_DISPLAY_NAMES[TIERS.FREEMIUM]).toBe('Freemium');
            expect(TIER_DISPLAY_NAMES[TIERS.PAYG]).toBe('Pay-As-You-Go');
            expect(TIER_DISPLAY_NAMES[TIERS.PRO]).toBe('Pro');
            expect(TIER_DISPLAY_NAMES[TIERS.CUSTOM]).toBe('Custom');
        });
    });

    describe('TIER_BADGE_CLASSES', () => {
        it('should have badge classes for all tiers', () => {
            expect(TIER_BADGE_CLASSES[TIERS.FREEMIUM]).toBe('tier-badge-freemium');
            expect(TIER_BADGE_CLASSES[TIERS.PAYG]).toBe('tier-badge-payg');
            expect(TIER_BADGE_CLASSES[TIERS.PRO]).toBe('tier-badge-pro');
            expect(TIER_BADGE_CLASSES[TIERS.CUSTOM]).toBe('tier-badge-custom');
        });
    });

    describe('TIER_FEATURES', () => {
        it('should have features for all tiers', () => {
            expect(TIER_FEATURES[TIERS.FREEMIUM]).toBeInstanceOf(Array);
            expect(TIER_FEATURES[TIERS.PAYG]).toBeInstanceOf(Array);
            expect(TIER_FEATURES[TIERS.PRO]).toBeInstanceOf(Array);
            expect(TIER_FEATURES[TIERS.CUSTOM]).toBeInstanceOf(Array);
        });

        it('should have feature objects with text and available properties', () => {
            const feature = TIER_FEATURES[TIERS.FREEMIUM][0];
            expect(feature).toHaveProperty('text');
            expect(feature).toHaveProperty('available');
        });
    });

    describe('TIER_CTA_CONFIG', () => {
        it('should have CTA config for all tiers', () => {
            expect(TIER_CTA_CONFIG[TIERS.FREEMIUM]).toBeInstanceOf(Array);
            expect(TIER_CTA_CONFIG[TIERS.PAYG]).toBeInstanceOf(Array);
            expect(TIER_CTA_CONFIG[TIERS.PRO]).toBeInstanceOf(Array);
            expect(TIER_CTA_CONFIG[TIERS.CUSTOM]).toBeInstanceOf(Array);
        });

        it('should have CTA objects with required properties', () => {
            const cta = TIER_CTA_CONFIG[TIERS.FREEMIUM][0];
            expect(cta).toHaveProperty('id');
            expect(cta).toHaveProperty('label');
            expect(cta).toHaveProperty('variant');
        });

        it('freemium should have upgrade and compare buttons', () => {
            const ids = TIER_CTA_CONFIG[TIERS.FREEMIUM].map(c => c.id);
            expect(ids).toContain('upgrade-btn');
            expect(ids).toContain('compare-plans-btn');
        });
    });

    describe('STORAGE_KEYS', () => {
        it('should have all storage keys', () => {
            expect(STORAGE_KEYS.ACCESS_TOKEN).toBe('access_token');
            expect(STORAGE_KEYS.REFRESH_TOKEN).toBe('refresh_token');
            expect(STORAGE_KEYS.TOKEN_EXPIRES).toBe('token_expires_at');
            expect(STORAGE_KEYS.CACHED_TIER).toBe('cached_tier_data');
        });
    });

    describe('HTTP_STATUS', () => {
        it('should have common HTTP status codes', () => {
            expect(HTTP_STATUS.OK).toBe(200);
            expect(HTTP_STATUS.UNAUTHORIZED).toBe(401);
            expect(HTTP_STATUS.NOT_FOUND).toBe(404);
            expect(HTTP_STATUS.TIMEOUT).toBe(408);
            expect(HTTP_STATUS.SERVER_ERROR).toBe(500);
        });
    });
});
