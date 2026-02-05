import { TierManager } from '../../../static/js/tier-manager.js';
import { TIERS } from '../../../static/js/constants.js';

// Mock auth-helpers
jest.mock('../../../static/js/auth-helpers.js', () => ({
    hasAuthToken: jest.fn(),
    getAuthHeaders: jest.fn().mockReturnValue({ 'Authorization': 'Bearer test' })
}));

import { hasAuthToken } from '../../../static/js/auth-helpers.js';

describe('TierManager', () => {
    let tierManager;

    beforeEach(() => {
        document.body.innerHTML = '<div class="header-right"><div class="balance-display"></div></div>';
        hasAuthToken.mockReturnValue(true);
        global.fetch = jest.fn();

        // Use autoInit: false to prevent immediate network calls in constructor
        tierManager = new TierManager({ autoInit: false });
    });

    test('checkFeatureAccess returns true for authorized tiers', () => {
        tierManager.currentTier = TIERS.PRO;
        expect(tierManager.checkFeatureAccess('api_keys')).toBe(true);

        tierManager.currentTier = TIERS.FREEMIUM;
        expect(tierManager.checkFeatureAccess('api_keys')).toBe(false);
    });

    test('loadCurrentTier updates currentTier on success', async () => {
        const mockData = { current_tier: 'payg' };
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockData)
        });

        await tierManager.loadCurrentTier();

        expect(tierManager.currentTier).toBe('payg');
    });

    test('renderTierBadge creates badge element in header', () => {
        tierManager.currentTier = TIERS.PRO;
        tierManager.renderTierBadge();

        const badge = document.querySelector('.tier-badge');
        expect(badge).toBeTruthy();
        expect(badge.textContent).toContain('Pro');
    });

    test('showUpgradeModal appends modal to body', () => {
        tierManager.showUpgradeModal({ required_tier: TIERS.PRO, message: 'Need Pro' });

        const modal = document.querySelector('.upgrade-modal-overlay');
        expect(modal).toBeTruthy();
        expect(modal.innerHTML).toContain('Upgrade Required');
        expect(modal.innerHTML).toContain('Need Pro');
    });

    test('lockFeature adds overlay to element', () => {
        const featureEl = document.createElement('div');
        document.body.appendChild(featureEl);

        tierManager.lockFeature(featureEl, 'api_keys', TIERS.PRO);

        expect(featureEl.classList.contains('feature-locked')).toBe(true);
        expect(featureEl.querySelector('.feature-lock-overlay')).toBeTruthy();
    });
});
