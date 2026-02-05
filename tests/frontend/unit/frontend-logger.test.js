import { FrontendLogger } from '../../../static/js/frontend-logger.js';

describe('FrontendLogger', () => {
    beforeEach(() => {
        // Clear previous logs
        FrontendLogger.clearLogs();
        // Mock console methods
        jest.spyOn(console, 'log').mockImplementation(() => { });
        jest.spyOn(console, 'info').mockImplementation(() => { });
        jest.spyOn(console, 'warn').mockImplementation(() => { });
        jest.spyOn(console, 'error').mockImplementation(() => { });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    test('should log info messages and store them in memory', () => {
        FrontendLogger.info('Test info message', { key: 'value' });

        const logs = FrontendLogger.getLogs();
        expect(logs.length).toBe(2); // 'Logs cleared' + our log
        expect(logs[1].level).toBe('INFO');
        expect(logs[1].message).toBe('Test info message');
        expect(logs[1].data).toEqual({ key: 'value' });
        expect(console.info).toHaveBeenCalled();
    });

    test('should log error messages with stack traces', () => {
        FrontendLogger.error('Test error message', { err: 'failed' });

        const logs = FrontendLogger.getLogs();
        expect(logs.length).toBe(2); // 'Logs cleared' + our log
        expect(logs[1].level).toBe('ERROR');
        expect(logs[1].stack).toBeDefined();
        expect(console.error).toHaveBeenCalled();
    });

    test('should clear logs successfully', () => {
        FrontendLogger.info('Log 1');
        FrontendLogger.info('Log 2');
        expect(FrontendLogger.getLogs().length).toBe(3); // 'Logs cleared' + 2 logs

        FrontendLogger.clearLogs();
        expect(FrontendLogger.getLogs().length).toBe(1); // 'Logs cleared' is also logged
        expect(FrontendLogger.getLogs()[0].message).toBe('Logs cleared');
    });

    test('logApiCall should format message correctly', () => {
        FrontendLogger.logApiCall('POST', '/api/data', { foo: 'bar' });

        const logs = FrontendLogger.getLogs();
        expect(logs[logs.length - 1].message).toBe('API Call: POST /api/data');
    });

    test('logApiResponse should log ERROR for status >= 400', () => {
        FrontendLogger.logApiResponse('GET', '/api/fail', 404);

        const logs = FrontendLogger.getLogs();
        expect(logs[logs.length - 1].level).toBe('ERROR');
    });

    test('logTierLoad should log info on success', () => {
        const tierData = {
            current_tier: 'pro',
            tier_name: 'Professional',
            quota_used_usd: 10,
            quota_usd: 100
        };
        FrontendLogger.logTierLoad(true, tierData);

        const logs = FrontendLogger.getLogs();
        expect(logs[logs.length - 1].level).toBe('INFO');
        expect(logs[logs.length - 1].message).toBe('Tier info loaded successfully');
    });
});
