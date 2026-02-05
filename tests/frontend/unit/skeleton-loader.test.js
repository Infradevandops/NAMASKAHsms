import { SkeletonLoader } from '../../../static/js/skeleton-loader.js';

describe('SkeletonLoader', () => {
    let container;

    beforeEach(() => {
        container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);
    });

    afterEach(() => {
        document.body.removeChild(container);
    });

    test('createSkeletonText creates element with correct classes', () => {
        const el = SkeletonLoader.createSkeletonText('short');
        expect(el.classList.contains('skeleton')).toBe(true);
        expect(el.classList.contains('skeleton-text')).toBe(true);
        expect(el.classList.contains('short')).toBe(true);
    });

    test('showSkeleton injects skeleton into container', () => {
        SkeletonLoader.showSkeleton(container, 'tier');
        expect(container.querySelector('.skeleton-tier-card')).toBeDefined();

        SkeletonLoader.showSkeleton(container, 'activity', { rows: 3 });
        expect(container.querySelectorAll('.skeleton-activity-row').length).toBe(3);
    });

    test('hideSkeleton replaces content and adds fade-in class', () => {
        jest.useFakeTimers();
        const html = '<div class="content">Done</div>';
        SkeletonLoader.hideSkeleton(container, html);

        expect(container.innerHTML).toBe(html);
        expect(container.classList.contains('fade-in')).toBe(true);

        jest.advanceTimersByTime(300);
        expect(container.classList.contains('fade-in')).toBe(false);
        jest.useRealTimers();
    });

    test('withLoading shows skeleton then replaces with content', async () => {
        const loadFn = jest.fn().mockResolvedValue('success');

        const promise = SkeletonLoader.withLoading(container, loadFn, { skeletonType: 'stats' });

        expect(container.querySelector('.skeleton-stats-grid')).toBeDefined();

        const result = await promise;
        expect(result).toBe('success');
        expect(loadFn).toHaveBeenCalled();
    });

    test('withLoading handles errors', async () => {
        const error = new Error('Load failed');
        const loadFn = jest.fn().mockRejectedValue(error);
        const onError = jest.fn();

        await expect(SkeletonLoader.withLoading(container, loadFn, { onError })).rejects.toThrow('Load failed');

        expect(onError).toHaveBeenCalledWith(error);
    });
});
