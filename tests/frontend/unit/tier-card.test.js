import { TierCard } from '../../../static/js/tier-card.js';
import { STATES } from '../../../static/js/constants.js';

// Mock auth-helpers
jest.mock('../../../static/js/auth-helpers.js', () => ({
    hasAuthToken: jest.fn(),
    getAuthHeaders: jest.fn().mockReturnValue({ 'Authorization': 'Bearer test' })
}));

import { hasAuthToken } from '../../../static/js/auth-helpers.js';

describe('TierCard', () => {
    let tierCard;
    const containerId = 'tier-card';

    beforeEach(() => {
        // Set up DOM
        document.body.innerHTML = `
            <div id="tier-card">
                <div id="tier-name"></div>
                <div id="tier-price"></div>
                <div id="tier-features-list"></div>
                <button id="upgrade-btn" style="display:none"></button>
                <button id="compare-plans-btn" style="display:none"></button>
                <button id="add-credits-btn" style="display:none"></button>
                <button id="usage-btn" style="display:none"></button>
                <button id="manage-btn" style="display:none"></button>
                <button id="contact-btn" style="display:none"></button>
                <div id="quota-card" style="display:none">
                    <div id="quota-fill"></div>
                    <div id="quota-text"></div>
                </div>
            </div>
        `;

        hasAuthToken.mockReturnValue(true);
        global.fetch = jest.fn();

        tierCard = new TierCard(containerId);
    });

    test('initializes with correct state', () => {
        expect(tierCard.state).toBe(STATES.INITIAL);
    });

    test('shows loading state when load starts', async () => {
        global.fetch.mockReturnValue(new Promise(() => { })); // Never resolves

        tierCard.load();

        expect(tierCard.state).toBe(STATES.LOADING);
        expect(document.getElementById('tier-name').innerHTML).toContain('Loading');
    });

    test('renders tier data correctly after successful load', async () => {
        const mockData = {
            current_tier: 'pro',
            price_monthly: 29
        };

        global.fetch.mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve(mockData)
        });

        await tierCard.load();

        expect(tierCard.state).toBe(STATES.LOADED);
        expect(document.getElementById('tier-name').textContent).toContain('Pro');
        expect(document.getElementById('tier-price').textContent).toBe('$29/month');
    });

    test('handles unauthenticated state', async () => {
        hasAuthToken.mockReturnValue(false);

        await tierCard.load();

        expect(tierCard.state).toBe(STATES.UNAUTHENTICATED);
        expect(document.getElementById('tier-name').textContent).toContain('Not logged in');
    });

    test('handles 401 Unauthorized', async () => {
        global.fetch.mockResolvedValue({
            ok: false,
            status: 401
        });

        await tierCard.load();

        expect(tierCard.state).toBe(STATES.SESSION_EXPIRED);
    });

    test('handles network errors and uses cache', async () => {
        const cachedData = { current_tier: 'freemium' };
        localStorage.setItem('cached_tier_data', JSON.stringify(cachedData));

        global.fetch.mockRejectedValue(new Error('Network error'));

        await tierCard.load();

        expect(tierCard.state).toBe(STATES.LOADED);
        expect(document.getElementById('tier-name').textContent).toContain('Freemium');
        expect(document.body.innerHTML).toContain('Showing cached data');
    });

    test('timeout triggers timeout state', async () => {
        jest.useFakeTimers();

        // Mock a long running fetch
        global.fetch.mockReturnValue(new Promise(resolve => {
            // Will resolve eventually or not
        }));

        tierCard.load();

        // Fast forward time
        jest.advanceTimersByTime(11000); // Default timeout is 10000

        expect(tierCard.state).toBe(STATES.TIMEOUT);

        jest.useRealTimers();
    });
});
