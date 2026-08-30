# gemini-review.yml — Gemini Code Review workflow
#
# For gemini/opencode providers only. Uses external action Codium-ai/pr-agent
#
# Notes:
#   - The action posts its own comments (we cannot modify its format)
#   - We added a failure handler for user feedback
#   - The model can be changed in CONFIG.MODEL (see https://ai.google.dev/gemini-api/docs/models)
#     Available models: gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash, etc.

name: Gemini Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  gemini-review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
      issues: write
    steps:
      - uses: actions/checkout@v4

      - name: PR Agent Action
        id: pr-agent-review
        uses: Codium-ai/pr-agent@v0.42.0
        env:
          # PR Agent reads the Gemini key from GOOGLE_AI_STUDIO.GEMINI_API_KEY (dot notation).
          GOOGLE_AI_STUDIO.GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # Change the model according to your preference. Some models require an API key with billing enabled.
          CONFIG.MODEL: "gemini/gemini-2.5-flash"
          CONFIG.MAX_MODEL_TOKENS: "1048576"
          github_action_config.pr_actions: '["opened", "synchronize", "reopened"]'
          github_action_config.auto_review: "true"
          github_action_config.auto_describe: "true"
          # Configurable from state.ci.auto_improve (default true). Regenerate this
          # workflow after toggling "AI Review Suggestions" in /wf-settings.
          github_action_config.auto_improve: "true"

      - name: Post failure comment on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const errorMsg = `⚠️ **Gemini Code Review failed**

            The Gemini code review (PR Agent) could not complete. This is usually caused by:
            - **API quota exceeded** — check your Gemini API key and billing
            - **Provider timeout** — the review took too long, try again later
            - **Invalid API key** — verify your GEMINI_API_KEY secret is configured

            **Workflow**: \`gemini-review.yml\` | **Job**: \`gemini-review\` | **Phase**: Gemini Code Review

            *This comment was added automatically by the CI pipeline.*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: errorMsg
            });
