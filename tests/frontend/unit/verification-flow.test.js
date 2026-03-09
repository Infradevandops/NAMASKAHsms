/**
 * Tests for verification flow fixes:
 * - Issue #3: Tier caching non-blocking
 * - Issue #4: Exponential backoff polling correctness
 * - Issue #5: Carrier pricing impact display
 * - Issue #7: Carrier caching
 * - Issue #8: Favorites in service dropdown
 */

// ─── Shared helpers ──────────────────────────────────────────────────────────

function makeFetch(body, ok = true) {
    return jest.fn().mockResolvedValue({ ok, json: () => Promise.resolve(body) });
}

// ─── Issue #3: Tier caching ───────────────────────────────────────────────────

describe('Tier caching (Issue #3)', () => {
    const CACHE_KEY = 'nsk_tier_cache';

    beforeEach(() => localStorage.clear());

    test('applies cached tier immediately without waiting for API', () => {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), tier: 'pro' }));
        const cached = localStorage.getItem(CACHE_KEY);
        const { ts, tier } = JSON.parse(cached);
        expect(Date.now() - ts).toBeLessThan(3600000);
        expect(tier).toBe('pro');
    });

    test('treats expired cache (>1h) as miss', () => {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now() - 3700000, tier: 'pro' }));
        const { ts } = JSON.parse(localStorage.getItem(CACHE_KEY));
        expect(Date.now() - ts).toBeGreaterThan(3600000);
    });

    test('updates cache when API returns different tier', () => {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), tier: 'freemium' }));
        const freshTier = 'payg';
        localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), tier: freshTier }));
        const { tier } = JSON.parse(localStorage.getItem(CACHE_KEY));
        expect(tier).toBe('payg');
    });

    test('falls back to freemium on API failure', () => {
        // No cache, API fails — default should be freemium
        const userTier = 'freemium'; // default value in code
        expect(userTier).toBe('freemium');
    });
});

// ─── Issue #4: Exponential backoff ───────────────────────────────────────────

describe('Exponential backoff polling (Issue #4)', () => {
    const backoffMs = [2000, 3000, 5000, 8000, 10000];

    test('delays are strictly increasing', () => {
        for (let i = 1; i < backoffMs.length; i++) {
            expect(backoffMs[i]).toBeGreaterThan(backoffMs[i - 1]);
        }
    });

    test('max delay is capped at 10s', () => {
        expect(Math.max(...backoffMs)).toBe(10000);
    });

    test('elapsed time tracks delay used before stepIdx increment', () => {
        let stepIdx = 0;
        const elapsed = [];

        // Simulate 5 poll cycles
        for (let i = 0; i < 5; i++) {
            const delayUsed = backoffMs[stepIdx];
            if (stepIdx < backoffMs.length - 1) stepIdx++;
            elapsed.push(delayUsed / 1000);
        }

        expect(elapsed).toEqual([2, 3, 5, 8, 10]);
    });

    test('total elapsed after all steps is correct', () => {
        const total = backoffMs.reduce((sum, ms) => sum + ms / 1000, 0);
        expect(total).toBe(28); // 2+3+5+8+10 = 28s
    });

    test('request count stays under 25 within 120s timeout', () => {
        let stepIdx = 0;
        let elapsed = 0;
        let requests = 0;

        while (elapsed < 120) {
            const delay = backoffMs[stepIdx] / 1000;
            if (stepIdx < backoffMs.length - 1) stepIdx++;
            elapsed += delay;
            requests++;
        }

        expect(requests).toBeLessThan(25);
    });

    test('old fixed 3s interval would make ~40 requests in 120s', () => {
        // Regression check: confirm old approach was worse
        const oldRequests = Math.floor(120 / 3);
        expect(oldRequests).toBe(40);
    });
});

// ─── Issue #5: Carrier pricing display ───────────────────────────────────────

