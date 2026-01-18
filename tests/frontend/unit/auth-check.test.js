import { refreshToken, checkAuthentication } from '../../../static/js/auth-check.js';

describe('AuthCheck', () => {
    beforeEach(() => {
        localStorage.clear();
        global.fetch = jest.fn();
        // Mock window.location
        delete window.location;
        window.location = { href: '', pathname: '/dashboard' };
        jest.spyOn(console, 'log').mockImplementation(() => { });
        jest.spyOn(console, 'error').mockImplementation(() => { });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    describe('refreshToken', () => {
        test('returns false if no refresh token in localStorage', async () => {
            const result = await refreshToken();
            expect(result).toBe(false);
            expect(global.fetch).not.toHaveBeenCalled();
        });

        test('prevents multiple simultaneous refresh requests (race condition)', async () => {
            localStorage.setItem('refresh_token', 'test_refresh');

            global.fetch.mockImplementation(() => new Promise(resolve => {
                setTimeout(() => resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        access_token: 'new_access',
                        expires_in: 3600
                    })
                }), 50);
            }));

            // Call it twice
            const p1 = refreshToken();
            const p2 = refreshToken();

            const [r1, r2] = await Promise.all([p1, p2]);

            expect(r1).toBe(true);
            expect(r2).toBe(true);
            expect(global.fetch).toHaveBeenCalledTimes(1); // Only one fetch!
        });
    });

    describe('checkAuthentication', () => {
        test('redirects to login if no access token found', async () => {
            await checkAuthentication();
            expect(window.location.href).toBe('/auth/login');
        });

        test('does not redirect if already on auth page', async () => {
            window.location.pathname = '/auth/login';
            await checkAuthentication();
            expect(window.location.href).toBe(''); // No change
        });

        test('returns true if token is valid and server responds 200', async () => {
            localStorage.setItem('access_token', 'valid_token');
            global.fetch.mockResolvedValue({ ok: true, status: 200 });

            const result = await checkAuthentication();
            expect(result).toBe(true);
            expect(global.fetch).toHaveBeenCalledWith('/api/user/me', expect.any(Object));
        });

        test('attempts refresh if server responds 401', async () => {
            localStorage.setItem('access_token', 'invalid_token');
            localStorage.setItem('refresh_token', 'valid_refresh');

            // First call fails, refresh succeeds
            global.fetch
                .mockResolvedValueOnce({ ok: false, status: 401 })
                .mockResolvedValueOnce({
                    ok: true,
                    json: () => Promise.resolve({ access_token: 'new_token', expires_in: 3600 })
                });

            const result = await checkAuthentication();
            expect(result).toBe(true);
            expect(localStorage.getItem('access_token')).toBe('new_token');
        });
    });
});
