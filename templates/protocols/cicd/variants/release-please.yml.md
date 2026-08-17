# release-please.yml — Release Please workflow
#
# Template variables (from .wizard-state.json):
#   ci.conventional_commits — true if using conventional commits
#   ci.release_ai_summary — true if AI summary is enabled
#   ci.release_ai_provider — claude, openai, or gemini (provider for AI summary)
#   answers.project_name — project name for release branch naming
#
# Notes:
#   - release-type: simple is the default for markdown/templates projects (override to `node` for Node.js projects)
#   - The repo must allow GitHub Actions to create PRs (Settings → Actions → General → Workflow permissions)

name: release-please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      pr: ${{ steps.release.outputs.pr }}
    permissions:
      contents: write
      pull-requests: write
      issues: write
    steps:
      - uses: googleapis/release-please-action@v4
        id: release

  # {{AI_SUMMARY_JOB}}
