/**
 * Skeleton Loader Utility
 * 
 * Provides functions to create and manage skeleton loading states
 */

(function(window) {
    'use strict';

    /**
     * Create a skeleton text element
     * @param {string} size - 'short', 'medium', or 'long'
     * @returns {HTMLElement}
     */
    function createSkeletonText(size = 'medium') {
        const el = document.createElement('div');
        el.className = `skeleton skeleton-text ${size}`;
        return el;
    }

    /**
     * Create a skeleton title element
     * @returns {HTMLElement}
     */
    function createSkeletonTitle() {
        const el = document.createElement('div');
        el.className = 'skeleton skeleton-title';
        return el;
    }

    /**
     * Create a skeleton stat element
     * @returns {HTMLElement}
     */
    function createSkeletonStat() {
        const el = document.createElement('div');
        el.className = 'skeleton skeleton-stat';
        return el;
    }

    /**
     * Create a tier card skeleton
     * @returns {HTMLElement}
     */
    function createTierCardSkeleton() {
        const container = document.createElement('div');
        container.className = 'skeleton-tier-card';
        container.innerHTML = `
            <div class="skeleton skeleton-tier-name"></div>
            <div class="skeleton skeleton-tier-price"></div>
            <div class="skeleton-tier-features">
                <div class="skeleton skeleton-text short"></div>
                <div class="skeleton skeleton-text medium"></div>
                <div class="skeleton skeleton-text short"></div>
            </div>
        `;
        return container;
    }

    /**
     * Create an activity table skeleton
     * @param {number} rows - Number of skeleton rows
     * @returns {HTMLElement}
     */
    function createActivityTableSkeleton(rows = 5) {
        const container = document.createElement('div');
        container.className = 'skeleton-activity-table';
        
        for (let i = 0; i < rows; i++) {
            const row = document.createElement('div');
            row.className = 'skeleton-activity-row';
            row.innerHTML = `
                <div class="skeleton skeleton-cell"></div>
                <div class="skeleton skeleton-cell"></div>
                <div class="skeleton skeleton-cell"></div>
                <div class="skeleton skeleton-cell"></div>
            `;
            container.appendChild(row);
        }
        
        return container;
    }

    /**
     * Create a stats grid skeleton
     * @param {number} count - Number of stat cards
     * @returns {HTMLElement}
     */
    function createStatsGridSkeleton(count = 4) {
        const container = document.createElement('div');
        container.className = 'skeleton-stats-grid';
        
        for (let i = 0; i < count; i++) {
            const card = document.createElement('div');
            card.className = 'skeleton-stat-card';
            card.innerHTML = `
                <div class="skeleton skeleton-stat-label"></div>
                <div class="skeleton skeleton-stat-value"></div>
            `;
            container.appendChild(card);
        }
        
        return container;
    }

    /**
     * Create a loading container with spinner
     * @param {string} message - Loading message
     * @returns {HTMLElement}
     */
    function createLoadingContainer(message = 'Loading...') {
        const container = document.createElement('div');
        container.className = 'loading-container';
        container.innerHTML = `
            <div class="loading-spinner large"></div>
            <div class="loading-text">${escapeHtml(message)}</div>
        `;
        return container;
    }

    /**
     * Show skeleton in a container
     * @param {HTMLElement|string} container - Container element or selector
     * @param {string} type - Type of skeleton ('tier', 'activity', 'stats', 'loading')
     * @param {object} options - Additional options
     */
    function showSkeleton(container, type = 'loading', options = {}) {
        const el = typeof container === 'string' ? document.querySelector(container) : container;
        if (!el) return;

        let skeleton;
        switch (type) {
            case 'tier':
                skeleton = createTierCardSkeleton();
                break;
            case 'activity':
                skeleton = createActivityTableSkeleton(options.rows || 5);
                break;
            case 'stats':
                skeleton = createStatsGridSkeleton(options.count || 4);
                break;
            case 'loading':
            default:
                skeleton = createLoadingContainer(options.message || 'Loading...');
                break;
        }

        el.innerHTML = '';
        el.appendChild(skeleton);
    }

    /**
     * Hide skeleton and show content with animation
     * @param {HTMLElement|string} container - Container element or selector
     * @param {string} html - HTML content to show
     */
    function hideSkeleton(container, html) {
        const el = typeof container === 'string' ? document.querySelector(container) : container;
        if (!el) return;

        el.innerHTML = html;
        el.classList.add('fade-in');
        
        // Remove animation class after it completes
        setTimeout(() => {
            el.classList.remove('fade-in');
        }, 300);
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Add fade-in animation to an element
     * @param {HTMLElement|string} element - Element or selector
     */
    function fadeIn(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;
        
        el.classList.add('fade-in');
        setTimeout(() => {
            el.classList.remove('fade-in');
        }, 300);
    }

    /**
     * Transition between loading and content states
     * @param {HTMLElement|string} container - Container element or selector
     * @param {function} loadFn - Async function that returns content
     * @param {object} options - Options for skeleton type and messages
     */
    async function withLoading(container, loadFn, options = {}) {
        const el = typeof container === 'string' ? document.querySelector(container) : container;
        if (!el) return;

        const {
            skeletonType = 'loading',
            loadingMessage = 'Loading...',
            errorMessage = 'Failed to load',
            onError
        } = options;

        // Show skeleton
        showSkeleton(el, skeletonType, { message: loadingMessage, ...options });

        try {
            const result = await loadFn();
            return result;
        } catch (error) {
            if (onError) {
                onError(error);
            } else {
                el.innerHTML = `<div class="loading-container"><div style="color: var(--text-muted);">⚠️ ${escapeHtml(errorMessage)}</div></div>`;
            }
            throw error;
        }
    }

    // Public API
    window.SkeletonLoader = {
        createSkeletonText,
        createSkeletonTitle,
        createSkeletonStat,
        createTierCardSkeleton,
        createActivityTableSkeleton,
        createStatsGridSkeleton,
        createLoadingContainer,
        showSkeleton,
        hideSkeleton,
        fadeIn,
        withLoading
    };

})(window);
