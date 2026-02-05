/**
 * Validation Module
 * Input validation for verification flow
 */

export const validators = {
  /**
   * Validate area code
   * @param {string} value - Area code value
   * @returns {Object} Validation result
   */
  areaCode(value) {
    if (!value) return { valid: false, error: 'Area code required' };
    if (!/^\d{3}$/.test(value)) return { valid: false, error: 'Invalid area code format' };
    return { valid: true };
  },

  /**
   * Validate service
   * @param {string} value - Service value
   * @returns {Object} Validation result
   */
  service(value) {
    if (!value) return { valid: false, error: 'Service required' };
    if (typeof value !== 'string') return { valid: false, error: 'Invalid service' };
    return { valid: true };
  },

  /**
   * Validate carrier
   * @param {string} value - Carrier value
   * @returns {Object} Validation result
   */
  carrier(value) {
    if (!value) return { valid: true }; // Optional
    if (typeof value !== 'string') return { valid: false, error: 'Invalid carrier' };
    return { valid: true };
  }
};

/**
 * Validate verification data
 * @param {Object} data - Verification data
 * @returns {Object} Validation result with errors
 */
export function validateVerification(data) {
  const errors = {};

  const areaCodeValidation = validators.areaCode(data.areaCode);
  if (!areaCodeValidation.valid) errors.areaCode = areaCodeValidation.error;

  const serviceValidation = validators.service(data.service);
  if (!serviceValidation.valid) errors.service = serviceValidation.error;

  const carrierValidation = validators.carrier(data.carrier);
  if (!carrierValidation.valid) errors.carrier = carrierValidation.error;

  return {
    valid: Object.keys(errors).length === 0,
    errors
  };
}
