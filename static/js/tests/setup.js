/**
 * Jest setup file for DOM testing
 */

// Mock window and document globals
global.window = {
  location: {
    href: 'http://localhost:3000',
    protocol: 'http:',
    host: 'localhost:3000'
  },
  addEventListener: jest.fn(),
  removeEventListener: jest.fn()
};

global.document = {
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  getElementById: jest.fn(),
  querySelectorAll: jest.fn(() => []),
  createElement: jest.fn(),
  body: {
    appendChild: jest.fn(),
    removeChild: jest.fn()
  }
};

// Mock URL and Blob for file downloads
global.URL = {
  createObjectURL: jest.fn(() => 'mock-url'),
  revokeObjectURL: jest.fn()
};

global.Blob = jest.fn();

// Mock console methods to reduce test noise
global.console = {
  ...console,
  error: jest.fn(),
  warn: jest.fn(),
  log: jest.fn()
};