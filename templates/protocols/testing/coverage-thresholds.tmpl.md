# coverage-thresholds — Coverage thresholds fragment
#
# This fragment is injected inside test: { ... } in vitest.config.ts
# Placeholder resolution:
#   {{threshold}} → number (e.g., 80)

coverage: {
  provider: 'v8',
  thresholds: {
    lines: {{threshold}},
    functions: {{threshold}},
    branches: {{threshold}},
    statements: {{threshold}},
  },
},
