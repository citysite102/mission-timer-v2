import js from '@eslint/js';
import html from 'eslint-plugin-html';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    files: ['**/*.html'],
    plugins: { html },
    languageOptions: { ecmaVersion: 2022, sourceType: 'script', globals: globals.browser },
    rules: {
      'no-empty': ['error', { allowEmptyCatch: true }],   // 專案規定 localStorage 用 try {…} catch {}
      'no-redeclare': ['error', { builtinGlobals: false }], // 頂層的 stop() 和瀏覽器內建的 window.stop 同名，不算錯
    },
  },
];
