# Protocol: CI/CD (pipeline + drift hook)

<!--
  SINGLE SOURCE of the CI/CD rules and templates. Consumed by wf-cicd.md (command) and
  the Builder/hook (phase6d). Source in inventory.md: wf-cicd.md (all, 42 items),
  phase6d 1-93, post-commit, phase6a 57-59 (Programmatic Checks), AI_DEV_WORKFLOW §10.
  The concrete artifacts (YAML/JSON/hook) are in variants/ and hook.post-commit.tmpl.md
  (VERBATIM from the source).
-->

## wf-cicd command rules

- Pause per phase; **never push**; the user approves before writing.
- Branch rules: configured **manually** in GitHub (the command lists what to do).

## wf-cicd phases (order)

0. Detect current CI/CD state.
1. **AI reviewer** (5 options): **GGA (recommended)** · Copilot (setting, no workflow) ·
   Claude (`variants/claude-review.yml.md`) · Gemini (`variants/gemini-review.yml.md`) ·
   none. Missing secret message if the secret is not set.
   - **GGA (Gentleman Guardian Angel)**: provider-agnostic, uses `AGENTS.md` as rules.
     Config: `variants/gga-config.tmpl.md` (.gga). Local mode: `gga init && gga install` (pre-commit
     hook). CI mode: `variants/gga-review.yml.md` (`gga run --pr-mode`). Binary via
     `gentle-ai install --component gga` or `brew install gentleman-programming/tap/gga`.
2. **quality-guard** (`variants/quality-guard.yml.md`) — conditional on present scripts.
3. **Dedicated security review** (optional): `variants/security-review.claude.yml.md` or
   `variants/security-review.gemini.yml.md` (with SAST prompt).
4. **Conventional commits**: husky + commitlint. `variants/commitlintrc.json.md`,
   `variants/husky-commit-msg.md` (remember `chmod +x`).
5. **release-please** (optional): `variants/release-please.yml.md`,
   `variants/release-please-config.json.md`, `variants/release-please-manifest.json.md`,
    + optional AI summary job (`variants/ai-summary-job.{gemini,claude,openai}.yml.md`). Note: third-party
    action → trust chain.
6. Final commit (no push).

## Post-commit hook (drift detector) — single source

- Body template: `hook.post-commit.tmpl.md` (VERBATIM phase6d 12-93). It is the ONLY
  source of the drift logic; the repo root `post-commit` is regenerated from here.
- Detects two drift categories and only **notifies** (never acts):
  - **AGENTS.md drift** (`REFRESH_FILES`) → suggests `/wf-refresh`.
  - **SDD drift** (`SDD_FILES`) → suggests `/sdd-init`.
- `openspec/config.yaml` **excluded** (it is the output of /sdd-init; avoids loop).
- Writes persistent `.wf-status` between sessions + macOS notification (osascript).

### Hook location: `.git/hooks/` vs `.husky/` (Block 6 migration)

- **By default** (`/wf-init` without CI/CD): the hook lives in `.git/hooks/post-commit` (NOT
  versioned; every clone loses it).
- **With conventional commits configured** (`/wf-cicd` PHASE 4): it **migrates** to
  `.husky/post-commit` (versioned, survives clones, coexists with `commit-msg`). Wrapper
  template: `husky-post-commit.tmpl.md`, which injects the body of `hook.post-commit.tmpl.md`
  (without shebang) — single source, no duplication of drift logic. When migrating, **delete**
  `.git/hooks/post-commit` to avoid double firing.
- **Rule for `/wf-init` and `/wf-refresh`**: when verifying or regenerating the hook, look in
  both locations — `.husky/post-commit` first, `.git/hooks/post-commit` as fallback.

## ⚠ CI/CD gotchas verified in real use (apply when generating)

1. **`npm ci` "lockfile out of sync"**: the `package-lock.json` is generated with the user's
   local npm/Node; the npm bundled with Node in CI may resolve peer-deps differently and
   `npm ci` fails even though the lock is valid locally. Fix in `quality-guard.yml`: use Node
   `state.discovery.node_engine` or 22 (NOT hardcoded 20), and **pin npm** with
   `npm install -g npm@{state.discovery.npm_major}` before `npm ci`.
2. **Installing GGA in CI**: NOT `curl -fsSL install.sh | bash` (the `install.sh` references
   `bin/gga` relative to its dir; via pipe there is no stable BASH_SOURCE → `cp: cannot stat`).
   Use `git clone --depth=1 ... /tmp/gga && echo "/tmp/gga/bin" >> $GITHUB_PATH`.
3. **GGA base branch in PR**: in PR, `actions/checkout` does not fetch the base branch as a local ref
   → GGA auto-detection fails. Set `PR_BASE_BRANCH` in `.gga` with
   `state.discovery.default_branch` and do `git fetch origin <base>` in the workflow.
4. **GGA local + Husky**: `gga install` writes `.git/hooks/pre-commit`, which Husky
   (`core.hooksPath=.husky`) IGNORES. With Husky active, run GGA via `.husky/pre-commit`
   (`gga run`), NOT `gga install`. Without Husky, `gga install` does work.
5. **Husky v9+**: hooks without shebang `#!/usr/bin/env sh` or `. .../_/husky.sh` (broken in v10).
6. **Commit messages ≤100 chars** (commitlint). See `workflow` protocol.
7. **Explicit `GITHUB_TOKEN` permissions**: since Oct-2023 the default token is
   read-only. EVERY workflow that **creates resources** must declare a `permissions:` block with
   least privilege, not depend on the default:
   - `release-please.yml` → `contents: write` + `pull-requests: write` (otherwise it fails with
     "Resource not accessible by integration"). Additionally, the repo needs *Settings → Actions →
     General → "Allow GitHub Actions to create and approve pull requests"* enabled (the wizard
     cannot touch this; notify the user).
    - `gemini-review.yml` / `security-review.yml` (Gemini/`Codium-ai/pr-agent`): the API key
      is passed as `GOOGLE_AI_STUDIO.GEMINI_API_KEY`. If the free tier exceeds 20 requests/day
      for `gemini-2.5-flash`, pr-agent fails with 429 (quota exceeded) in all its functions
      (`auto_review`, `auto_describe`, `auto_improve`). Fix: enable billing in Google
      AI Studio or wait for the daily quota reset.
    - Workflows that post comments/reviews on the PR (e.g., GGA, security review if commenting)
      → `pull-requests: write`.
    - `quality-guard.yml` only reads and runs tests → no extra permissions needed.
 8. **Deprecated Gemini models**: `gemini-1.5-flash` and `gemini-1.5-pro` were deprecated
    by Google. Do NOT use in any workflow. Current models: `gemini-2.5-flash`,
    `gemini-2.5-pro`, `gemini-2.0-flash`. Check available models with:
    `curl https://generativelanguage.googleapis.com/v1beta/models?key=$KEY`.
    - security-review (`pr-agent`): `CONFIG.MODEL: "gemini/gemini-2.5-flash"`
    - AI summary job: `models/gemini-2.5-flash:generateContent`

## Programmatic Checks in AGENTS.md

The `## Programmatic Checks` section lists the commands the agent runs before
declaring a task done (lint + build + test based on `state.testing`).
