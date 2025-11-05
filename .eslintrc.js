module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true
  },
  extends: [
    'eslint:recommended'
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  rules: {
    'no-unused-vars': 'error',
    'no-undef': 'error',
    'prefer-const': 'error',
    'no-var': 'error',
    'eqeqeq': 'error',
    'curly': 'error',
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-new-func': 'error',
    'no-script-url': 'error',
    'no-eval': 'error',
    'no-implied-eval': 'error'
  },
  globals: {
    'Chart': 'readonly',
    'fetch': 'readonly',
    'localStorage': 'readonly',
    'console': 'readonly',
    'document': 'readonly',
    'window': 'readonly',
    'setTimeout': 'readonly',
    'setInterval': 'readonly',
    'clearInterval': 'readonly',
    'URL': 'readonly',
    'Blob': 'readonly'
  }
};