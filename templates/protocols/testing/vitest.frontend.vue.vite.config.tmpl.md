import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './{{vite_config_file}}'

// Vitest ignores vite.config.* when a vitest.config.* exists, so the Vite config of the app is merged
// in here: its aliases (for example the "@" alias that laravel-vite-plugin sets) and its plugins (the
// Vue plugin among them) also apply to the tests. It can be an object, a function or an async function.
export default defineConfig(async (env) =>
  mergeConfig(
    await (typeof viteConfig === 'function' ? viteConfig(env) : viteConfig),
    {
      test: {
        environment: 'jsdom',
        globals: true,
        // Only the frontend tests: a PHP project keeps other files named *.test.* (for example a
        // node:test script) that Vitest must not run.
        include: ['{{frontend_root}}/**/*.{test,spec}.{js,jsx,ts,tsx}', 'tests/js/**/*.{test,spec}.{js,jsx,ts,tsx}'],
        exclude: ['**/node_modules/**', '**/e2e/**'],
      },
    },
  ),
)
