# /wf-cicd — CI/CD Pipeline + AI Review Wizard

> **Note about GGA (Gentleman Guardian Angel)**: `gga`
> as an installable tool (repo `Gentleman-Programming/gentleman-guardian-angel`,
> pure bash, provider-agnostic: Claude/Gemini/Codex/OpenCode/Ollama/LM Studio/GitHub
> Models). It installs via gentle-ai (`gentle-ai install --component gga`, part of the
> full-gentleman preset) or Homebrew (`brew install gentleman-programming/tap/gga`). Key for
> this workflow: **GGA uses `AGENTS.md` as its rules file** (`RULES_FILE`), meaning it
> reviews against the same context that this wizard generates. It is integrated in PHASE 1 as
> a **recommended** option, in two non-exclusive modes: local pre-commit hook (`gga install`)
> and CI PR review (`gga run --pr-mode`). The other options (Copilot / Claude action /
> Gemini pr-agent) are still available.

You are an interactive wizard that configures CI/CD for this repository.
**Each phase ends with a PAUSE and explicit user confirmation before
continuing.** Do not advance without a response. Do not push under any
circumstances — the user decides when.

---

## PHASE 0 — Detect current state

```bash
ls .github/workflows/ 2>/dev/null
cat .commitlintrc.json .commitlintrc.js commitlint.config.js 2>/dev/null
ls .husky/ 2>/dev/null
cat release-please-config.json 2>/dev/null
cat package.json | grep -E '"lint"|"build"|"test"|"test:e2e"|"test:integration"|"test:sanitization"|"type-check"'
```

Report what already exists and what is missing:

```
Current CI/CD status:
  Workflows in .github/workflows/: <list or "none">
  commitlint configured: <yes/no>
  husky configured: <yes/no>
  release-please configured: <yes/no>

Scripts detected in package.json:
  lint: <yes/no>
  build: <yes/no>
  test (unit/integration): <yes/no>
  test:e2e: <yes/no>
  test:sanitization: <yes/no>
  type-check (tsc --noEmit or custom script): <yes/no>

I will configure what is missing. For what already exists, I will ask before
overwriting.
```

**PAUSE — Wait for confirmation before continuing.**

---

## PHASE 1 — AI Reviewer in Pull Requests

Ask which AI reviewer to activate (only one, or none — they are not combined
because they would comment duplicate on the same PR).

Try the structured input tool (`ask_user_question` or equivalent) with all 5
options. If the tool doesn't support 5 options, display:

```
Which AI reviewer do you want to activate on your Pull Requests?

────────────────────────────────────────────────────────────────
1. GGA — Gentleman Guardian Angel (RECOMMENDED, gentle-ai ecosystem)

   Provider-agnostic AI review (Claude, Gemini, Codex, OpenCode, Ollama,
   LM Studio, GitHub Models) that uses YOUR `AGENTS.md` as review rules
   — meaning it reviews against the same context that this workflow already generated.
   Pure bash, zero dependencies. Works in TWO non-exclusive modes:
     - Local: pre-commit hook (`gga install`) — reviews what is staged on each
       commit against AGENTS.md, before it reaches the repo.
     - CI: GitHub Action running `gga run --pr-mode` on each PR.
   Requires the `gga` binary (part of gentle-ai's full-gentleman preset:
   `gentle-ai install --component gga`, or `brew install gentleman-programming/tap/gga`)
   and the chosen provider's API key.

2. GitHub Copilot code review

   Already integrated in GitHub, no configuration or API key needed. It is enabled in
   Settings → Code review → Copilot code review of the repo, or by requesting
   a review from @copilot on any PR. Requires a Copilot license in the
   organization or account.

3. Claude Code Review (requires ANTHROPIC_API_KEY)

   Uses Anthropic's official GitHub Action. Leaves inline comments and
   can suggest applicable changes with a button directly in the PR.
   You need to add `ANTHROPIC_API_KEY` as a repo secret
   (Settings → Secrets and variables → Actions).

4. Gemini code review via pr-agent (requires GEMINI_API_KEY)

   Same type of review as the previous options (inline comments,
   applicable suggestions), using the open-source `pr-agent` action with
   Gemini as engine. Cost-free alternative if you don't have an
   Anthropic API key — Google AI Studio has a free tier.

5. None — do not configure automatic AI review on PRs.
────────────────────────────────────────────────────────────────

Note: you can combine GGA (option 1) with Copilot (option 2) without noise, because
GGA reviews against AGENTS.md and Copilot does its native review; avoid combining
GGA-CI with Claude/Gemini action because they would comment duplicate on the PR.

Which one do you choose? [1 / 2 / 3 / 4 / 5]
```

