# openspec/config.yaml — SDD project configuration
#
# Placeholders (resolve from state):
#   {{strict_tdd}}          → true/false based on TDD mode
#   {{runner}}              → vitest | playwright | vitest+playwright
#   {{unit}}                → true/false
#   {{integration}}         → true/false
#   {{e2e}}                 → true/false
#   {{coverage_threshold}}  → number (e.g., 80) from testing.coverage_threshold
#   {{checks_before_done}}  → list of scripts based on active layers
#   {{project_context}}     → multi-line text with stack + architecture + testing + style
#
schema: spec-driven

context: |
  {{project_context}}

testing:
  strict_tdd: {{strict_tdd}}
  test_runner: {{runner}}
  test_command: npm test
  coverage_command: npm run test:coverage
  e2e_command: npm run test:e2e
  layers:
    unit: {{unit}}
    integration: {{integration}}
    e2e: {{e2e}}
  tools:
    linter: eslint
    linter_command: npm run lint
    type_checker: tsc
    type_checker_command: npx tsc --noEmit
    formatter: none

rules:
  proposal:
    - Include rollback plan for risky changes
  specs:
    - Use Given/When/Then for scenarios
    - Use RFC 2119 keywords (MUST, SHALL, SHOULD, MAY)
  design:
    - Include sequence diagrams for complex flows
    - Document architecture decisions with rationale
  tasks:
    - Group by phase, use hierarchical numbering
    - Keep tasks completable in one session
  apply:
    - Follow existing code patterns
    tdd: false
    test_command: npm test
  verify:
    test_command: npm test
    build_command: npm run build
    coverage_threshold: {{coverage_threshold}}
  archive:
    - Warn before merging destructive deltas

checks_before_done:
  - npm run lint
  - npm run build
  {{checks_before_done}}
