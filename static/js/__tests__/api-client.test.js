/**
 * Unit Tests for api-client.js
 */

import { ApiClient, ApiError, api } from '../api-client.js';
import { STORAGE_KEYS, HTTP_STATUS } from '../constants.js';

// Mock fetch
global.fetch = jest.fn();

describe('api-client.js', () => {
    
    beforeEach(() => {
        localStorage.clear();
        fetch.mockClear();
    });

    describe('ApiError', () => {
        it('should create error with message and status', () => {
            const error = new ApiError('Not found', 404);
            expect(error.message).toBe('Not found');
            expect(error.status).toBe(404);
            expect(error.name).toBe('ApiError');
        });

        it('should identify unauthorized errors', () => {
            const error = new ApiError('Unauthorized', 401);
            expect(error.isUnauthorized()).toBe(true);
            
            const otherError = new ApiError('Not found', 404);
            expect(otherError.isUnauthorized()).toBe(false);
        });

        it('should identify timeout errors', () => {
            const error = new ApiError('Timeout', 408);
            expect(error.isTimeout()).toBe(true);
        });

        it('should identify server errors', () => {
            const error500 = new ApiError('Server error', 500);
            expect(error500.isServerError()).toBe(true);

            const error503 = new ApiError('Service unavailable', 503);
            expect(error503.isServerError()).toBe(true);

            const error400 = new ApiError('Bad request', 400);
            expect(error400.isServerError()).toBe(false);
        });
    });

    describe('ApiClient', () => {
        let client;

        beforeEach(() => {
            client = new ApiClient({ baseUrl: '/api' });
            localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'test-token');
        });

        describe('request', () => {
            it('should make GET request with auth headers', async () => {
                fetch.mockResolvedValueOnce({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: () => Promise.resolve({ data: 'test' })
                });

                const result = await client.get('/test');

                expect(fetch).toHaveBeenCalledWith(
                    '/api/test',
                    expect.objectContaining({
                        method: 'GET',
                        headers: expect.objectContaining({
                            'Authorization': 'Bearer test-token'
                        })
                    })
                );
                expect(result).toEqual({ data: 'test' });
            });

            it('should make POST request with body', async () => {
                fetch.mockResolvedValueOnce({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: () => Promise.resolve({ success: true })
                });

                const result = await client.post('/test', { name: 'test' });

                expect(fetch).toHaveBeenCalledWith(
                    '/api/test',
                    expect.objectContaining({
                        method: 'POST',
                        body: JSON.stringify({ name: 'test' })
                    })
                );
                expect(result).toEqual({ success: true });
            });

            it('should throw ApiError on 401', async () => {
                const mockRedirect = jest.fn();
                client.onUnauthorized = mockRedirect;

                fetch.mockResolvedValueOnce({
                    ok: false,
                    status: 401
                });

                await expect(client.get('/test')).rejects.toThrow(ApiError);
                expect(mockRedirect).toHaveBeenCalled();
            });

            it('should throw ApiError on 404', async () => {
                fetch.mockResolvedValueOnce({
                    ok: false,
                    status: 404,
                    json: () => Promise.resolve({ detail: 'Not found' })
                });

                await expect(client.get('/test')).rejects.toThrow(ApiError);
            });

            it('should retry on 500 errors', async () => {
                // First call fails with 500
                fetch.mockResolvedValueOnce({
                    ok: false,
                    status: 500
                });
                // Second call succeeds
                fetch.mockResolvedValueOnce({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: () => Promise.resolve({ data: 'success' })
                });

                const result = await client.get('/test', { maxRetries: 1 });

                expect(fetch).toHaveBeenCalledTimes(2);
                expect(result).toEqual({ data: 'success' });
            });

            it('should throw ApiError when no auth token and requiresAuth is true', async () => {
                localStorage.clear();

                await expect(client.get('/test')).rejects.toThrow('No authentication token');
            });

            it('should allow requests without auth when requiresAuth is false', async () => {
                localStorage.clear();

                fetch.mockResolvedValueOnce({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: () => Promise.resolve({ public: true })
                });

                const result = await client.get('/public', { requiresAuth: false });
                expect(result).toEqual({ public: true });
            });
        });

        describe('convenience methods', () => {
            beforeEach(() => {
                fetch.mockResolvedValue({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: () => Promise.resolve({ success: true })
                });
            });

            it('should have get method', async () => {
                await client.get('/test');
                expect(fetch).toHaveBeenCalledWith(
                    '/api/test',
                    expect.objectContaining({ method: 'GET' })
                );
            });

            it('should have post method', async () => {
                await client.post('/test', { data: 1 });
                expect(fetch).toHaveBeenCalledWith(
                    '/api/test',
                    expect.objectContaining({ method: 'POST' })
                );
            });

            it('should have put method', async () => {
                await client.put('/test', { data: 1 });
                expect(fetch).toHaveBeenCalledWith(
                    '/api/test',
                    expect.objectContaining({ method: 'PUT' })
                );
            });

            it('should have delete method', async () => {
                await client.delete('/test');
                expect(fetch).toHaveBeenCalledWith(
                    '/api/test',
                    expect.objectContaining({ method: 'DELETE' })
                );
            });
        });
    });

    describe('default api instance', () => {
        it('should be an instance of ApiClient', () => {
            expect(api).toBeInstanceOf(ApiClient);
        });
    });
});
