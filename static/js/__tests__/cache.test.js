/**
 * Cache Module Tests
 */

import { Cache } from '../utils/cache.js';

describe('Cache', () => {
  let cache;

  beforeEach(() => {
    cache = new Cache(1000); // 1 second TTL for testing
  });

  describe('set and get', () => {
    test('should set and get value', () => {
      cache.set('key1', 'value1');
      expect(cache.get('key1')).toBe('value1');
    });

    test('should return null for non-existent key', () => {
      expect(cache.get('nonexistent')).toBeNull();
    });

    test('should handle different data types', () => {
      cache.set('obj', { name: 'test' });
      expect(cache.get('obj')).toEqual({ name: 'test' });

      cache.set('arr', [1, 2, 3]);
      expect(cache.get('arr')).toEqual([1, 2, 3]);
    });
  });

  describe('TTL expiry', () => {
    test('should expire value after TTL', (done) => {
      cache.set('key1', 'value1', 100); // 100ms TTL
      expect(cache.get('key1')).toBe('value1');

      setTimeout(() => {
        expect(cache.get('key1')).toBeNull();
        done();
      }, 150);
    });

    test('should use default TTL', (done) => {
      cache.set('key1', 'value1'); // Uses default 1000ms
      expect(cache.get('key1')).toBe('value1');

      setTimeout(() => {
        expect(cache.get('key1')).toBeNull();
        done();
      }, 1100);
    });
  });

  describe('clear', () => {
    test('should clear all cache', () => {
      cache.set('key1', 'value1');
      cache.set('key2', 'value2');
      cache.clear();
      expect(cache.get('key1')).toBeNull();
      expect(cache.get('key2')).toBeNull();
    });
  });

  describe('has', () => {
    test('should check if key exists', () => {
      cache.set('key1', 'value1');
      expect(cache.has('key1')).toBe(true);
      expect(cache.has('nonexistent')).toBe(false);
    });

    test('should return false for expired key', (done) => {
      cache.set('key1', 'value1', 100);
      expect(cache.has('key1')).toBe(true);

      setTimeout(() => {
        expect(cache.has('key1')).toBe(false);
        done();
      }, 150);
    });
  });
});
