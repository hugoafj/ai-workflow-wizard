import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    // Only the frontend tests: a PHP project keeps other files named *.test.* (for example a
    // node:test script) that Vitest must not run.
    include: ['{{frontend_root}}/**/*.{test,spec}.{js,jsx,ts,tsx}', 'tests/js/**/*.{test,spec}.{js,jsx,ts,tsx}'],
    exclude: ['**/node_modules/**', '**/e2e/**'],
  },
})
