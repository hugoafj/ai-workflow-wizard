# release-please.yml — Release Please workflow
#
# Template variables (from .wizard-state.json):
#   ci.conventional_commits — true if using conventional commits
#   ci.release_ai_summary — true if AI summary is enabled
#   ci.release_ai_provider — claude, openai, or gemini (provider for AI summary)
#   answers.project_name — project name for release branch naming
#
# Notes:
#   - release-type: node assumes package.json. For markdown-only, use release-type: simple
#   - The repo must allow GitHub Actions to create PRs (Settings → Actions → General → Workflow permissions)

name: release-please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      pr: ${{ steps.release.outputs.pr }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with:
          release-type: node
{{if ci.release_ai_summary}}

  ai-summary:
    needs: release-please
    if: needs.release-please.outputs.pr
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - name: Generate AI summary for release PR
        run: |
          echo "AI summary job enabled (provider: {{ci.release_ai_provider}})"
          # {{AI_SUMMARY_JOB}}
          echo "Project: {{answers.project_name}}"
{{/if}}
