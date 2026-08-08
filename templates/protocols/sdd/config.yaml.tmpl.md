# openspec/config.yaml — Wizard-Allowed Field Reference (NOT a file to copy)
#
# ⚠️ This is NOT a template to stamp into `openspec/config.yaml`. That file is the
# exclusive artifact of gentle-ai's `/sdd-init` (see protocol `sdd`, BLOCK RULE) —
# its real shape can vary and is NOT fully uniform even across gentle-ai's own skills
# (e.g. these keys may live at the top level or nested under `context.*` depending on
# how `/sdd-init` wrote the file for this project).
#
# This block only documents the SPECIFIC leaf fields the wizard is allowed to ask the
# agent to add/update inside the EXISTING file (Phase 4.6b, `wf-settings`), always via
# a targeted, agent-driven edit that preserves everything else byte-for-byte. Never
# regenerate or overwrite the file from this reference.
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
