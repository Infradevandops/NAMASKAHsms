/**
 * Error Handling Module
 * Structured error handling with specific messages
 */

export class APIError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = 'APIError';
  }
}

export const errorMessages = {
  400: 'Invalid request. Please check your input.',
  401: 'Session expired. Please login again.',
  402: 'Insufficient balance. Please add credits.',
  404: 'Resource not found.',
  429: 'Too many requests. Please wait a moment.',
  500: 'Server error. Please try again later.',
  503: 'Service unavailable. Please try again later.'
};

/**
 * Handle API errors
 * @param {Error} error - Error object
 * @returns {string} Error message
 */
export function handleError(error) {
  if (error instanceof APIError) {
    return errorMessages[error.status] || 'An error occurred';
  }
  if (error.message) {
    return error.message;
  }
  return 'Unknown error occurred';
}

/**
 * Log error with context
 * @param {string} context - Error context
 * @param {Error} error - Error object
 * @returns {void}
 */
export function logError(context, error) {
  console.error(`[${context}]`, error);
}
