# quality-guard.yml — CI Quality Guard workflow
#
# Placeholder resolution:
#   {{node_version}} → project engines.node, or 22 by default
#   {{npm_major}}    → user's local npm major version (e.g., 11)
#
# Conditional resolution:
#   <if type-check script or tsconfig.json exists>: → include type-check step
#   <if unit or integration layer is active>:      → include test step
#   <if test:sanitization script exists>:          → include sanitization step
#   <if e2e layer is active>:                      → include Playwright steps
#
# Notes:
#   - Node 22 is active LTS, satisfies >=18/>=20/>=22 of the current ecosystem
#   - npm is pinned before npm ci to avoid lockfile desync
#   - continue-on-error: true on security audit to avoid blocking on transitive deps
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

      - name: Lint
        run: |
          if [ -f package.json ] && grep -q '"lint"' package.json; then
            npm run lint
          else
            echo "No lint script defined; skipping."
          fi

      <if type-check script or tsconfig.json exists>:
      - name: Type check
        run: npx tsc --noEmit

      - name: Security audit
        run: npm audit --audit-level=high
        continue-on-error: true

      <if unit or integration layer is active>:
      - name: Unit & integration tests
        run: npm run test

      <if test:sanitization script exists>:
      - name: Sanitization tests
        run: npm run test:sanitization

      - name: Build
        run: |
          if [ -f package.json ] && grep -q '"build"' package.json; then
            npm run build
          else
            echo "No build script defined; skipping."
          fi

      <if e2e layer is active>:
      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium

      <if e2e layer is active>:
      - name: E2E tests
        run: npm run test:e2e

      - name: Post failure comment on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const errorMsg = `⚠️ **CI Quality Guard failed**

            The CI pipeline failed. Check the workflow logs for details on which step failed.

            **Common causes:**
            - Lint errors — fix with \`npm run lint\`
            - Type errors — fix with \`npx tsc --noEmit\`
            - Test failures — run \`npm test\` locally
            - Build errors — run \`npm run build\` locally

            **Workflow**: \`quality-guard.yml\` | **Job**: \`quality-guard\` | **Phase**: CI Quality Guard

            *This comment was added automatically by the CI pipeline.*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: errorMsg
            });
