import {
    checkRequiredFields,
    validateTiersListResponse,
    validateCurrentTierResponse,
    validateResponse
} from '../../../static/js/response-validator.js';

describe('Response Validator', () => {

    describe('checkRequiredFields', () => {
        test('returns valid when all fields are present', () => {
            const data = { a: 1, b: 2 };
            const fields = ['a', 'b'];
            expect(checkRequiredFields(data, fields)).toEqual({ valid: true, missing: [] });
        });

        test('returns missing fields when some are absent', () => {
            const data = { a: 1 };
            const fields = ['a', 'b'];
            expect(checkRequiredFields(data, fields)).toEqual({ valid: false, missing: ['b'] });
        });
    });

    describe('validateTiersListResponse', () => {
        test('validates valid tiers response', () => {
            const data = {
                tiers: [
                    { tier: 'f', name: 'F', price_monthly: 0, price_display: '0', quota_usd: 0, overage_rate: 0, features: [] },
                    { tier: 'p', name: 'P', price_monthly: 1, price_display: '1', quota_usd: 0, overage_rate: 0, features: [] },
                    { tier: 'pr', name: 'Pr', price_monthly: 1, price_display: '1', quota_usd: 0, overage_rate: 0, features: [] },
                    { tier: 'c', name: 'C', price_monthly: 1, price_display: '1', quota_usd: 0, overage_rate: 0, features: [] }
                ]
            };
            expect(validateTiersListResponse(data).valid).toBe(true);
        });

        test('fails when tiers is not an array', () => {
            expect(validateTiersListResponse({ tiers: {} }).valid).toBe(false);
        });
    });

    describe('validateCurrentTierResponse', () => {
        test('fails on missing fields', () => {
            const data = { current_tier: 'pro' };
            const result = validateCurrentTierResponse(data);
            expect(result.valid).toBe(false);
            expect(result.error).toContain('Missing required fields');
        });
    });

    describe('validateResponse dispatcher', () => {
        test('routes to current tier validator correctly', () => {
            const data = { current_tier: 'pro' };
            const result = validateResponse('/api/tiers/current', data);
            // It should fail because data is incomplete, but this confirms it called the right validator
            expect(result.valid).toBe(false);
            expect(result.error).toContain('tier_name');
        });

        test('returns valid for unknown endpoints', () => {
            expect(validateResponse('/api/unknown', {}).valid).toBe(true);
        });
    });
});