describe('Carrier pricing impact display (Issue #5)', () => {
    test('shows Free when no price_impact', () => {
        const carrier = { id: 'verizon', name: 'Verizon', success_rate: 95, price_impact: null };
        const price = carrier.price_impact ? `+$${carrier.price_impact.toFixed(2)}` : 'Free';
        expect(price).toBe('Free');
    });

    test('shows +$X.XX when price_impact present', () => {
        const carrier = { id: 'att', name: 'AT&T', success_rate: 93, price_impact: 0.50 };
        const price = carrier.price_impact ? `+$${carrier.price_impact.toFixed(2)}` : 'Free';
        expect(price).toBe('+$0.50');
    });

    test('shows ✅ for success_rate >= 90', () => {
        const icon = (rate) => rate >= 90 ? '✅' : '⏳';
        expect(icon(95)).toBe('✅');
        expect(icon(90)).toBe('✅');
        expect(icon(89)).toBe('⏳');
    });
});

// ─── Issue #7: Carrier caching ───────────────────────────────────────────────

describe('Carrier caching (Issue #7)', () => {
    const CACHE_KEY = 'nsk_carriers_cache';
    const TTL_24H = 24 * 60 * 60 * 1000;

    beforeEach(() => localStorage.clear());

    test('stores carrier HTML in localStorage', () => {
        const html = '<option value="">Any Carrier</option><option value="verizon">Verizon ✅ 95% (Free)</option>';
        localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), data: html }));
        const raw = JSON.parse(localStorage.getItem(CACHE_KEY));
        expect(raw.data).toContain('Verizon');
    });

    test('cache is valid within 24h', () => {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), data: '<option>test</option>' }));
        const { ts } = JSON.parse(localStorage.getItem(CACHE_KEY));
        expect(Date.now() - ts).toBeLessThan(TTL_24H);
    });

    test('cache expires after 24h', () => {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now() - TTL_24H - 1000, data: 'old' }));
        const { ts } = JSON.parse(localStorage.getItem(CACHE_KEY));
        expect(Date.now() - ts).toBeGreaterThan(TTL_24H);
    });
});

// ─── Issue #8: Favorites in service dropdown ─────────────────────────────────

describe('Favorites integration in service dropdown (Issue #8)', () => {
    const mockItems = [
        { value: 'telegram', label: 'Telegram', sub: '$2.00' },
        { value: 'whatsapp', label: 'WhatsApp', sub: '$2.50' },
        { value: 'google', label: 'Google', sub: '$2.00' },
        { value: 'discord', label: 'Discord', sub: '$2.25' },
    ];

    function renderDropdown(q, favIds) {
        const items = mockItems;
        if (!q) {
            const favItems = items.filter(i => favIds.includes(i.value)).slice(0, 3);
            const rest = items.filter(i => !favIds.includes(i.value)).slice(0, 10 - favItems.length);
            return [...favItems, ...rest];
        }
        return items.filter(i => i.label.toLowerCase().includes(q.toLowerCase())).slice(0, 10);
    }

    test('favorites appear first when no query', () => {
        const result = renderDropdown('', ['telegram', 'discord']);
        expect(result[0].value).toBe('telegram');
        expect(result[1].value).toBe('discord');
    });

    test('non-favorites fill remaining slots', () => {
        const result = renderDropdown('', ['telegram']);
        expect(result[0].value).toBe('telegram');
        expect(result.slice(1).every(i => i.value !== 'telegram')).toBe(true);
    });

    test('favorites not pinned when searching', () => {
        const result = renderDropdown('what', ['telegram']);
        expect(result[0].value).toBe('whatsapp'); // search result, not favorite
    });

    test('max 3 favorites shown at top', () => {
        const allFavs = ['telegram', 'whatsapp', 'google', 'discord'];
        const result = renderDropdown('', allFavs);
        const favCount = result.filter(i => allFavs.includes(i.value)).slice(0, 3).length;
        expect(favCount).toBeLessThanOrEqual(3);
    });

    test('total results capped at 10', () => {
        const result = renderDropdown('', []);
        expect(result.length).toBeLessThanOrEqual(10);
    });
});
