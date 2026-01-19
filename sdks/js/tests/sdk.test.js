const NamaskahClient = require('../src/index');
const axios = require('axios');

jest.mock('axios');

describe('NamaskahClient', () => {
    let client;
    let mockAxiosInstance;

    beforeEach(() => {
        mockAxiosInstance = {
            post: jest.fn(),
            get: jest.fn(),
            create: jest.fn()
        };
        // axios.create returns the mock instance
        axios.create.mockReturnValue(mockAxiosInstance);

        client = new NamaskahClient('test-api-key');
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('initializes with correct config', () => {
        expect(axios.create).toHaveBeenCalledWith({
            baseURL: 'https://api.namaskah.com/api',
            headers: {
                'Authorization': 'Bearer test-api-key',
                'Content-Type': 'application/json',
                'User-Agent': 'Namaskah-Node-SDK/1.0.0'
            }
        });
    });

    test('throws error without api key', () => {
        expect(() => new NamaskahClient()).toThrow('API Key is required');
    });

    describe('Verifications', () => {
        test('create calls correct endpoint', async () => {
            const data = { service: 'whatsapp', country: 'US' };
            const mockResponse = { data: { id: 'v1', ...data } };
            mockAxiosInstance.post.mockResolvedValue(mockResponse);

            const result = await client.verifications.create(data);

            expect(mockAxiosInstance.post).toHaveBeenCalledWith('/verify', data);
            expect(result).toEqual(mockResponse.data);
        });

        test('get calls correct endpoint', async () => {
            const mockResponse = { data: { id: 'v1', status: 'pending' } };
            mockAxiosInstance.get.mockResolvedValue(mockResponse);

            const result = await client.verifications.get('v1');

            expect(mockAxiosInstance.get).toHaveBeenCalledWith('/verify/v1');
            expect(result).toEqual(mockResponse.data);
        });

        test('cancel calls correct endpoint', async () => {
            const mockResponse = { data: { success: true } };
            mockAxiosInstance.post.mockResolvedValue(mockResponse);

            const result = await client.verifications.cancel('v1');

            expect(mockAxiosInstance.post).toHaveBeenCalledWith('/verify/v1/cancel');
            expect(result).toEqual(mockResponse.data);
        });
    });

    describe('Users', () => {
        test('getProfile calls correct endpoint', async () => {
            const mockResponse = { data: { id: 'u1', email: 'test@test.com' } };
            mockAxiosInstance.get.mockResolvedValue(mockResponse);

            const result = await client.users.getProfile();

            expect(mockAxiosInstance.get).toHaveBeenCalledWith('/user/profile');
            expect(result).toEqual(mockResponse.data);
        });

        test('getBalance calls correct endpoint', async () => {
            const mockResponse = { data: { balance: 10.0 } };
            mockAxiosInstance.get.mockResolvedValue(mockResponse);

            const result = await client.users.getBalance();

            expect(mockAxiosInstance.get).toHaveBeenCalledWith('/billing/balance');
            expect(result).toEqual(mockResponse.data);
        });
    });

    describe('Referrals', () => {
        test('getStats calls correct endpoint', async () => {
            const mockResponse = { data: { total: 5 } };
            mockAxiosInstance.get.mockResolvedValue(mockResponse);

            const result = await client.referrals.getStats();

            expect(mockAxiosInstance.get).toHaveBeenCalledWith('/referrals/stats');
            expect(result).toEqual(mockResponse.data);
        });

        test('list calls correct endpoint', async () => {
            const mockResponse = { data: [] };
            mockAxiosInstance.get.mockResolvedValue(mockResponse);

            const result = await client.referrals.list();

            expect(mockAxiosInstance.get).toHaveBeenCalledWith('/referrals/list');
            expect(result).toEqual(mockResponse.data);
        });
    });
});
