import { fetchWithRetry, calculateDelay } from '../../../static/js/api-retry.js';
import { HTTP_STATUS } from '../../../static/js/constants.js';

describe('ApiRetry Utility', () => {
    beforeEach(() => {
        global.fetch = jest.fn();
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.resetAllMocks();
    });

    const flushPromises = () => new Promise(resolve => Promise.resolve().then(resolve));

    test('calculateDelay returns correct values with exponential backoff', () => {
        const config = { baseDelay: 1000, backoffMultiplier: 2, maxDelay: 10000 };
        expect(calculateDelay(0, config)).toBe(1000);
        expect(calculateDelay(1, config)).toBe(2000);
        expect(calculateDelay(2, config)).toBe(4000);
        expect(calculateDelay(3, config)).toBe(8000);
        expect(calculateDelay(4, config)).toBe(10000);
    });

    test('fetchWithRetry succeeds on first attempt', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ data: 'success' })
        });

        const response = await fetchWithRetry('/api/test');
        expect(response.status).toBe(200);
        expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    test('fetchWithRetry retries on 500 server error', async () => {
        global.fetch
            .mockResolvedValueOnce({ status: 500, ok: false })
            .mockResolvedValueOnce({ status: 200, ok: true });

        const fetchPromise = fetchWithRetry('/api/test', {}, { baseDelay: 100 });

        await flushPromises(); // Initial fetch
        jest.advanceTimersByTime(100); // Sleep
        await flushPromises(); // Next fetch

        const response = await fetchPromise;
        expect(response.status).toBe(200);
        expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    test('fetchWithRetry retries on network error', async () => {
        global.fetch
            .mockRejectedValueOnce(new Error('Network failure'))
            .mockResolvedValueOnce({ status: 200, ok: true });

        const fetchPromise = fetchWithRetry('/api/test', {}, { baseDelay: 100 });

        await flushPromises();
        jest.advanceTimersByTime(100);
        await flushPromises();

        const response = await fetchPromise;
        expect(response.status).toBe(200);
        expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    test('fetchWithRetry fails after max retries', async () => {
        global.fetch.mockResolvedValue({ status: 500, ok: false });

        const maxRetries = 2;
        const fetchPromise = fetchWithRetry('/api/test', {}, { maxRetries, baseDelay: 100 });

        // Initial fetch (attempt 0)
        await flushPromises();

        // Attempt 1: sleep(100) -> fetch
        jest.advanceTimersByTime(100);
        await flushPromises();

        // Attempt 2: sleep(200) -> fetch
        jest.advanceTimersByTime(200);
        await flushPromises();

        await expect(fetchPromise).rejects.toThrow('HTTP 500');
        expect(global.fetch).toHaveBeenCalledTimes(3);
    });

    test('fetchWithRetry does not retry on 401 Unauthorized', async () => {
        global.fetch.mockResolvedValue({ status: 401, ok: false });

        const response = await fetchWithRetry('/api/test');
        expect(response.status).toBe(401);
        expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    test('fetchWithRetry retries on 408 Timeout', async () => {
        global.fetch
            .mockResolvedValueOnce({ status: HTTP_STATUS.TIMEOUT, ok: false })
            .mockResolvedValueOnce({ status: 200, ok: true });

        const fetchPromise = fetchWithRetry('/api/test', {}, { baseDelay: 100 });

        await flushPromises();
        jest.advanceTimersByTime(100);
        await flushPromises();

        const response = await fetchPromise;
        expect(response.status).toBe(200);
        expect(global.fetch).toHaveBeenCalledTimes(2);
    });
});
