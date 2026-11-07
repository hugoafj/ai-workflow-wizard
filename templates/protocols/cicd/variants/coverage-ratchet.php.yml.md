# coverage-ratchet.yml — Raises the coverage floors through a chore PR (ratchet mode, PHP stacks)
#
# Placeholder resolution:
#   {{php_version}}          → as in quality-guard.php.yml.md
#   {{php_extensions_line}}  → the extensions line for setup-php, or nothing when the project needs none
#   {{laravel_env_steps}}    → the .env and APP_KEY step, only for a Laravel app
#   {{measure_steps}}        → the steps that measure the backend (Clover) and the frontend (json-summary) coverage
#   {{raise_steps}}          → the step that raises each floor in .wizard-state.json and its file, then opens the PR
#
# Notes:
#   - it runs on each merge to main and never pushes to main: the floors only move through a PR
#   - the backend floor is COVERAGE_FLOOR in quality-guard.yml; the frontend floor is the lines threshold in vitest.config.ts
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

      - uses: shivammathur/setup-php@v2
        with:
          php-version: "{{php_version}}"
          tools: composer:v2
          coverage: pcov
          {{php_extensions_line}}

      - name: Install dependencies
        run: composer install --no-interaction --prefer-dist --no-progress

      {{laravel_env_steps}}

      {{measure_steps}}

      {{raise_steps}}
