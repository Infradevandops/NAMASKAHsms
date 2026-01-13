/**
 * Unit Tests for tier-card.js
 */

import { TierCard, initTierCard } from '../tier-card.js';
import { STATES, STORAGE_KEYS } from '../constants.js';

// Mock fetch
global.fetch = jest.fn();

// Mock DOM
document.body.innerHTML = `
    <div id="tier-card">
        <div id="tier-name"></div>
        <div id="tier-price"></div>
        <div id="tier-features-list"></div>
        <button id="upgrade-btn"></button>
        <button id="compare-plans-btn"></button>
        <button id="add-credits-btn"></button>
        <button id="usage-btn"></button>
        <button id="manage-btn"></button>
        <button id="contact-btn"></button>
    </div>
    <div id="quota-card" style="display: none;">
        <div id="quota-fill"></div>
        <div id="quota-text"></div>
    </div>
    <div id="api-stats-card" style="display: none;">
        <div id="api-sms-count"></div>
        <div id="api-calls-count"></div>
        <div id="api-keys-count"></div>
    </div>
`;

describe('tier-card.js', () => {
    let tierCard;

    beforeEach(() => {
        localStorage.clear();
        fetch.mockClear();
        tierCard = new TierCard('tier-card');
    });

    afterEach(() => {
        if (tierCard) {
            tierCard.destroy();
        }
    });

    describe('TierCard constructor', () => {
        it('should initialize with container', () => {
            expect(tierCard.container).toBe(document.getElementById('tier-card'));
        });

        it('should have initial state', () => {
            expect(tierCard.state).toBe(STATES.INITIAL);
        });

        it('should have element references', () => {
            expect(tierCard.elements.tierName).toBe(document.getElementById('tier-name'));
            expect(tierCard.elements.tierPrice).toBe(document.getElementById('tier-price'));
            expect(tierCard.elements.featuresList).toBe(document.getElementById('tier-features-list'));
        });
    });

    describe('setState', () => {
        it('should set loading state', () => {
            tierCard.setState(STATES.LOADING);
            
            expect(tierCard.state).toBe(STATES.LOADING);
            expect(tierCard.container.classList.contains('tier-card-loading')).toBe(true);
            expect(tierCard.container.getAttribute('aria-busy')).toBe('true');
        });

        it('should set unauthenticated state', () => {
            tierCard.setState(STATES.UNAUTHENTICATED);
            
            expect(tierCard.state).toBe(STATES.UNAUTHENTICATED);
            expect(tierCard.elements.tierName.innerHTML).toContain('Not logged in');
        });

        it('should set session-expired state', () => {
            tierCard.setState(STATES.SESSION_EXPIRED);
            
            expect(tierCard.state).toBe(STATES.SESSION_EXPIRED);
            expect(tierCard.elements.tierName.innerHTML).toContain('Session expired');
        });

        it('should set timeout state', () => {
            tierCard.setState(STATES.TIMEOUT);
            
            expect(tierCard.state).toBe(STATES.TIMEOUT);
            expect(tierCard.elements.tierName.innerHTML).toContain('timed out');
        });

        it('should set error state with message', () => {
            tierCard.setState(STATES.ERROR, { message: 'Test error' });
            
            expect(tierCard.state).toBe(STATES.ERROR);
            expect(tierCard.elements.featuresList.innerHTML).toContain('Test error');
        });

        it('should set loaded state with data', () => {
            const mockData = {
                current_tier: 'freemium',
                price_monthly: 0,
                quota_usd: 0
            };
            
            tierCard.setState(STATES.LOADED, mockData);
            
            expect(tierCard.state).toBe(STATES.LOADED);
            expect(tierCard.container.classList.contains('tier-card-loaded')).toBe(true);
            expect(tierCard.container.getAttribute('aria-busy')).toBe('false');
        });
    });

    describe('load', () => {
        it('should show unauthenticated when no token', async () => {
            await tierCard.load();
            
            expect(tierCard.state).toBe(STATES.UNAUTHENTICATED);
        });

        it('should load tier data when authenticated', async () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'test-token');
            
            fetch.mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: () => Promise.resolve({
                    current_tier: 'pro',
                    tier_name: 'Pro',
                    price_monthly: 25,
                    quota_usd: 30,
                    quota_used_usd: 5,
                    features: { api_key_limit: 10 }
                })
            });

            await tierCard.load();

            expect(tierCard.state).toBe(STATES.LOADED);
            expect(tierCard.currentData.current_tier).toBe('pro');
        });

        it('should show session-expired on 401', async () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'expired-token');
            
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 401
            });

            await tierCard.load();

            expect(tierCard.state).toBe(STATES.SESSION_EXPIRED);
        });

        it('should use cached data on error', async () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'test-token');
            localStorage.setItem(STORAGE_KEYS.CACHED_TIER, JSON.stringify({
                current_tier: 'payg',
                price_monthly: 0
            }));
            
            fetch.mockRejectedValueOnce(new Error('Network error'));

            await tierCard.load();

            expect(tierCard.state).toBe(STATES.LOADED);
            expect(tierCard.elements.featuresList.innerHTML).toContain('cached data');
        });

        it('should show error when no cached data available', async () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'test-token');
            
            fetch.mockRejectedValueOnce(new Error('Network error'));

            await tierCard.load();

            expect(tierCard.state).toBe(STATES.ERROR);
        });
    });

    describe('CTA rendering', () => {
        it('should show upgrade and compare for freemium', () => {
            const mockData = {
                current_tier: 'freemium',
                price_monthly: 0
            };
            
            tierCard.setState(STATES.LOADED, mockData);

            expect(document.getElementById('upgrade-btn').style.display).toBe('inline-flex');
            expect(document.getElementById('compare-plans-btn').style.display).toBe('inline-flex');
            expect(document.getElementById('add-credits-btn').style.display).toBe('none');
        });

        it('should show add-credits for payg', () => {
            const mockData = {
                current_tier: 'payg',
                price_monthly: 0
            };
            
            tierCard.setState(STATES.LOADED, mockData);

            expect(document.getElementById('add-credits-btn').style.display).toBe('inline-flex');
        });

        it('should show usage and manage for pro', () => {
            const mockData = {
                current_tier: 'pro',
                price_monthly: 25,
                quota_usd: 30
            };
            
            tierCard.setState(STATES.LOADED, mockData);

            expect(document.getElementById('usage-btn').style.display).toBe('inline-flex');
            expect(document.getElementById('manage-btn').style.display).toBe('inline-flex');
        });
    });

    describe('destroy', () => {
        it('should clear timers and abort controller', () => {
            tierCard.timeoutId = setTimeout(() => {}, 10000);
            tierCard.failsafeId = setTimeout(() => {}, 15000);
            tierCard.abortController = new AbortController();

            tierCard.destroy();

            expect(tierCard.timeoutId).toBeNull();
            expect(tierCard.failsafeId).toBeNull();
        });
    });

    describe('initTierCard', () => {
        it('should create and initialize tier card', () => {
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'test-token');
            
            fetch.mockResolvedValueOnce({
                ok: true,
                status: 200,
                json: () => Promise.resolve({ current_tier: 'freemium' })
            });

            const card = initTierCard('tier-card');

            expect(card).toBeInstanceOf(TierCard);
            expect(window.tierCard).toBe(card);
        });
    });
});