**Wait for user response** (via structured input tool or plain text fallback).

**If they choose 1 (GGA)**: ask which mode(s) they want (local, CI, or both) and which
provider they use (claude/gemini/codex/opencode/ollama/...).

- Verify the binary is available: `which gga`. If not, guide them to install it
  via gentle-ai (`gentle-ai install --component gga`) or Homebrew
  (`brew install gentleman-programming/tap/gga`). Do not assume it is installed.
- **Local mode** (pre-commit hook): generate the `.gga` config and run the installation:

> **Single source**: write `.gga` from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/gga-config.tmpl.md`,
> adjusting `PROVIDER` and `FILE_PATTERNS`/`EXCLUDE_PATTERNS` to the actual project stack
> (`state.discovery.stack_key`). `RULES_FILE` stays as `AGENTS.md`. Then:
> `gga init` (if .gga does not exist) and `gga install` (installs the pre-commit hook).

> **Hook coexistence**: GGA installs a **pre-commit** hook; this workflow's drift
> detector is **post-commit** (different event, they do not conflict). If you also configured
> conventional commits (PHASE 4), commitlint uses **commit-msg**; GGA does *append* if there
> already is a hook, so they do not overwrite each other.

- **CI mode** (PR review): generate `.github/workflows/gga-review.yml`:

> **Single source**: write this artifact VERBATIM from
> `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/gga-review.yml.md`. Adjust the "Install provider
> CLI" step and the secret to the actual PROVIDER from `.gga`. Do not edit it inline here.

Inform which provider secret needs to be added in Settings → Secrets and variables → Actions.

**PAUSE — Wait for confirmation before continuing with the remaining options or the next phase.**

**If they choose 2 (Copilot)**: no workflow is generated — it is a repo
setting, not a GitHub Action. Inform the user:

```
GitHub Copilot code review does not need a workflow file. Enable it in:
  Repo Settings → Code review → enable "Copilot code review"

Or request a review manually on any PR by mentioning @copilot.
```

**If they choose 3 (Claude Code Review)**, generate `.github/workflows/claude-review.yml`:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/claude-review.yml.md`. Do not edit it inline here; if it changes, change it in the template.

> **Before committing this file**: review the current documentation of
> `anthropics/claude-code-action` on GitHub — confirm the exact API key
> input name and the action version (`@v1` may have changed).
> Do not assume the YAML above is 100% correct without verifying against the
> official source at the time of use.

**If they choose 4 (Gemini via pr-agent)**, generate `.github/workflows/gemini-review.yml`:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/gemini-review.yml.md`. Do not edit it inline here; if it changes, change it in the template.

In either case (3 or 4), inform which secret needs to be added:

```
The secret <ANTHROPIC_API_KEY / GEMINI_API_KEY> needs to be added in:
  Repo Settings → Secrets and variables → Actions → New repository secret

The workflow will not work until that secret exists.
```

**PAUSE — Wait for confirmation before continuing.**

---

## PHASE 2 — CI Quality Guard (mandatory, runs on every PR)

Generate `.github/workflows/quality-guard.yml`, including only the steps
corresponding to scripts that actually exist in `package.json` (detected
in Phase 0 — do not include a step for a script that does not exist):

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/quality-guard.yml.md`. Do not edit it inline here; if it changes, change it in the template.

Show the user which steps were included and which were omitted because the
corresponding script does not exist, so they can confirm it is correct:

```
CI Quality Guard generated with these steps:
  ✓ Install, Lint, Build (always)
  <✓/✗> Type check
  <✓/✗> Unit & integration tests
  <✓/✗> Sanitization tests
  <✓/✗> E2E tests (+ browser installation)

Is this correct, or is a step missing/extra? [yes / add: <step> / remove: <step>]
```

**PAUSE — Wait for user response.**

---

## PHASE 3 — Automated Security Review

Ask if they want to activate a dedicated security review (separate from the
general AI reviewer in Phase 1 — this one is specific to SQLi, XSS, exposed
secrets, and vulnerable dependencies):

```
Do you want an automated Security Review on every PR (SQL injection, XSS,
exposed secrets, vulnerable dependencies)?

<if in Phase 1 chose option 3 (Claude), or GGA with claude provider>:
1. Yes, using Claude Code Security Review (same API key already configured)
<if in Phase 1 does NOT use Claude>:
1. Yes, using an equivalent action based on Gemini (requires
   GEMINI_API_KEY — can be the same secret from Phase 1 if already activated)
2. No, skip dedicated security review

Which one do you choose?
```

