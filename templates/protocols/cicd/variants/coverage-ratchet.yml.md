# coverage-ratchet.yml — Raises the coverage floor through a chore PR (ratchet mode, Node)
#
# Placeholder resolution:
#   {{node_version}} and {{npm_major}} → as in quality-guard.yml.md
#   {{measure_steps}} → the step that measures the line coverage the floor is compared with
#   {{raise_steps}}   → the step that raises the floor in .wizard-state.json and in the unit config, then opens the PR
#
# Notes:
#   - it runs on each merge to main and never pushes to main: the floor only moves through a PR
#   - the PR is titled chore(coverage), so release-please does not release for it and no deploy runs for a chore
#   - the repo must allow GitHub Actions to create PRs (Settings → Actions → General → Workflow permissions)
#   - the PR is opened with GITHUB_TOKEN, which does not start other workflows: if quality-guard is a required
#     check, that PR needs the check run by hand or a merge by an admin

name: Coverage ratchet

on:
  push:
    branches: [main]

concurrency:
  group: coverage-ratchet
  cancel-in-progress: false

permissions:
  contents: write
  pull-requests: write

jobs:
  ratchet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "{{node_version}}"
          cache: npm

      - name: Pin npm version (match local lockfile)
        run: npm install -g npm@{{npm_major}}

      - name: Install dependencies
        run: npm ci

      {{measure_steps}}

      {{raise_steps}}
