import { CurrencyFormatter } from '../../../static/js/currency.js';

describe('Currency Formatter', () => {
    let formatter;
    const mockRates = {
        USD: 1,
        EUR: 0.9,
        GBP: 0.8
    };

    beforeEach(async () => {
        localStorage.clear();
        global.fetch.mockReset();
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ rates: mockRates })
        });

        formatter = new CurrencyFormatter();
        await formatter.loadRates();
    });

    test('convert USD to EUR', () => {
        const result = formatter.convert(100, 'USD', 'EUR');
        expect(result).toBe(90);
    });

    test('convert EUR to USD', () => {
        const result = formatter.convert(90, 'EUR', 'USD');
        expect(result).toBe(100);
    });

    test('format USD as current currency (USD)', () => {
        formatter.currency = 'USD';
        // Intl.NumberFormat depends on locale, we assume en-US defaults in jsdom
        const formatted = formatter.format(100, 'USD');
        // Match either "$100.00" or just checking contains 100
        expect(formatted).toMatch(/100/);
        expect(formatted).toContain('$');
    });

    test('getSymbol returns correct symbols', () => {
        expect(formatter.getSymbol('USD')).toBe('$');
        expect(formatter.getSymbol('EUR')).toBe('€');
        expect(formatter.getSymbol('NGN')).toBe('₦');
    });

    test('loadRates fallback to hardcoded rates on fetch failure', async () => {
        global.fetch.mockRejectedValueOnce(new Error('Network error'));
        localStorage.removeItem('exchange_rates');

        const newFormatter = new CurrencyFormatter();
        await newFormatter.loadRates();

        expect(newFormatter.rates.USD).toBe(1);
        expect(newFormatter.rates.EUR).toBeDefined();
    });
});
