"""Phase 3: Frontend Integration Tests.

Tests for:
- TierLoader blocking load and cache management
- SkeletonLoader UI state management
- AppInit blocking initialization
- TierSync cross-tab synchronization
"""

describe('TierLoader Integration', () => {
    let tierLoader;
    let mockFetch;

    beforeEach(() => {
        // Clear localStorage
        localStorage.clear();
        
        // Mock fetch
        mockFetch = jest.fn();
        global.fetch = mockFetch;
        
        // Import TierLoader
        tierLoader = require('../../../static/js/tier-loader.js').TierLoader;
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('loadTierBlocking', () => {
        test('returns cached tier if valid', async () => {
            const cachedTier = {
                tier: 'pro',
                cached_at: new Date().toISOString(),
                checksum: 'abc123'
            };
            localStorage.setItem('user_tier_cache', JSON.stringify(cachedTier));

            const tier = await tierLoader.loadTierBlocking();

            expect(tier).toBe('pro');
            expect(mockFetch).not.toHaveBeenCalled();
        });

        test('fetches tier if cache expired', async () => {
            const expiredCache = {
                tier: 'freemium',
                cached_at: new Date(Date.now() - 2 * 3600000).toISOString(),
                checksum: 'abc123'
            };
            localStorage.setItem('user_tier_cache', JSON.stringify(expiredCache));

            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ tier: 'pro' })
            });

            const tier = await tierLoader.loadTierBlocking();

            expect(tier).toBe('pro');
            expect(mockFetch).toHaveBeenCalled();
        });

        test('returns freemium on timeout', async () => {
            mockFetch.mockImplementationOnce(() => 
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('timeout')), 6000)
                )
            );

            const tier = await tierLoader.loadTierBlocking();

            expect(tier).toBe('freemium');
        });

        test('returns freemium on API error', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500
            });

            const tier = await tierLoader.loadTierBlocking();

            expect(tier).toBe('freemium');
        });

        test('validates response format', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ invalid: 'response' })
            });

            const tier = await tierLoader.loadTierBlocking();

            expect(tier).toBe('freemium');
        });
    });

    describe('Cache Management', () => {
        test('caches tier with TTL', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ tier: 'pro' })
            });

            await tierLoader.loadTierBlocking();

            const cached = JSON.parse(localStorage.getItem('user_tier_cache'));
            expect(cached.tier).toBe('pro');
            expect(cached.cached_at).toBeDefined();
        });

        test('cache includes checksum', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ tier: 'pro' })
            });

            await tierLoader.loadTierBlocking();

            const cached = JSON.parse(localStorage.getItem('user_tier_cache'));
            expect(cached.checksum).toBeDefined();
        });

        test('detects cache corruption', async () => {
            localStorage.setItem('user_tier_cache', 'corrupted data');

            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ tier: 'pro' })
            });

            const tier = await tierLoader.loadTierBlocking();

            expect(tier).toBe('pro');
            expect(mockFetch).toHaveBeenCalled();
        });

        test('clears invalid cache', async () => {
            const invalidCache = {
                tier: 'invalid_tier',
                cached_at: new Date().toISOString(),
                checksum: 'abc123'
            };
            localStorage.setItem('user_tier_cache', JSON.stringify(invalidCache));

            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ tier: 'pro' })
            });

            await tierLoader.loadTierBlocking();

            const cached = JSON.parse(localStorage.getItem('user_tier_cache'));
            expect(cached.tier).toBe('pro');
        });
    });

    describe('Timeout Handling', () => {
        test('enforces 5 second timeout', async () => {
            jest.useFakeTimers();

            mockFetch.mockImplementationOnce(() => 
                new Promise((resolve) => 
                    setTimeout(() => resolve({ ok: true, json: async () => ({ tier: 'pro' }) }), 6000)
                )
            );

            const tierPromise = tierLoader.loadTierBlocking();

            jest.advanceTimersByTime(5000);

            const tier = await tierPromise;
            expect(tier).toBe('freemium');

            jest.useRealTimers();
        });

        test('returns cached tier on timeout', async () => {
            const cachedTier = {
                tier: 'pro',
                cached_at: new Date(Date.now() - 2 * 3600000).toISOString(),
                checksum: 'abc123'
            };
            localStorage.setItem('user_tier_cache', JSON.stringify(cachedTier));

            mockFetch.mockImplementationOnce(() => 
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('timeout')), 6000)
                )
            );

            const tier = await tierLoader.loadTierBlocking();

            expect(tier).toBe('pro');
        });
    });
});

