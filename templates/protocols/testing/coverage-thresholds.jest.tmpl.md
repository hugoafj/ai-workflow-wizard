# coverage-thresholds.jest — Coverage thresholds fragment for jest.config.js
#
# This fragment is injected right after `module.exports = {` in jest.config.js
# Placeholder resolution:
#   {{threshold}} → number (e.g., 80)

coverageThreshold: {
  global: {
    lines: {{threshold}},
    functions: {{threshold}},
    branches: {{threshold}},
    statements: {{threshold}},
  },
},
