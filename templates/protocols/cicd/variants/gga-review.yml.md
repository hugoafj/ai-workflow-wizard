# gga-review.yml — Gentleman Guardian Angel AI review workflow
#
# Placeholder resolution:
#   {{provider_cli}}    → npm package of the provider (see table below)
#   {{provider_secret}} → secret name in GitHub Actions
#
# Provider table:
#   | gga_provider | {{provider_cli}}              | {{provider_secret}} |
#   |--------------|-------------------------------|---------------------|
#   | claude       | @anthropic-ai/claude-code     | ANTHROPIC_API_KEY   |
#   | gemini       | @google/gemini-cli            | GEMINI_API_KEY      |
#   | codex        | @openai/codex                 | OPENAI_API_KEY      |
#   | opencode     | (based on its docs)           | (based on its docs)      |
#
# Notes:
#   - fetch-depth: 0 so --pr-mode can diff against the base
#   - git fetch of the base branch is necessary because actions/checkout does not bring it as a local ref
#   - GEMINI_CLI_TRUST_WORKSPACE: true required since Gemini CLI v0.39.1+
#   - GGA posting comments: GGA automatically posts review comments,
#     we cannot modify its format. Attribution only applies to comments that
#     we control (e.g., ai-summary-job).

name: Gentleman Guardian Angel

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Fetch base branch
        run: git fetch origin "$GITHUB_BASE_REF":"$GITHUB_BASE_REF" || true

      - name: Install Gentleman Guardian Angel
        run: |
          git clone --depth=1 https://github.com/Gentleman-Programming/gentleman-guardian-angel.git /tmp/gga
          chmod +x /tmp/gga/bin/gga
          echo "/tmp/gga/bin" >> "$GITHUB_PATH"

      - name: Install provider CLI ({{provider_cli}})
        run: npm install -g {{provider_cli}}
        env:
          {{provider_secret}}: ${{ '{{' }}secrets.{{provider_secret}}{{ '}}' }}

      - name: Run AI review (GGA, against AGENTS.md)
        id: gga-review
        run: gga run --pr-mode --diff-only
        env:
          {{provider_secret}}: ${{ '{{' }}secrets.{{provider_secret}}{{ '}}' }}
          GEMINI_CLI_TRUST_WORKSPACE: true

      - name: Post failure comment on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const provider = '${{ '{{' }}provider_cli{{ '}}' }}';
            const errorMsg = `⚠️ **GGA review failed**

            The AI code review could not complete. This is usually caused by:
            - **API quota exceeded** — check your ${provider} API key and billing
            - **Provider timeout** — the review took too long, try again later
            - **Invalid API key** — verify your secrets are configured correctly

            **Workflow**: \`gga-review.yml\` | **Job**: \`review\` | **Phase**: GGA PR Review

            *This comment was added automatically by the CI pipeline.*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: errorMsg
            });
