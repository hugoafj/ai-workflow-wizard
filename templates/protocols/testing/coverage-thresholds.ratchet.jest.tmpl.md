# coverage-thresholds.ratchet.jest — Coverage floor fragment for the ratchet mode (Jest)
#
# This fragment is injected inside module.exports = { ... } in jest.config.js.
# Placeholder resolution:
#   {{threshold}} → the current floor (number, e.g., 0 or 34)
# The floor is raised only by the coverage-ratchet workflow (a chore PR), never by Jest itself.
# The json-summary reporter writes coverage/coverage-summary.json, which that workflow reads.

coverageReporters: ['text', 'json-summary'],
coverageThreshold: {
  global: {
    lines: {{threshold}},
  },
},
