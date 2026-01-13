/**
 * Tests for api-retry.js module
 */

// Mock fetch
global.fetch = jest.fn();

// Mock window
global.window = {
    FrontendLogger: {
        info: jest.fn(),
        warn: jest.fn(),
        error: jest.fn()
    }
};

// Mock constants
jest.mock('../constants.js', () => ({
    TIMEOUTS: {
        API_REQUEST: 10000
    },
    HTTP_STATUS: {
        TIMEOUT: 408,
        TOO_MANY_REQUESTS: 429
    }
}));

import {
    DEFAULT_RETRY_CONFIG,
    calculateDelay,
    sleep,
    fetchWithRetry,
    createRetryButton,
    showRetryUI,
    apiCall,
    ApiRetry
} from '../api-retry.js';

describe('api-retry.js', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        fetch.mockClear();
    });

    describe('DEFAULT_RETRY_CONFIG', () => {
        it('should have correct default values', () => {
            expect(DEFAULT_RETRY_CONFIG.maxRetries).toBe(3);
            expect(DEFAULT_RETRY_CONFIG.baseDelay).toBe(1000);
            expect(DEFAULT_RETRY_CONFIG.backoffMultiplier).toBe(2);
        });
    });

    describe('calculateDelay', () => {
        it('should calculate exponential backoff', () => {
            const config = { baseDelay: 1000, backoffMultiplier: 2, maxDelay: 10000 };
            
            expect(calculateDelay(0, config)).toBe(1000);
            expect(calculateDelay(1, config)).toBe(2000);
            expect(calculateDelay(2, config)).toBe(4000);
            expect(calculateDelay(3, config)).toBe(8000);
        });

        it('should cap at maxDelay', () => {
            const config = { baseDelay: 1000, backoffMultiplier: 2, maxDelay: 5000 };
            
            expect(calculateDelay(5, config)).toBe(5000);
        });
    });

    describe('sleep', () => {
        it('should resolve after specified time', async () => {
            jest.useFakeTimers();
            
            const promise = sleep(1000);
            jest.advanceTimersByTime(1000);
            
            await expect(promise).resolves.toBeUndefined();
            
            jest.useRealTimers();
        });
    });

    describe('fetchWithRetry', () => {
        it('should return response on success', async () => {
            const mockResponse = { ok: true, status: 200 };
            fetch.mockResolvedValueOnce(mockResponse);

            const result = await fetchWithRetry('/api/test');
            
            expect(result).toBe(mockResponse);
            expect(fetch).toHaveBeenCalledTimes(1);
        });

        it('should not retry on 4xx errors (except 408, 429)', async () => {
            const mockResponse = { ok: false, status: 400 };
            fetch.mockResolvedValueOnce(mockResponse);

            const result = await fetchWithRetry('/api/test', {}, { maxRetries: 3 });
            
            expect(result).toBe(mockResponse);
            expect(fetch).toHaveBeenCalledTimes(1);
        });

        it('should retry on 5xx errors', async () => {
            jest.useFakeTimers();
            
            const errorResponse = { ok: false, status: 500 };
            const successResponse = { ok: true, status: 200 };
            
            fetch
                .mockResolvedValueOnce(errorResponse)
                .mockResolvedValueOnce(successResponse);

            const promise = fetchWithRetry('/api/test', {}, { maxRetries: 3, baseDelay: 100 });
            
            // Advance timers for retry delay
            await jest.advanceTimersByTimeAsync(100);
            
            const result = await promise;
            
            expect(result).toBe(successResponse);
            expect(fetch).toHaveBeenCalledTimes(2);
            
            jest.useRealTimers();
        });

        it('should throw after max retries', async () => {
            jest.useFakeTimers();
            
            fetch.mockRejectedValue(new Error('Network error'));

            const promise = fetchWithRetry('/api/test', {}, { maxRetries: 2, baseDelay: 100 });
            
            // Advance through all retries
            await jest.advanceTimersByTimeAsync(100);
            await jest.advanceTimersByTimeAsync(200);
            
            await expect(promise).rejects.toThrow('Network error');
            expect(fetch).toHaveBeenCalledTimes(3);
            
            jest.useRealTimers();
        });
    });

    describe('createRetryButton', () => {
        beforeEach(() => {
            document.body.innerHTML = '';
        });

        it('should create a retry button container', () => {
            const callback = jest.fn();
            const container = createRetryButton(callback, 'Test error');
            
            expect(container.className).toBe('retry-container');
            expect(container.querySelector('button')).toBeTruthy();
            expect(container.textContent).toContain('Test error');
        });

        it('should call callback on button click', async () => {
            const callback = jest.fn().mockResolvedValue();
            const container = createRetryButton(callback);
            
            const button = container.querySelector('button');
            button.click();
            
            expect(callback).toHaveBeenCalled();
        });
    });

    describe('showRetryUI', () => {
        beforeEach(() => {
            document.body.innerHTML = '<div id="test-container"></div>';
        });

        it('should show retry UI in container', () => {
            const callback = jest.fn();
            showRetryUI('#test-container', callback, 'Error message');
            
            const container = document.getElementById('test-container');
            expect(container.querySelector('.retry-container')).toBeTruthy();
        });

        it('should handle element reference', () => {
            const callback = jest.fn();
            const element = document.getElementById('test-container');
            showRetryUI(element, callback, 'Error message');
            
            expect(element.querySelector('.retry-container')).toBeTruthy();
        });
    });

    describe('ApiRetry object', () => {
        it('should export all functions', () => {
            expect(ApiRetry.fetchWithRetry).toBe(fetchWithRetry);
            expect(ApiRetry.createRetryButton).toBe(createRetryButton);
            expect(ApiRetry.showRetryUI).toBe(showRetryUI);
            expect(ApiRetry.apiCall).toBe(apiCall);
            expect(ApiRetry.config).toBe(DEFAULT_RETRY_CONFIG);
        });
    });
});
