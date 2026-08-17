# ai-summary-job.gemini.yml — AI summary job fragment
#
# This fragment is merged into release-please.yml as a second job.
# Not a standalone file — injected after the release-please job.
#
# Notes:
#   - No third-party dependencies: only actions/checkout, curl, gh pr comment
#   - If GEMINI_API_KEY is not configured, it silently fails with fallback
#   - Includes attribution footer to identify the comment origin

  update-pr-with-ai:
    needs: release-please
    if: ${{ needs.release-please.outputs.pr }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Generate AI Summary and comment on PR
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          PR_JSON: ${{ needs.release-please.outputs.pr }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          PR_NUMBER=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['number'])")
          PR_BODY=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['body'])")
          SUMMARY=$(curl -s \
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}" \
            -H "Content-Type: application/json" \
            -d "$(jq -n \
              --arg text "Summarize these changes for humans, highlighting benefits for the end user. Keep the Markdown format.\n\n${PR_BODY}" \
              '{contents:[{parts:[{text:$text}]}]}')" \
            | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['candidates'][0]['content']['parts'][0]['text'])" 2>/dev/null \
            || echo "_Could not generate automatic summary._")

          if [ -n "$SUMMARY" ] && [ "$SUMMARY" != "_Could not generate automatic summary._" ]; then
            COMMENT=$(printf "## 🤖 AI Suggested Summary\n\n%s\n\n---\n*Review this text before merging. What remains here will be part of the official release.*\n\n---\n*Added by AI Summary Job | workflow: release-please.yml | Phase: Post-release*" "${SUMMARY}")
            gh pr comment "${PR_NUMBER}" --body "$COMMENT"
          fi

      - name: Post failure comment on PR
        if: failure()
        env:
          PR_NUMBER: ${{ fromJson(needs.release-please.outputs.pr).number }}
        uses: actions/github-script@v7
        with:
          script: |
            const errorMsg = `⚠️ **AI Summary failed`

            The AI summary generation could not complete. This is usually caused by:
            - **Gemini API quota exceeded** — check your Gemini API key and billing
            - **Provider timeout** — the summary generation took too long
            - **Invalid API key** — verify your GEMINI_API_KEY secret is configured

            **Workflow**: \`release-please.yml\` | **Job**: \`update-pr-with-ai\` | **Phase**: Post-release Summary

            *This comment was added automatically by the CI pipeline.*`;

            github.rest.issues.createComment({
              issue_number: parseInt(process.env.PR_NUMBER, 10),
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: errorMsg
            });
