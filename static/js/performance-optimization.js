/**
 * Frontend Performance Optimization
 * 
 * Implements:
 * - Lazy loading
 * - Code splitting
 * - Resource hints
 * - Image optimization
 * - Bundle optimization
 */

/**
 * Lazy load modules on demand
 */
const LazyLoader = {
  modules: {},
  
  /**
   * Load module lazily
   * @param {string} moduleName - Module name
   * @param {function} loader - Module loader function
   * @returns {Promise} Module promise
   */
  async load(moduleName, loader) {
    if (this.modules[moduleName]) {
      return this.modules[moduleName];
    }
    
    try {
      const module = await loader();
      this.modules[moduleName] = module;
      console.log(`Lazy loaded: ${moduleName}`);
      return module;
    } catch (error) {
      console.error(`Failed to lazy load ${moduleName}:`, error);
      throw error;
    }
  },
  
  /**
   * Preload module
   * @param {string} moduleName - Module name
   * @param {function} loader - Module loader function
   */
  preload(moduleName, loader) {
    // Preload in background
    setTimeout(() => {
      this.load(moduleName, loader).catch(err => {
        console.warn(`Preload failed for ${moduleName}:`, err);
      });
    }, 1000);
  }
};

/**
 * Code splitting strategy
 */
const CodeSplitter = {
  chunks: {
    tier: null,
    dashboard: null,
    analytics: null,
    settings: null,
  },
  
  /**
   * Load chunk
   * @param {string} chunkName - Chunk name
   * @returns {Promise} Chunk promise
   */
  async loadChunk(chunkName) {
    if (this.chunks[chunkName]) {
      return this.chunks[chunkName];
    }
    
    try {
      const chunk = await import(`./chunks/${chunkName}.js`);
      this.chunks[chunkName] = chunk;
      console.log(`Code chunk loaded: ${chunkName}`);
      return chunk;
    } catch (error) {
      console.error(`Failed to load chunk ${chunkName}:`, error);
      throw error;
    }
  },
  
  /**
   * Preload chunks
   * @param {string[]} chunkNames - Chunk names to preload
   */
  preloadChunks(chunkNames) {
    chunkNames.forEach(name => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = `/static/chunks/${name}.js`;
      document.head.appendChild(link);
    });
  }
};

/**
 * Resource hints for performance
 */
const ResourceHints = {
  /**
   * Add DNS prefetch
   * @param {string} domain - Domain to prefetch
   */
  dnsPrefetch(domain) {
    const link = document.createElement('link');
    link.rel = 'dns-prefetch';
    link.href = `//${domain}`;
    document.head.appendChild(link);
  },
  
  /**
   * Add preconnect
   * @param {string} url - URL to preconnect
   */
  preconnect(url) {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = url;
    document.head.appendChild(link);
  },
  
  /**
   * Add prefetch
   * @param {string} url - URL to prefetch
   */
  prefetch(url) {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    document.head.appendChild(link);
  },
  
  /**
   * Add preload
   * @param {string} url - URL to preload
   * @param {string} as - Resource type
   */
  preload(url, as = 'script') {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = url;
    link.as = as;
    document.head.appendChild(link);
  }
};

/**
 * Image optimization
 */
const ImageOptimizer = {
  /**
   * Lazy load image
   * @param {HTMLImageElement} img - Image element
   */
  lazyLoad(img) {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const image = entry.target;
            image.src = image.dataset.src;
            image.classList.add('loaded');
            observer.unobserve(image);
          }
        });
      });
      
      observer.observe(img);
    } else {
      // Fallback for older browsers
      img.src = img.dataset.src;
    }
  },
  
  /**
   * Lazy load all images
   */
  lazyLoadAll() {
    const images = document.querySelectorAll('img[data-src]');
    images.forEach(img => this.lazyLoad(img));
  },
  
  /**
   * Optimize image size
   * @param {string} url - Image URL
   * @param {number} width - Target width
   * @param {number} height - Target height
   * @returns {string} Optimized URL
   */
  optimizeSize(url, width, height) {
    // Add image optimization parameters
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}w=${width}&h=${height}&q=80`;
  }
};

/**
 * Bundle optimization
 */
const BundleOptimizer = {
  /**
   * Analyze bundle size
   * @returns {Promise} Bundle analysis
   */
  async analyzeBundleSize() {
    try {
      const response = await fetch('/api/metrics/bundle-size');
      const data = await response.json();
      console.log('Bundle size analysis:', data);
      return data;
    } catch (error) {
      console.error('Bundle analysis failed:', error);
      return null;
    }
  },
  
  /**
   * Get bundle metrics
   * @returns {Promise} Bundle metrics
   */
  async getBundleMetrics() {
    try {
      const response = await fetch('/api/metrics/bundle');
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to get bundle metrics:', error);
      return null;
    }
  }
};

/**
 * Performance monitoring
 */
const PerformanceMonitor = {
  /**
   * Measure operation
   * @param {string} name - Operation name
   * @param {function} fn - Operation function
   * @returns {Promise} Operation result
   */
  async measure(name, fn) {
    const start = performance.now();
    try {
      const result = await fn();
      const duration = performance.now() - start;
      console.log(`${name}: ${duration.toFixed(2)}ms`);
      return result;
    } catch (error) {
      const duration = performance.now() - start;
      console.error(`${name} failed after ${duration.toFixed(2)}ms:`, error);
      throw error;
    }
  },
  
  /**
   * Get performance metrics
   * @returns {object} Performance metrics
   */
  getMetrics() {
    const navigation = performance.getEntriesByType('navigation')[0];
    const paint = performance.getEntriesByType('paint');
    
    return {
      dns: navigation.domainLookupEnd - navigation.domainLookupStart,
      tcp: navigation.connectEnd - navigation.connectStart,
      ttfb: navigation.responseStart - navigation.requestStart,
      download: navigation.responseEnd - navigation.responseStart,
      domInteractive: navigation.domInteractive - navigation.fetchStart,
      domComplete: navigation.domComplete - navigation.fetchStart,
      loadComplete: navigation.loadEventEnd - navigation.fetchStart,
      paint: paint.map(p => ({
        name: p.name,
        time: p.startTime
      }))
    };
  },
  
  /**
   * Report performance metrics
   */
  reportMetrics() {
    const metrics = this.getMetrics();
    console.log('Performance Metrics:', metrics);
    
    // Send to monitoring service
    fetch('/api/metrics/performance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(metrics)
    }).catch(err => console.error('Failed to report metrics:', err));
  }
};

/**
 * Initialize performance optimizations
 */
function initializePerformanceOptimizations() {
  // Add resource hints
  ResourceHints.dnsPrefetch('api.example.com');
  ResourceHints.preconnect('https://cdn.example.com');
  
  // Preload critical chunks
  CodeSplitter.preloadChunks(['tier', 'dashboard']);
  
  // Lazy load images
  ImageOptimizer.lazyLoadAll();
  
  // Report performance metrics
  if (document.readyState === 'complete') {
    PerformanceMonitor.reportMetrics();
  } else {
    window.addEventListener('load', () => {
      PerformanceMonitor.reportMetrics();
    });
  }
  
  console.log('Performance optimizations initialized');
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    LazyLoader,
    CodeSplitter,
    ResourceHints,
    ImageOptimizer,
    BundleOptimizer,
    PerformanceMonitor,
    initializePerformanceOptimizations
  };
}

// Initialize on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePerformanceOptimizations);
} else {
  initializePerformanceOptimizations();
}