**Wait for user response.**

**If they chose Claude**, generate `.github/workflows/security-review.yml`:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/security-review.claude.yml.md`. Do not edit it inline here; if it changes, change it in the template.

**If they chose the Gemini equivalent**, generate
`.github/workflows/security-review.yml`:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/security-review.gemini.yml.md`. Do not edit it inline here; if it changes, change it in the template.

If they chose "No" in the question above, inform them they can add it later
with `/wf-settings` (once that command includes this module) or by
re-running this phase manually.

**PAUSE — Wait for confirmation before continuing.**

---

## PHASE 4 — Conventional commits (husky + commitlint)

Explain and confirm before installing anything:

```
I will configure local enforcement of conventional commits:
  - Allowed types: feat, fix, docs, style, refactor, test, chore
    (and their breaking change variants: feat!, fix!, etc.)
  - husky will block the commit if the message does not follow the format
  - PRs must come from a branch created from an up-to-date main/master

Do I install the dependencies and generate the config? [yes / no]
```

**Wait for user response.**

If confirmed, install:

```bash
npm install -D husky @commitlint/cli @commitlint/config-conventional
npx husky init
```

Generate `.commitlintrc.json`:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/commitlintrc.json.md`. Do not edit it inline here; if it changes, change it in the template.

Generate (or replace) `.husky/commit-msg`:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/husky-commit-msg.md`. Do not edit it inline here; if it changes, change it in the template.

```bash
chmod +x .husky/commit-msg
```

Inform:

```
Conventional commits configured. From now on, a commit with a type
outside the list (e.g. "wip: testing something") will fail locally before
reaching CI. Expected format: <type>[!][(scope)]: <description>

Valid examples:
  feat: add drag and drop to the task list
  fix(auth): fix token expiration
  feat!: change API response format (breaking change)
```

### Migrating the drift post-commit hook to Husky

