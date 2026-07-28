# .pr_agent.toml — PR Agent configuration
#
# Used by Codium-ai/pr-agent in GitHub Actions
# Docs: https://github.com/Codium-ai/pr-agent/blob/main/docs/docs/usage-guide/configuration-options.md

[config]
# Run review on opened, synchronize, and reopened events
pr_actions = ["opened", "synchronize", "reopened"]

[rating]
# Enable code feedback
enable_code_suggestions = true

[review]
# Disable review (use pr_code_suggestions instead for actionable feedback)
enable_review = false

[pr_code_suggestions]
# Enable code suggestions with actionable feedback
enable_code_suggestions = true
