/**
 * Cache Module
 * Smart caching with TTL
 */

export class Cache {
  constructor(ttl = 3600000) { // 1 hour default
    this.data = new Map();
    this.ttl = ttl;
  }

  /**
   * Set cache value with TTL
   * @param {string} key - Cache key
   * @param {*} value - Cache value
   * @param {number} ttl - Time to live in ms
   * @returns {void}
   */
  set(key, value, ttl = this.ttl) {
    this.data.set(key, {
      value,
      expires: Date.now() + ttl
    });
  }

  /**
   * Get cache value
   * @param {string} key - Cache key
   * @returns {*} Cache value or null
   */
  get(key) {
    const item = this.data.get(key);
    if (!item) return null;

    if (Date.now() > item.expires) {
      this.data.delete(key);
      return null;
    }

    return item.value;
  }

  /**
   * Clear all cache
   * @returns {void}
   */
  clear() {
    this.data.clear();
  }

  /**
   * Check if key exists and not expired
   * @param {string} key - Cache key
   * @returns {boolean} True if valid
   */
  has(key) {
    return this.get(key) !== null;
  }
}

export const cache = new Cache();
