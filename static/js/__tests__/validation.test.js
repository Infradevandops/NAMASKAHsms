/**
 * Validation Module Tests
 */

import { validators, validateVerification } from '../modules/validation.js';

describe('Validators', () => {
  describe('areaCode', () => {
    test('should accept valid area code', () => {
      const result = validators.areaCode('201');
      expect(result.valid).toBe(true);
    });

    test('should reject invalid area code (2 digits)', () => {
      const result = validators.areaCode('20');
      expect(result.valid).toBe(false);
    });

    test('should reject empty area code', () => {
      const result = validators.areaCode('');
      expect(result.valid).toBe(false);
    });

    test('should reject non-numeric area code', () => {
      const result = validators.areaCode('abc');
      expect(result.valid).toBe(false);
    });
  });

  describe('service', () => {
    test('should accept valid service', () => {
      const result = validators.service('Tinder');
      expect(result.valid).toBe(true);
    });

    test('should reject empty service', () => {
      const result = validators.service('');
      expect(result.valid).toBe(false);
    });

    test('should reject non-string service', () => {
      const result = validators.service(123);
      expect(result.valid).toBe(false);
    });
  });

  describe('carrier', () => {
    test('should accept valid carrier', () => {
      const result = validators.carrier('Verizon');
      expect(result.valid).toBe(true);
    });

    test('should accept empty carrier (optional)', () => {
      const result = validators.carrier('');
      expect(result.valid).toBe(true);
    });

    test('should reject non-string carrier', () => {
      const result = validators.carrier(123);
      expect(result.valid).toBe(false);
    });
  });
});

describe('validateVerification', () => {
  test('should validate complete data', () => {
    const result = validateVerification({
      areaCode: '201',
      service: 'Tinder',
      carrier: 'Verizon'
    });
    expect(result.valid).toBe(true);
    expect(Object.keys(result.errors).length).toBe(0);
  });

  test('should validate without carrier', () => {
    const result = validateVerification({
      areaCode: '201',
      service: 'Tinder',
      carrier: ''
    });
    expect(result.valid).toBe(true);
  });

  test('should reject missing area code', () => {
    const result = validateVerification({
      areaCode: '',
      service: 'Tinder',
      carrier: 'Verizon'
    });
    expect(result.valid).toBe(false);
    expect(result.errors.areaCode).toBeDefined();
  });

  test('should reject missing service', () => {
    const result = validateVerification({
      areaCode: '201',
      service: '',
      carrier: 'Verizon'
    });
    expect(result.valid).toBe(false);
    expect(result.errors.service).toBeDefined();
  });
});
