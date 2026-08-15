# security-review.gemini.yml — Gemini Security Review workflow
#
# For gemini/opencode providers only. For Claude, use security-review.claude.yml.md
#
# Notes:
#   - Uses external action Codium-ai/pr-agent
#   - The action posts its own comments (we cannot modify its format)
#   - We added a failure handler for user feedback

name: Security Review (Gemini)

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  ai_security_review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: PR Agent Security Audit
        id: pr-agent-review
        uses: Codium-ai/pr-agent@v0.42.0
        env:
          GOOGLE_AI_STUDIO_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          CONFIG.MODEL: "gemini/gemini-2.5-flash"
          PR_REVIEWER.EXTRA_INSTRUCTIONS: >
            Act as a Certified Software Security Auditor (OSCP/CISSP).
            Your task is to perform a static security analysis (SAST) on the
            changes in this Pull Request.

            Analyze the code looking exclusively for critical vulnerabilities:
            1. Injections: SQL, NoSQL, OS Command Injection, and LDAP Injection.
            2. Authentication Management: login bypass, misconfigured JWT tokens
              or insecure cookies.
            3. Sensitive Data Exposure: hardcoded credentials (API keys,
              passwords), PII in logs, or lack of encryption.
            4. Access Control: Insecure Direct Object References (IDOR) and
              missing role validation (RBAC/ABAC).
            5. Security Configurations: missing HTTP headers (HSTS, CSP),
              misconfigured CORS, or dependencies with known vulnerabilities.
            6. Error Handling: stack trace leaks or infrastructure
              information in error responses.

            Response format:
            - Risk: vulnerability name.
            - Severity: (Low, Medium, High, Critical).
            - Location: affected file and lines.
            - Description: why it is a risk and how it could be exploited.
            - Remediation: corrected code or steps to mitigate the risk.

            Be concise. If no security risks are found, indicate that the
            code appears secure from an AppSec perspective.

      - name: Post failure comment on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const errorMsg = `⚠️ **Security Review failed**

            The Gemini security review (PR Agent) could not complete. This is usually caused by:
            - **API quota exceeded** — check your Gemini API key and billing
            - **Provider timeout** — the review took too long, try again later
            - **Invalid API key** — verify your secrets are configured correctly

            **Workflow**: \`security-review.yml\` | **Job**: \`ai_security_review\` | **Phase**: Security Review

            *This comment was added automatically by the CI pipeline.*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: errorMsg
            });
