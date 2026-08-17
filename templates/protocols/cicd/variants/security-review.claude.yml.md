# security-review.claude.yml — Claude Code Security Review workflow
#
# For claude provider only. For other providers, use security-review.gemini.yml.md
#
# Notes:
#   - Uses external action anthropics/claude-code-security-review
#   - The action posts its own comments (we cannot modify its format)
#   - We added a failure handler for user feedback

name: Security Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  security-review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Claude Code Security Review
        id: claude-review
        uses: anthropics/claude-code-security-review@0c6a49f1fa56a1d472575da86a94dbc1edb78eda
        with:
          claude-api-key: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Post failure comment on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const errorMsg = `⚠️ **Security Review failed**

            The Claude Code security review could not complete. This is usually caused by:
            - **API quota exceeded** — check your Anthropic API key and billing
            - **Provider timeout** — the review took too long, try again later
            - **Invalid API key** — verify your secrets are configured correctly

            **Workflow**: \`security-review.yml\` | **Job**: \`security-review\` | **Phase**: Security Review

            *This comment was added automatically by the CI pipeline.*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: errorMsg
            });
