/**
 * Tests for tier-manager.js module
 */

// Mock fetch
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
    store: {},
    getItem: jest.fn((key) => localStorageMock.store[key] || null),
    setItem: jest.fn((key, value) => { localStorageMock.store[key] = value; }),
    removeItem: jest.fn((key) => { delete localStorageMock.store[key]; }),
    clear: jest.fn(() => { localStorageMock.store = {}; })
};
global.localStorage = localStorageMock;

// Mock window
global.window = {
    location: { href: '', pathname: '/dashboard' },
    addEventListener: jest.fn(),
    FrontendLogger: {
        info: jest.fn(),
        warn: jest.fn(),
        error: jest.fn()
    }
};

// Mock document
global.document = {
    readyState: 'complete',
    body: { appendChild: jest.fn() },
    querySelector: jest.fn(),
    createElement: jest.fn(() => ({
        className: '',
        innerHTML: '',
        style: {},
        setAttribute: jest.fn(),
        addEventListener: jest.fn(),
        querySelector: jest.fn(),
        remove: jest.fn(),
        appendChild: jest.fn()
    })),
    addEventListener: jest.fn()
};

// Mock constants
jest.mock('../constants.js', () => ({
    ENDPOINTS: {
        TIERS: {
            CURRENT: '/api/tiers/current',
            UPGRADE: '/api/tiers/upgrade'
        }
    },
    STORAGE_KEYS: {
        ACCESS_TOKEN: 'access_token'
    },
    TIERS: {
        FREEMIUM: 'freemium',
        PAYG: 'payg',
        PRO: 'pro',
        CUSTOM: 'custom'
    },
    TIER_DISPLAY_NAMES: {
        freemium: 'Freemium',
        payg: 'Pay-As-You-Go',
        pro: 'Pro',
        custom: 'Custom'
    }
}));

// Mock auth-helpers
jest.mock('../auth-helpers.js', () => ({
    getAuthToken: jest.fn(() => 'test-token'),
    hasAuthToken: jest.fn(() => true),
    getAuthHeaders: jest.fn(() => ({ 'Authorization': 'Bearer test-token' }))
}));

import {
    FEATURE_ACCESS_MAP,
    FEATURE_NAMES,
    TierManager,
    initTierManager
} from '../tier-manager.js';

