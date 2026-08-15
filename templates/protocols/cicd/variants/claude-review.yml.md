# claude-review.yml — Claude Code Review workflow
#
# For claude provider only. Uses external action anthropics/claude-code-action
#
# Notes:
#   - The action posts its own comments (we cannot modify its format)
#   - We added a failure handler for user feedback
#   - fetch-depth: 0 so it can see the full history
#   - claude-code-action uses Anthropic's default model. Does not support direct model change.
#     To use a different model, see: https://docs.anthropic.com/en/docs/about-claude/models

name: Claude Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  claude-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Claude Code Review
        id: claude-review
        uses: anthropics/claude-code-action@v1.0.193
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # Inline suggestions: allows Claude to create inline comments on the code.
          # If you prefer review only without suggestions, remove mcp__github_inline_comment__create_inline_comment.
          # (Only applies to Claude Code Action)
          claude_args: |
            --allowedTools "mcp__github_inline_comment__create_inline_comment,Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*)"

      - name: Post failure comment on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const errorMsg = `⚠️ **Claude Code Review failed**

            The Claude Code review could not complete. This is usually caused by:
            - **API quota exceeded** — check your Anthropic API key and billing
            - **Provider timeout** — the review took too long, try again later
            - **Invalid API key** — verify your ANTHROPIC_API_KEY secret is configured

            **Workflow**: \`claude-review.yml\` | **Job**: \`claude-review\` | **Phase**: Claude Code Review

            *This comment was added automatically by the CI pipeline.*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: errorMsg
            });
