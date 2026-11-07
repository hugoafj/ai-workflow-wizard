# coverage-thresholds.ratchet — Coverage floor fragment for the ratchet mode (Vitest)
#
# This fragment is injected inside test: { ... } in vitest.config.ts.
# Placeholder resolution:
#   {{threshold}} → the current floor (number, e.g., 0 or 34)
# The floor is raised only by the coverage-ratchet workflow (a chore PR), never by Vitest itself.
# The json-summary reporter writes coverage/coverage-summary.json, which that workflow reads.

coverage: {
  provider: 'v8',
  reporter: ['text', 'json-summary'],
  thresholds: {
    lines: {{threshold}},
  },
},
