# release-please.yml — Release Please workflow
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

# {{AI_SUMMARY_JOB}} — injected here if release_ai_summary == true
