/**
 * @module eslint.config
 * Strict lint rules for browser code and its tests.
 */
import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    files: ['static/**/*.js'],
    languageOptions: { ecmaVersion: 2023, sourceType: 'module', globals: { ...globals.browser } },
  },
  {
    files: ['static/sw.js'],
    languageOptions: { sourceType: 'script', globals: { ...globals.serviceworker } },
  },
  {
    files: ['tests/js/**/*.mjs'],
    languageOptions: { ecmaVersion: 2023, sourceType: 'module', globals: { ...globals.node } },
  },
  {
    rules: {
      'no-console': 'error',
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      'no-var': 'error',
      'prefer-const': 'error',
      eqeqeq: ['error', 'always'],
      curly: ['error', 'all'],
      'no-magic-numbers': ['error', { ignore: [-1, 0, 1, 2], ignoreArrayIndexes: true, ignoreDefaultValues: true }],
      'max-lines': ['error', { max: 200 }],
      'max-lines-per-function': ['error', { max: 30, skipComments: true, skipBlankLines: true }],
      'no-restricted-properties': [
        'error',
        { property: 'innerHTML', message: 'Use textContent or dom.h() instead.' },
        { property: 'outerHTML', message: 'Use textContent or dom.h() instead.' },
        { property: 'insertAdjacentHTML', message: 'Use dom.h() instead.' },
      ],
    },
  },
  {
    files: ['tests/js/**/*.mjs'],
    rules: { 'no-magic-numbers': 'off', 'max-lines-per-function': 'off' },
  },
];
