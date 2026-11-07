import { defineConfig, mergeConfig } from 'vitest/config'
import * as vite from 'vite'
import viteConfig from './{{vite_config_file}}'

// Vitest ignores vite.config.* when a vitest.config.* exists, so the Vite config of the app is merged
// in here: its aliases (for example the "@" alias that laravel-vite-plugin sets) and its plugins also
// apply to the tests. It can be an object, a function or an async function.

// Vite only treats .jsx and .tsx as JSX. The .js files under {{frontend_root}} often hold JSX too, so they
// go through the JSX transform first (Oxc on Vite 8, esbuild on Vite 7 and older). It does no harm when the
// Vite config of the app already handles them.
const jsxInJs = {
  name: 'jsx-in-js',
  enforce: 'pre' as const,
  transform(code: string, id: string) {
    if (!/{{frontend_root_regex}}\/.*\.js$/.test(id.split('?')[0])) return null
    const v = vite as any
    return v.transformWithOxc
      ? v.transformWithOxc(code, id, { lang: 'jsx' })
      : v.transformWithEsbuild(code, id, { loader: 'jsx' })
  },
}

export default defineConfig(async (env) =>
  mergeConfig(
    await (typeof viteConfig === 'function' ? viteConfig(env) : viteConfig),
    {
      plugins: [jsxInJs],
      test: {
        environment: 'jsdom',
        setupFiles: ['./tests/js/setup.ts'],
        globals: true,
        // Only the frontend tests: a PHP project keeps other files named *.test.* (for example a
        // node:test script) that Vitest must not run.
        include: ['{{frontend_root}}/**/*.{test,spec}.{js,jsx,ts,tsx}', 'tests/js/**/*.{test,spec}.{js,jsx,ts,tsx}'],
        exclude: ['**/node_modules/**', '**/e2e/**'],
      },
    },
  ),
)
