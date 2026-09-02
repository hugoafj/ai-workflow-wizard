# openspec/config.yaml — Wizard-Allowed Field Reference (NOT a file to copy)
#
# ⚠️ This is NOT a template to stamp into `openspec/config.yaml`. That file is the
# exclusive artifact of gentle-ai's `/sdd-init` (see protocol `sdd`, BLOCK RULE).
#
# This block documents the SPECIFIC canonical leaf fields the wizard is allowed to ask the
# agent to add/update inside the EXISTING file (Phase 8, step 8.1d), always via a targeted,
# `yq`-based leaf-field edit that preserves everything else byte-for-byte. The schema below
# is gentle-ai's own (`_shared/openspec-convention.md`, `docs/openspec-config.md`, and the
# `openspec/config.yaml` in the gentle-ai repo). Never regenerate or overwrite the file from
# this reference, and never invent new top-level keys (`configured`, `planned`, `extras`,
# `conventions`, `checks_before_done`) — no gentle-ai consumer reads them.
#
# What gentle-ai actually reads:
#   - sdd-apply          → strict_tdd (enables strict TDD module); the test RUNNER and its
#                          command come from cached capabilities (Engram, sdd-init), not
#                          from `testing.runner.command`; overrides in `rules.apply.test_command`
#   - sdd-verify         → `rules.verify.test_command`, `rules.verify.build_command`,
#                          `rules.verify.coverage_threshold`
#   - sdd-init           → writes the file; caches capabilities in Engram (`testing-capabilities`
#                          topic) and/or `testing.*` here
#
# Wizard-Allowed Field Edits (leaf fields, resolve placeholders from state):
#   {{strict_tdd}}          → true/false based on TDD mode (Phase 4.6 owns this — leave alone)
#   {{runner_framework}}    → vitest | playwright | vitest+playwright
#   {{layer_unit}}          → true/false
#   {{layer_integration}}   → true/false
#   {{layer_e2e}}           → true/false
#   {{coverage_available}}  → true/false (extra 1 activated)
#   {{coverage_command}}    → e.g. "npm run test:coverage"
#   {{coverage_threshold}}  → number (e.g., 80) from testing.coverage_threshold
#   {{test_command}}        → e.g. "npm test"
#   {{build_command}}       → e.g. "npm run build"
#
# NOTE: there is NO {{runner_command}} edit. Phase 8.1d writes only
# `testing.runner.framework`; the actual command lives in `rules.apply.test_command` /
# `rules.verify.test_command` (and sdd-apply detects it from cached capabilities /
# Engram, not from a `testing.runner.command` config key that no consumer reads).
#
# Canonical shape (only the leaf fields the wizard may touch; omit what isn't activated):

strict_tdd: {{strict_tdd}}

rules:
  apply:
    test_command: {{test_command}}
  verify:
    test_command: {{test_command}}
    build_command: {{build_command}}
    coverage_threshold: {{coverage_threshold}}

testing:
  strict_tdd: {{strict_tdd}}        # Phase 4.6 writes this (informational)
  runner:
    framework: {{runner_framework}} # 8.1d writes framework only — no `command` child
  layers:
    unit:
      available: {{layer_unit}}
      tool: vitest
    integration:
      available: {{layer_integration}}
      tool: vitest
    e2e:
      available: {{layer_e2e}}
      tool: playwright
  coverage:
    available: {{coverage_available}}
    command: {{coverage_command}}