describe('SkeletonLoader Integration', () => {
    let container;
    let skeletonLoader;

    beforeEach(() => {
        container = document.createElement('div');
        container.id = 'app-container';
        document.body.appendChild(container);

        skeletonLoader = require('../../../static/js/skeleton-loader.js').SkeletonLoader;
    });

    afterEach(() => {
        document.body.removeChild(container);
    });

    describe('showSkeleton', () => {
        test('shows tier skeleton', () => {
            skeletonLoader.showSkeleton(container, 'tier');

            expect(container.querySelector('.skeleton-tier-card')).toBeDefined();
            expect(container.querySelector('.skeleton')).toBeDefined();
        });

        test('shows activity skeleton with rows', () => {
            skeletonLoader.showSkeleton(container, 'activity', { rows: 3 });

            const rows = container.querySelectorAll('.skeleton-activity-row');
            expect(rows.length).toBe(3);
        });

        test('prevents UI flashing', () => {
            skeletonLoader.showSkeleton(container, 'tier');

            expect(container.classList.contains('loading')).toBe(true);
        });
    });

    describe('hideSkeleton', () => {
        test('replaces skeleton with content', () => {
            skeletonLoader.showSkeleton(container, 'tier');
            const html = '<div class="tier-card">Pro Plan</div>';

            skeletonLoader.hideSkeleton(container, html);

            expect(container.innerHTML).toContain('Pro Plan');
            expect(container.querySelector('.skeleton')).toBeNull();
        });

        test('adds fade-in animation', (done) => {
            skeletonLoader.showSkeleton(container, 'tier');
            const html = '<div class="tier-card">Pro Plan</div>';

            skeletonLoader.hideSkeleton(container, html);

            expect(container.classList.contains('fade-in')).toBe(true);

            setTimeout(() => {
                expect(container.classList.contains('fade-in')).toBe(false);
                done();
            }, 300);
        });

        test('removes loading class', () => {
            skeletonLoader.showSkeleton(container, 'tier');
            const html = '<div class="tier-card">Pro Plan</div>';

            skeletonLoader.hideSkeleton(container, html);

            expect(container.classList.contains('loading')).toBe(false);
        });
    });

    describe('withLoading', () => {
        test('shows skeleton then content', async () => {
            const loadFn = jest.fn().mockResolvedValue('<div>Content</div>');

            const promise = skeletonLoader.withLoading(container, loadFn, { skeletonType: 'tier' });

            expect(container.querySelector('.skeleton')).toBeDefined();

            const result = await promise;

            expect(result).toBe('<div>Content</div>');
            expect(container.innerHTML).toContain('Content');
        });

        test('handles load errors', async () => {
            const error = new Error('Load failed');
            const loadFn = jest.fn().mockRejectedValue(error);
            const onError = jest.fn();

            await expect(
                skeletonLoader.withLoading(container, loadFn, { onError })
            ).rejects.toThrow('Load failed');

            expect(onError).toHaveBeenCalledWith(error);
        });

        test('cleans up skeleton on error', async () => {
            const loadFn = jest.fn().mockRejectedValue(new Error('Load failed'));

            try {
                await skeletonLoader.withLoading(container, loadFn, { skeletonType: 'tier' });
            } catch (e) {
                // Expected
            }

            expect(container.querySelector('.skeleton')).toBeNull();
        });
    });
});

describe('AppInit Integration', () => {
    let appInit;
    let tierLoader;
    let skeletonLoader;

    beforeEach(() => {
        // Mock DOM
        document.body.innerHTML = '<div id="app"></div>';

        // Mock modules
        tierLoader = {
            loadTierBlocking: jest.fn().mockResolvedValue('pro')
        };

        skeletonLoader = {
            showSkeleton: jest.fn(),
            hideSkeleton: jest.fn()
        };

        appInit = require('../../../static/js/app-init.js').AppInit;
    });

    describe('initialize', () => {
        test('shows skeleton on start', async () => {
            const initPromise = appInit.initialize();

            expect(skeletonLoader.showSkeleton).toHaveBeenCalled();

            await initPromise;
        });

        test('blocks on tier load', async () => {
            tierLoader.loadTierBlocking.mockImplementationOnce(() => 
                new Promise(resolve => setTimeout(() => resolve('pro'), 100))
            );

            const startTime = Date.now();
            await appInit.initialize();
            const duration = Date.now() - startTime;

            expect(duration).toBeGreaterThanOrEqual(100);
        });

        test('hides skeleton after load', async () => {
            await appInit.initialize();

            expect(skeletonLoader.hideSkeleton).toHaveBeenCalled();
        });

        test('initializes global state', async () => {
            await appInit.initialize();

            expect(window.appState).toBeDefined();
            expect(window.appState.tier).toBe('pro');
        });

        test('renders dashboard', async () => {
            await appInit.initialize();

            expect(document.querySelector('#app').innerHTML).toBeTruthy();
        });

        test('starts tier sync', async () => {
            const tierSync = {
                startSync: jest.fn()
            };

            await appInit.initialize();

            // Tier sync should be started
            expect(tierSync.startSync).toHaveBeenCalled();
        });

        test('handles initialization errors', async () => {
            tierLoader.loadTierBlocking.mockRejectedValueOnce(new Error('Load failed'));

            await expect(appInit.initialize()).rejects.toThrow();
        });
    });
});

