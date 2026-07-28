# visual-snapshots — Visual regression configuration fragment
#
# This fragment is injected inside defineConfig({ ... }) in playwright.config.ts
# No placeholders required — static configuration
#
# Notes:
#   - References are generated with: npx playwright test --update-snapshots
#   - Review and commit reference images manually

expect: {
  toHaveScreenshot: { maxDiffPixels: 100 },
},
