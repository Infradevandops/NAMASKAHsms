import { ErrorMessages } from '../../../static/js/error-messages.js';

describe('ErrorMessages', () => {
    describe('getErrorType', () => {
        test('identifies auth errors by status code', () => {
            expect(ErrorMessages.getErrorType(401)).toBe('auth');
            expect(ErrorMessages.getErrorType(403)).toBe('auth');
        });

        test('identifies network errors by message', () => {
            const error = new Error('Failed to fetch data');
            expect(ErrorMessages.getErrorType(error)).toBe('network');
        });

        test('identifies tier errors by status code', () => {
            expect(ErrorMessages.getErrorType(402)).toBe('tier_required');
        });

        test('identifies server errors by status code', () => {
            expect(ErrorMessages.getErrorType(500)).toBe('server');
            expect(ErrorMessages.getErrorType(503)).toBe('server');
        });
    });

    describe('getErrorInfo', () => {
        test('returns correct title and icon for network error', () => {
            const info = ErrorMessages.getErrorInfo(new Error('Network problem'));
            expect(info.title).toBe('Connection Problem');
            expect(info.icon).toBe('🌐');
        });

        test('applies custom message', () => {
            const info = ErrorMessages.getErrorInfo(500, 'Custom server message');
            expect(info.message).toBe('Custom server message');
        });
    });

    describe('UI components', () => {
        let container;

        beforeEach(() => {
            container = document.createElement('div');
            document.body.appendChild(container);
        });

        afterEach(() => {
            document.body.removeChild(container);
        });

        test('createErrorDisplay returns element with content', () => {
            const el = ErrorMessages.createErrorDisplay(404);
            expect(el.innerHTML).toContain('Not Found');
            expect(el.innerHTML).toContain('🔍');
        });

        test('showError injects display into container', () => {
            ErrorMessages.showError(container, 500);
            expect(container.querySelector('.error-display')).toBeDefined();
        });

        test('retry button calls callback', () => {
            const retryCallback = jest.fn();
            const el = ErrorMessages.createErrorDisplay(500, { retryCallback });
            const btn = el.querySelector('.btn-primary');

            btn.click();
            expect(retryCallback).toHaveBeenCalled();
        });
    });
});
