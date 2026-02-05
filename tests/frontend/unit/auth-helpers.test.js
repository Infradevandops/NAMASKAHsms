import {
    getAuthToken,
    hasAuthToken,
    setAuthTokens,
    clearAuth,
    isTokenExpired
} from '../../../static/js/auth-helpers.js';
import { STORAGE_KEYS } from '../../../static/js/constants.js';

describe('Auth Helpers', () => {
    beforeEach(() => {
        localStorage.clear();
        jest.clearAllMocks();
    });

    test('getAuthToken returns token from localStorage', () => {
        localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'test-token');
        expect(getAuthToken()).toBe('test-token');
    });

    test('hasAuthToken returns true when token is present', () => {
        localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'test-token');
        expect(hasAuthToken()).toBe(true);
    });

    test('hasAuthToken returns false when token is missing', () => {
        expect(hasAuthToken()).toBe(false);
    });

    test('setAuthTokens saves tokens to localStorage', () => {
        setAuthTokens('access', 'refresh');
        expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBe('access');
        expect(localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)).toBe('refresh');
    });

    test('setAuthTokens saves expiry if provided', () => {
        const expiresIn = 3600;
        const now = Date.now();
        jest.spyOn(Date, 'now').mockReturnValue(now);

        setAuthTokens('access', 'refresh', expiresIn);

        const expectedExpiry = (now + (expiresIn * 1000)).toString();
        expect(localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRES)).toBe(expectedExpiry);
    });

    test('clearAuth removes all tokens', () => {
        localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'a');
        localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, 'r');
        localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES, 'e');

        clearAuth();

        expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBeNull();
        expect(localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)).toBeNull();
        expect(localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRES)).toBeNull();
    });

    test('isTokenExpired returns true if past expiry', () => {
        localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES, (Date.now() - 1000).toString());
        expect(isTokenExpired()).toBe(true);
    });

    test('isTokenExpired returns false if before expiry', () => {
        localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES, (Date.now() + 1000).toString());
        expect(isTokenExpired()).toBe(false);
    });
});