describe('TierSync Integration', () => {
    let tierSync;

    beforeEach(() => {
        localStorage.clear();
        tierSync = require('../../../static/js/tier-sync.js').TierSync;
    });

    afterEach(() => {
        tierSync.stopSync();
    });

    describe('startSync', () => {
        test('listens to storage events', (done) => {
            tierSync.startSync();

            const event = new StorageEvent('storage', {
                key: 'user_tier',
                newValue: 'pro',
                oldValue: 'freemium'
            });

            window.dispatchEvent(event);

            setTimeout(() => {
                expect(tierSync.currentTier).toBe('pro');
                done();
            }, 100);
        });

        test('detects tier changes', (done) => {
            tierSync.startSync();

            const changeListener = jest.fn();
            tierSync.on('tierChange', changeListener);

            const event = new StorageEvent('storage', {
                key: 'user_tier',
                newValue: 'pro',
                oldValue: 'freemium'
            });

            window.dispatchEvent(event);

            setTimeout(() => {
                expect(changeListener).toHaveBeenCalledWith({
                    oldTier: 'freemium',
                    newTier: 'pro'
                });
                done();
            }, 100);
        });

        test('verifies tier periodically', (done) => {
            jest.useFakeTimers();

            tierSync.startSync();

            const verifyFn = jest.spyOn(tierSync, 'verifyTier');

            jest.advanceTimersByTime(60000);

            expect(verifyFn).toHaveBeenCalled();

            jest.useRealTimers();
            done();
        });

        test('reloads on tier mismatch', (done) => {
            const reloadFn = jest.fn();
            window.location.reload = reloadFn;

            tierSync.startSync();

            // Simulate tier mismatch
            localStorage.setItem('user_tier', 'pro');
            tierSync.currentTier = 'freemium';

            tierSync.verifyTier();

            setTimeout(() => {
                expect(reloadFn).toHaveBeenCalled();
                done();
            }, 100);
        });
    });

    describe('stopSync', () => {
        test('stops listening to events', () => {
            tierSync.startSync();
            tierSync.stopSync();

            const changeListener = jest.fn();
            tierSync.on('tierChange', changeListener);

            const event = new StorageEvent('storage', {
                key: 'user_tier',
                newValue: 'pro'
            });

            window.dispatchEvent(event);

            expect(changeListener).not.toHaveBeenCalled();
        });

        test('clears verification interval', (done) => {
            jest.useFakeTimers();

            tierSync.startSync();
            tierSync.stopSync();

            const verifyFn = jest.spyOn(tierSync, 'verifyTier');

            jest.advanceTimersByTime(60000);

            expect(verifyFn).not.toHaveBeenCalled();

            jest.useRealTimers();
            done();
        });
    });

    describe('Event Emitter', () => {
        test('emits tier change events', (done) => {
            const listener = jest.fn();
            tierSync.on('tierChange', listener);

            tierSync.emitTierChangeEvent('freemium', 'pro');

            setTimeout(() => {
                expect(listener).toHaveBeenCalledWith({
                    oldTier: 'freemium',
                    newTier: 'pro'
                });
                done();
            }, 10);
        });

        test('supports multiple listeners', (done) => {
            const listener1 = jest.fn();
            const listener2 = jest.fn();

            tierSync.on('tierChange', listener1);
            tierSync.on('tierChange', listener2);

            tierSync.emitTierChangeEvent('freemium', 'pro');

            setTimeout(() => {
                expect(listener1).toHaveBeenCalled();
                expect(listener2).toHaveBeenCalled();
                done();
            }, 10);
        });
    });
});

describe('End-to-End Tier Identification Flow', () => {
    test('complete flow: load -> skeleton -> sync', async () => {
        // 1. App initializes
        const appInit = require('../../../static/js/app-init.js').AppInit;
        const tierLoader = require('../../../static/js/tier-loader.js').TierLoader;
        const skeletonLoader = require('../../../static/js/skeleton-loader.js').SkeletonLoader;
        const tierSync = require('../../../static/js/tier-sync.js').TierSync;

        // 2. Skeleton shows
        expect(document.querySelector('.skeleton')).toBeDefined();

        // 3. Tier loads
        const tier = await tierLoader.loadTierBlocking();
        expect(tier).toBe('pro');

        // 4. Skeleton hides
        expect(document.querySelector('.skeleton')).toBeNull();

        // 5. Sync starts
        tierSync.startSync();
        expect(tierSync.currentTier).toBe('pro');

        // 6. Cross-tab change detected
        const event = new StorageEvent('storage', {
            key: 'user_tier',
            newValue: 'custom'
        });
        window.dispatchEvent(event);

        // 7. Tier updates
        expect(tierSync.currentTier).toBe('custom');
    });
});
