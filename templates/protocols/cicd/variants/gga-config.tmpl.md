# .gga — Gentleman Guardian Angel config
#
# Placeholder resolution:
#   {{provider}}       → claude | gemini | codex | opencode | ollama:<model> | lmstudio[:model] | github:<model>
#   {{file_patterns}}  → file patterns based on stack (e.g., *.ts,*.tsx,*.js,*.jsx)
#   {{exclude_patterns}} → exclusions (e.g., *.test.ts,*.spec.ts,*.d.ts,dist/*,build/*)
#   {{pr_base_branch}} → detected main branch (e.g., main)
#
# Notes:
#   - GGA uses AGENTS.md as RULES_FILE by default
#   - PR_BASE_BRANCH is necessary because auto-detection fails in CI

# AI Provider (required)
PROVIDER="{{provider}}"

# File patterns to review (by stack)
FILE_PATTERNS="{{file_patterns}}"

# Patterns to exclude (tests, generated, builds)
EXCLUDE_PATTERNS="{{exclude_patterns}}"

# File with the review rules
RULES_FILE="AGENTS.md"

# Fails if the AI response is ambiguous (recommended in CI)
STRICT_MODE="true"

# Provider response timeout (seconds)
TIMEOUT="300"

# Base branch for --pr-mode
PR_BASE_BRANCH="{{pr_base_branch}}"
