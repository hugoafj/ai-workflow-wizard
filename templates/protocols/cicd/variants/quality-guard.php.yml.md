# quality-guard.php.yml — CI Quality Guard workflow for PHP stacks (php-laravel, php-generic)
#
# Chosen by the Builder instead of quality-guard.yml.md when stack_key starts with "php-".
# The Node variant stays untouched for every Node project.
#
# Placeholder resolution:
#   {{php_version}}  → state discovery.php_version, else composer.json "config.platform.php", else the first X.Y of "require.php", else 8.3
#   {{test_command}} → state testing.test_command, else php artisan test (Laravel), pest or phpunit
#   {{node_version}} and {{npm_major}} → as in quality-guard.yml.md (only used by the frontend steps)
#
# Conditional resolution:
#   <if the project is a Laravel app>:                  → prepare .env and APP_KEY (stack_key php-laravel)
#   <if composer.json requires laravel/pint>:           → include the code style step (changed files only)
#   <if composer.json requires phpstan or larastan>:    → include the static analysis step
#   <if unit or integration layer is active>:           → include the test step
#   <if the frontend layer is active>:                  → include the Node setup, npm ci, frontend tests and build
#
# Notes:
#   - setup-php installs PHP and Composer on the runner; the PHP version comes from the project
#   - Pint only checks the files the PR changed (--diff against the base branch), so a legacy codebase
#     with existing style violations does not fail every PR; full history is fetched for that diff
#   - composer audit runs with continue-on-error: true so a transitive advisory does not block the PR
#   - the test step runs the suite with the project's own command; tests that need a database,
#     Redis or another service need a `services:` block added to this job by the team
#   - the frontend steps only exist when testing.layers has `frontend`: Node setup, npm ci, `npm run test`
#     and the build script when package.json has one
#   - failure handler posts a comment explaining which step failed

name: CI Quality Guard

on:
  pull_request:
    branches: [main, master]

jobs:
  quality-guard:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: shivammathur/setup-php@v2
        with:
          php-version: "{{php_version}}"
          tools: composer:v2
          coverage: none

      - name: Install dependencies
        run: composer install --no-interaction --prefer-dist --no-progress

      <if the project is a Laravel app>:
      - name: Prepare Laravel environment
        run: |
          [ -f .env ] || cp .env.example .env 2>/dev/null || touch .env
          php artisan key:generate --ansi

      <if composer.json requires laravel/pint>:
      - name: Code style (Pint, files changed in the PR)
        run: vendor/bin/pint --test --diff=origin/${{ github.base_ref }}

      <if composer.json requires phpstan or larastan>:
      - name: Static analysis (PHPStan)
        run: vendor/bin/phpstan analyse --no-progress

      - name: Security audit
        run: composer audit
        continue-on-error: true

      <if unit or integration layer is active>:
      - name: Unit & integration tests
        run: {{test_command}}

      <if the frontend layer is active>:
      - uses: actions/setup-node@v4
        with:
          node-version: "{{node_version}}"
          cache: npm

      <if the frontend layer is active>:
      - name: Pin npm version (match local lockfile)
        run: npm install -g npm@{{npm_major}}

      <if the frontend layer is active>:
      - name: Install frontend dependencies
        run: npm ci

      <if the frontend layer is active>:
      - name: Frontend unit tests
        run: npm run test

      <if the frontend layer is active>:
      - name: Build frontend
        run: |
          if [ -f package.json ] && grep -q '"build"' package.json; then
            npm run build
          else
            echo "No build script defined; skipping."
          fi

      - name: Post failure comment on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const errorMsg = `⚠️ **CI Quality Guard failed**

            The CI pipeline failed. Check the workflow logs for details on which step failed.

            **Common causes:**
            - Code style errors in the files you changed — fix with \`vendor/bin/pint --dirty\`
            - Static analysis errors — run \`vendor/bin/phpstan analyse\` locally
            - Test failures — run \`{{test_command}}\` (and \`npm run test\` for the frontend) locally
            - Missing environment — the tests may need a database or another service

            **Workflow**: \`quality-guard.yml\` | **Job**: \`quality-guard\` | **Phase**: CI Quality Guard

            *This comment was added automatically by the CI pipeline.*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: errorMsg
            });