describe('tier-manager.js', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorageMock.clear();
        fetch.mockClear();
    });

    describe('FEATURE_ACCESS_MAP', () => {
        it('should define feature access for all tiers', () => {
            expect(FEATURE_ACCESS_MAP.api_keys).toContain('pro');
            expect(FEATURE_ACCESS_MAP.api_keys).toContain('custom');
            expect(FEATURE_ACCESS_MAP.location_filters).toContain('payg');
            expect(FEATURE_ACCESS_MAP.isp_filter).toContain('pro');
        });
    });

    describe('FEATURE_NAMES', () => {
        it('should have display names for all features', () => {
            expect(FEATURE_NAMES.api_keys).toBe('API Keys');
            expect(FEATURE_NAMES.location_filters).toBe('Location Filters');
            expect(FEATURE_NAMES.affiliate_program).toBe('Affiliate Program');
        });
    });

    describe('TierManager', () => {
        describe('constructor', () => {
            it('should create instance with default options', () => {
                const manager = new TierManager({ autoInit: false });
                
                expect(manager.currentTier).toBeNull();
                expect(manager.tierConfig).toBeNull();
            });
        });

        describe('loadCurrentTier', () => {
            it('should load tier from API', async () => {
                const mockData = { current_tier: 'pro', features: {} };
                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve(mockData)
                });

                const manager = new TierManager({ autoInit: false });
                await manager.loadCurrentTier();

                expect(manager.currentTier).toBe('pro');
                expect(manager.tierConfig).toEqual(mockData);
            });

            it('should handle API errors gracefully', async () => {
                fetch.mockRejectedValueOnce(new Error('Network error'));

                const manager = new TierManager({ autoInit: false });
                await manager.loadCurrentTier();

                expect(manager.currentTier).toBeNull();
            });
        });

        describe('getTierDisplayName', () => {
            it('should return display name for tier', () => {
                const manager = new TierManager({ autoInit: false });
                manager.currentTier = 'pro';

                expect(manager.getTierDisplayName()).toBe('Pro');
            });

            it('should return Free for unknown tier', () => {
                const manager = new TierManager({ autoInit: false });
                manager.currentTier = 'unknown';

                expect(manager.getTierDisplayName()).toBe('Free');
            });
        });

        describe('checkFeatureAccess', () => {
            it('should return true for allowed features', () => {
                const manager = new TierManager({ autoInit: false });
                manager.currentTier = 'pro';

                expect(manager.checkFeatureAccess('api_keys')).toBe(true);
                expect(manager.checkFeatureAccess('location_filters')).toBe(true);
            });

            it('should return false for restricted features', () => {
                const manager = new TierManager({ autoInit: false });
                manager.currentTier = 'freemium';

                expect(manager.checkFeatureAccess('api_keys')).toBe(false);
                expect(manager.checkFeatureAccess('dedicated_support')).toBe(false);
            });
        });

        describe('showUpgradeModal', () => {
            it('should create modal element', () => {
                const manager = new TierManager({ autoInit: false });
                manager.currentTier = 'freemium';
                
                manager.showUpgradeModal({ required_tier: 'pro', feature: 'API Keys' });

                expect(document.body.appendChild).toHaveBeenCalled();
            });
        });

        describe('closeUpgradeModal', () => {
            it('should remove modal if exists', () => {
                const mockModal = { remove: jest.fn() };
                document.querySelector.mockReturnValueOnce(mockModal);

                const manager = new TierManager({ autoInit: false });
                manager.closeUpgradeModal();

                expect(mockModal.remove).toHaveBeenCalled();
            });

            it('should handle missing modal gracefully', () => {
                document.querySelector.mockReturnValueOnce(null);

                const manager = new TierManager({ autoInit: false });
                expect(() => manager.closeUpgradeModal()).not.toThrow();
            });
        });

        describe('upgradeTo', () => {
            it('should call upgrade API', async () => {
                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ success: true })
                });

                const manager = new TierManager({ autoInit: false });
                await manager.upgradeTo('pro');

                expect(fetch).toHaveBeenCalledWith(
                    '/api/tiers/upgrade',
                    expect.objectContaining({
                        method: 'POST',
                        body: JSON.stringify({ target_tier: 'pro' })
                    })
                );
            });

            it('should handle upgrade failure', async () => {
                fetch.mockResolvedValueOnce({
                    ok: false,
                    json: () => Promise.resolve({ detail: 'Upgrade failed' })
                });

                const manager = new TierManager({ autoInit: false });
                await manager.upgradeTo('pro');

                // Should not throw, just show error
                expect(fetch).toHaveBeenCalled();
            });
        });

        describe('lockFeature', () => {
            it('should add lock overlay to element', () => {
                const mockElement = {
                    classList: { add: jest.fn() },
                    setAttribute: jest.fn(),
                    style: {},
                    appendChild: jest.fn(),
                    querySelector: jest.fn()
                };

                const manager = new TierManager({ autoInit: false });
                manager.lockFeature(mockElement, 'api_keys', 'pro');

                expect(mockElement.classList.add).toHaveBeenCalledWith('feature-locked');
                expect(mockElement.setAttribute).toHaveBeenCalledWith('aria-disabled', 'true');
            });

            it('should handle null element', () => {
                const manager = new TierManager({ autoInit: false });
                expect(() => manager.lockFeature(null, 'api_keys', 'pro')).not.toThrow();
            });
        });

        describe('unlockFeature', () => {
            it('should remove lock from element', () => {
                const mockOverlay = { remove: jest.fn() };
                const mockElement = {
                    classList: { remove: jest.fn() },
                    removeAttribute: jest.fn(),
                    querySelector: jest.fn(() => mockOverlay)
                };

                const manager = new TierManager({ autoInit: false });
                manager.unlockFeature(mockElement);

                expect(mockElement.classList.remove).toHaveBeenCalledWith('feature-locked');
                expect(mockOverlay.remove).toHaveBeenCalled();
            });
        });
    });

    describe('initTierManager', () => {
        it('should create and return TierManager instance', () => {
            const manager = initTierManager({ autoInit: false });
            
            expect(manager).toBeInstanceOf(TierManager);
            expect(window.tierManager).toBe(manager);
        });
    });
});
