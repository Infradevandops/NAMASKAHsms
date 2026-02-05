import { ApiClient, ApiError } from '../../../static/js/api-client.js';
import { HTTP_STATUS } from '../../../static/js/constants.js';

// Import the module we want to mock
import * as authHelpers from '../../../static/js/auth-helpers.js';

// Mock the entire module
jest.mock('../../../static/js/auth-helpers.js', () => ({
    __esModule: true,
    getAuthHeaders: jest.fn(() => ({ 'Authorization': 'Bearer test' })),
    hasAuthToken: jest.fn(() => true),
    clearAuth: jest.fn()
}));

describe('ApiClient', () => {
    let client;

    beforeEach(() => {
        global.fetch = jest.fn();
        jest.useFakeTimers();
        client = new ApiClient({
            baseUrl: '/api',
            timeout: 5000,
            maxRetries: 1
        });
        // Ensure hasAuthToken returns true by default for all tests
        authHelpers.hasAuthToken.mockReturnValue(true);
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.resetAllMocks();
    });

    test('request adds correct headers and base URL', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            status: 200,
            headers: new Map([['content-type', 'application/json']]),
            json: () => Promise.resolve({ data: 'ok' })
        });

        const result = await client.get('/test');

        expect(global.fetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
            method: 'GET',
            headers: expect.objectContaining({
                'Content-Type': 'application/json',
                'Authorization': 'Bearer test'
            })
        }));
        expect(result).toEqual({ data: 'ok' });
    });

    test('request throws ApiError on 401 and calls onUnauthorized', async () => {
        const onUnauthorized = jest.fn();
        client = new ApiClient({ onUnauthorized });

        global.fetch.mockResolvedValue({
            status: 401,
            ok: false
        });

        await expect(client.get('/test')).rejects.toThrow('Unauthorized');
        expect(onUnauthorized).toHaveBeenCalled();
    });

    test('request retries on 500 error', async () => {
        global.fetch
            .mockResolvedValueOnce({ status: 500, ok: false })
            .mockResolvedValueOnce({
                status: 200,
                ok: true,
                headers: new Map([['content-type', 'application/json']]),
                json: () => Promise.resolve({ success: true })
            });

        const promise = client.get('/test', { retry: true });

        // Wait for first attempt
        await Promise.resolve();
        jest.advanceTimersByTime(client.retryDelay);

        const result = await promise;
        expect(result.success).toBe(true);
        expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    test('request handles timeout correctly', async () => {
        global.fetch.mockImplementation((url, options) => {
            return new Promise((resolve, reject) => {
                const signal = options.signal;
                if (signal) {
                    signal.addEventListener('abort', () => {
                        const error = new Error('Aborted');
                        error.name = 'AbortError';
                        reject(error);
                    });
                }
            });
        });

        const promise = client.get('/test', { timeout: 100, retry: false });

        // Wait for the fetch call to be established
        await Promise.resolve();

        // Advance timers to trigger abort
        jest.advanceTimersByTime(100);

        await expect(promise).rejects.toThrow('Request timeout');
    });

    test('ApiError class correctly identifies error categories', () => {
        const err401 = new ApiError('Msg', 401);
        expect(err401.isUnauthorized()).toBe(true);

        const err500 = new ApiError('Msg', 500);
        expect(err500.isServerError()).toBe(true);

        const err408 = new ApiError('Msg', 408);
        expect(err408.isTimeout()).toBe(true);
    });
});
