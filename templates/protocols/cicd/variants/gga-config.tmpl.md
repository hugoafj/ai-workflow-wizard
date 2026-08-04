# .gga — Gentleman Guardian Angel config
#
# Template variables (from .wizard-state.json):
#   ci.gga_provider — claude | gemini | openai | ollama
#   discovery.gga_file_patterns — file patterns based on stack
#   discovery.gga_exclude_patterns — exclusions (tests, generated, builds)
#   discovery.default_branch — detected main branch
#
# Notes:
#   - GGA uses AGENTS.md as RULES_FILE by default
#   - PR_BASE_BRANCH is necessary because auto-detection fails in CI

# AI Provider (required)
PROVIDER="{{ci.gga_provider}}"

# File patterns to review (by stack)
FILE_PATTERNS="{{discovery.gga_file_patterns}}"

# Patterns to exclude (tests, generated, builds)
EXCLUDE_PATTERNS="{{discovery.gga_exclude_patterns}}"

# File with the review rules
RULES_FILE="AGENTS.md"

# Fails if the AI response is ambiguous (recommended in CI)
STRICT_MODE="true"

# Provider response timeout (seconds)
TIMEOUT="300"

# Base branch for --pr-mode
PR_BASE_BRANCH="{{discovery.default_branch}}"