> **Why**: `/wf-init` installs the drift detector in `.git/hooks/post-commit`, which
> is NOT versioned (every clone loses it). Now that Husky is configured, we migrate that
> hook to `.husky/post-commit` (versioned, survives clones and coexists with
> commitlint's `commit-msg`). This is the "Migrate post-commit hook to Husky" item
> from Block 6 in the master document.

Detect if the wf-init drift hook exists:

```bash
if [ -f .git/hooks/post-commit ]; then
  echo "Detected drift hook in .git/hooks/post-commit. Migrating to .husky/post-commit."
else
  echo "No previous drift hook found (did you run /wf-init?). Still creating .husky/post-commit for future commits."
fi
```

Generate `.husky/post-commit` from the template (single source):

> **Single source**: write `.husky/post-commit` VERBATIM from
> `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/husky-post-commit.tmpl.md`, which in turn injects the drift
> detection body from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/hook.post-commit.tmpl.md` (without the
> shebang, because Husky provides its own). Do not duplicate the drift logic here.

After creating `.husky/post-commit`, **delete the old hook to avoid double triggering**:

```bash
chmod +x .husky/post-commit
rm -f .git/hooks/post-commit    # prevents drift from being notified twice per commit
```

> **Compatibility note with /wf-refresh**: the drift detector now lives in
> `.husky/post-commit`. `/wf-refresh` and `/wf-init` must look for the hook in both
> locations (`.husky/post-commit` first, `.git/hooks/post-commit` as fallback) when
> verifying or regenerating the hook.

**PAUSE — Wait for confirmation before continuing.**

---

## PHASE 5 — release-please

Ask:

```
Do you want to activate release-please to generate automatic versions
and changelog from conventional commits? [yes / no]
```

**Wait for user response.**

If confirmed, generate `.github/workflows/release-please.yml`:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/release-please.yml.md`. Do not edit it inline here; if it changes, change it in the template.

Generate `release-please-config.json`:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/release-please-config.json.md`. Do not edit it inline here; if it changes, change it in the template.

Generate `.release-please-manifest.json` with the current detected version
from `package.json`:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/release-please-manifest.json.md`. Do not edit it inline here; if it changes, change it in the template.

Ask about the optional AI summary step (requires the same
`GEMINI_API_KEY` from previous phases, if configured):

```
Do you want the release PR to include an AI-generated natural language
summary (in addition to the automatic conventional commits changelog)?
Requires GEMINI_API_KEY. [yes / no]
```

If confirmed, add a second job to the same workflow:

> **Single source**: write this artifact VERBATIM from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/ai-summary-job.<provider>.yml.md` (according to `state.cicd.release_ai_provider`). Do not edit it inline here; if it changes, change it in the template.

> This action (`steven0351/publish-gemini-release-notes`) is third-party, not
> from Google or Anthropic — review its code before giving it access to a
> secret if you are concerned about the supply chain. It is optional and does not affect
> the actual release-please versioning mechanism if omitted.

**PAUSE — Wait for confirmation before continuing.**

---

## PHASE 6 — Branch rules and final commit

Inform the user of the rules (not all are automatable from this wizard — some
are repo settings on GitHub, not files):

```
Branching rules to configure manually in GitHub (Settings → Branches):
  - Protect main/master: require a PR before merging, require that
    Quality Guard checks pass green.
  - Feature branches must come from an up-to-date main/master — there is no
    way to enforce this from a GitHub Action, it is a team
    convention (document it in your AGENTS.md or README if needed).

Files I will write in this repo:
  <list of .github/workflows/*.yml generated in Phases 1-5>
  <if applicable> .commitlintrc.json, .husky/commit-msg
  <if applicable> .husky/post-commit (drift detector migrated from .git/hooks/)
  <if applicable> release-please-config.json, .release-please-manifest.json

Show me the full diff before committing — as always, I do not push.
```

**Wait for explicit user approval of the shown diff.** Only then:

```bash
git add .github/workflows/ .commitlintrc.json .husky/ release-please-config.json .release-please-manifest.json package.json package-lock.json 2>/dev/null
# (.husky/ includes commit-msg and, if migrated, post-commit)

git commit -m "chore: configure CI/CD pipeline (Block 6)

- Add CI Quality Guard workflow (lint, type-check, tests, build)
<if applicable> - Add AI PR review workflow (<Claude/Gemini>)
<if applicable> - Add dedicated security review workflow
<if applicable> - Add conventional commits enforcement (husky + commitlint)
<if applicable> - Add release-please for automated versioning and changelog

Powered by wf-cicd | AI Workflow Wizard"
```

**Does NOT `git push` — the user decides that.**

Confirm:

```
✓ CI/CD CONFIGURED
===================
<list of created files>

Pending on your side (not automatable from here):
  - Add the required secrets in GitHub (Settings → Secrets and
    variables → Actions): <list of applicable secrets>
  - Configure branch protection rules on main/master.
  <if Copilot> - Enable Copilot code review in Settings → Code review.

Commit: chore: configure CI/CD pipeline (Block 6)
  (pending push — use: git push)
```

---

## PHASE 6 — CD (Continuous Delivery)

> **Implemented**. CD is configured as an independent feature in `/wf-init` (Phase 4.7
> PART B) and in `/wf-settings` option 14. The wizard detects the project stack and generates
> the corresponding deploy workflow.

### How it works

CD automatically deploys your app to a VPS when a release PR is merged. It is
independent of CI — it can be activated without CI configured.

### Supported stacks

| Stack | Template |
|---|---|
| Node.js (PM2) | `deploy-pm2.node.yml.md` |
| Laravel/PHP (Nginx + PHP-FPM) | `deploy-nginx-phpfpm.laravel.yml.md` |
| Laravel/PHP (Apache + PHP-FPM) | `deploy-apache-phpfpm.laravel.yml.md` |
| Docker | `deploy-docker.yml.md` |

### Tag-based strategy (recommended)

```
feature PR → main           → NO deploy (only CI passes)
release PR → main + tag v*  → DEPLOY ✅
```

### Required secrets

| Workflow | Secrets |
|---|---|
| `deploy.yml` (VPS) | `SERVER_IP`, `SSH_USER`, `SSH_KEY` |

Secrets are configured manually in GitHub Settings → Secrets and variables → Actions.

Release Please creates the `v*` tag automatically when the release PR is merged. This prevents
double deployment (once by the feature PR, once by the release PR).

### Platforms to cover

| Platform | Approach |
|---|---|
| **GitHub Actions → any target** | `deploy.yml` workflow triggered on `push: tags: v*` |
| **AWS CodePipeline** | Source stage listening for `v*` tags (config in AWS, not in GH Actions) |
| **Vercel / Netlify / Railway** | Disable auto-deploy on the platform + GH Actions workflow calling their API/CLI on tag |

### ⚠️ Known edge case — External CD dependency

If the user already has an external pipeline that automatically deploys when merging to `main`,
activating the wizard's CD can cause **two deploys per feature** (one from the external pipeline,
another from the deploy.yml workflow). The wizard recommends tag-based and educates the user
about why, but cannot control external pipelines (AWS CodePipeline, etc.). This is documented
in the CD configuration without attempting to solve it automatically.

---
