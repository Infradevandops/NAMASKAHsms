/**
 * Frontend Performance Optimizer
 */
class PerformanceOptimizer {
    constructor() {
        this.metrics = {
            loadTime: 0,
            renderTime: 0,
            apiCalls: 0,
            errors: 0
        };
        this.init();
    }

    init() {
        this.measurePageLoad();
        this.setupLazyLoading();
        this.optimizeImages();
        this.cacheAPIResponses();
    }

    measurePageLoad() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            this.metrics.loadTime = navigation.loadEventEnd - navigation.loadEventStart;
            
            // Report to monitoring
            this.reportMetrics();
        });
    }

    setupLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }

    optimizeImages() {
        // Convert images to WebP if supported
        if (this.supportsWebP()) {
            document.querySelectorAll('img').forEach(img => {
                if (img.src && !img.src.includes('.webp')) {
                    const webpSrc = img.src.replace(/\.(jpg|jpeg|png)$/, '.webp');
                    img.src = webpSrc;
                }
            });
        }
    }

    supportsWebP() {
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    }

    cacheAPIResponses() {
        const cache = new Map();
        const originalFetch = window.fetch;
        
        window.fetch = async (url, options = {}) => {
            // Only cache GET requests
            if (options.method && options.method !== 'GET') {
                return originalFetch(url, options);
            }

            const cacheKey = url + JSON.stringify(options);
            
            if (cache.has(cacheKey)) {
                const cached = cache.get(cacheKey);
                if (Date.now() - cached.timestamp < 60000) { // 1 minute cache
                    return Promise.resolve(new Response(JSON.stringify(cached.data)));
                }
            }

            const response = await originalFetch(url, options);
            const clonedResponse = response.clone();
            
            if (response.ok) {
                const data = await clonedResponse.json();
                cache.set(cacheKey, {
                    data: data,
                    timestamp: Date.now()
                });
            }

            this.metrics.apiCalls++;
            return response;
        };
    }

    reportMetrics() {
        // Send performance metrics to backend
        fetch('/monitoring/frontend-metrics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...this.metrics,
                userAgent: navigator.userAgent,
                timestamp: Date.now()
            })
        }).catch(() => {}); // Silent fail
    }

    preloadCriticalResources() {
        const criticalResources = [
            '/static/css/style.css',
            '/static/js/enhanced-verification-ui.js'
        ];

        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource;
            link.as = resource.endsWith('.css') ? 'style' : 'script';
            document.head.appendChild(link);
        });
    }
}

// Initialize performance optimizer
const performanceOptimizer = new PerformanceOptimizer();

// Service Worker for caching
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw-enhanced.js')
        .then(registration => console.log('SW registered'))
        .catch(error => console.log('SW registration failed'));
}