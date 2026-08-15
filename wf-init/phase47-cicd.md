## PHASE 4.7 — CI and CD configuration — conditional

> **Gate**: only runs if `features.ci == true`, `features.cd == true`, or
> `features.release_please == true`. If not, skip to Phase 5.

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

FEATURES_CI=$(jq -r '.features.ci // false' .wizard-state.json)
FEATURES_CD=$(jq -r '.features.cd // false' .wizard-state.json)
FEATURES_RELEASE=$(jq -r '.features.release_please // false' .wizard-state.json)
if [ "$FEATURES_CI" != "true" ] && [ "$FEATURES_CD" != "true" ] && [ "$FEATURES_RELEASE" != "true" ]; then
  echo "PHASE 4.7 skipped — CI and CD not selected."
  wf_phase_done phase47-cicd phase5
  echo "ℹ Next phase: phase5"
  cat "$WF_DIR/phase5.md"
  exit 0
fi
```

> This phase ONLY collects decisions and saves them in `state.ci` and `state.cd`.
> File **generation** is done by the Builder in Phase 6 (to staging).
> Don't write files here.

### Precondition: read state + detect GitHub

```bash
# Does the repo have a GitHub remote? (graceful degradation if not)
git remote -v 2>/dev/null | grep -q github.com && echo "github" || echo "no-github"
```

Save the result in `state.ci.github_remote` (`true`/`false`). **If there is NO GitHub
remote**: inform that you'll still generate the workflow files and local hook
(which doesn't depend on GitHub), but that the secrets and branch protection steps will remain
pending until you push the repo to GitHub. **Don't stop the wizard because of this.**

---

### PART A — CI (only if features.ci == true)

#### Mode 1 — Full CI (features.ci == true)

Present the exact same questions as `cicd` protocol PHASE 1-5 (single source of
option text). Collect in `state.ci`:

1. **AI reviewer** (`cicd` protocol PHASE 1) → `state.ci.ai_reviewer` ∈
   `{gga, copilot, claude, gemini, none}` (recommended: **gga**).

   Try the structured input tool with all 5 options. If the tool is unavailable or doesn't
   support 5, display the `cicd` protocol PHASE 1 options as plain text and
   wait for typed response. Parse the user's choice (1, 2, 3, 4, or 5).

   - If `gga`: ask `state.ci.gga_provider` (claude/gemini/codex/opencode/ollama/...)
     and `state.ci.gga_modes` ⊆ `{local, ci}` (recommended: both).
2. **Dedicated security review** (`cicd` protocol PHASE 3) → `state.ci.security_review`
   (`false` | `claude` | `gemini`).
3. **Conventional commits** (`cicd` protocol PHASE 4) → `state.ci.conventional_commits`
   (bool, recommended `true`). Includes migration of drift hook to Husky.
4. **release-please** (`cicd` protocol PHASE 5) → `state.ci.release_please` (bool) and, if yes,
    `state.ci.release_ai_summary` (bool, optional AI summary for the release PR).
    - If yes → ask `state.ci.release_ai_provider` ∈ `{gemini, claude, openai}`.
      If GGA is configured with a provider (`state.ci.gga_provider`), use that same one
      as default.

> The Quality Guard (`cicd` protocol PHASE 2) is **mandatory** — not asked; the Builder
> always generates it, conditioned on the actual `package.json` scripts (`state.testing` +
> discovery). It doesn't need user input beyond what's already collected.

**Additional question — E2E in CI** (only if `state.testing.layers` includes e2e):

```
Include E2E in the CI Quality Guard?

  test:e2e runs in CI with Playwright headless. It can extend
  the pipeline (2-10min extra). If not, it's skipped in CI
  but still runs locally with npm run test:e2e.

  [yes / no]  (recommended default: no)
```

Save in `state.ci.e2e_in_ci`.

#### Mode 2 — Release-please only (features.release_please == true, without full CI)

In this mode, **only** conventional commits + Husky + release-please are configured.
Without Quality Guard, without AI review, without security review.

Ask:

```
Configuring release-please standalone (automatic versioning in PRs):

────────────────────────────────────────────────────────────
1. Conventional commits
   Husky + commitlint in the commit-msg hook. Required for
   release-please to detect changes and calculate the version.

2. release-please
   GitHub Actions workflow that runs on PRs and creates a
   release PR automatically.

3. AI summary for the release PR (optional)
   AI summary in the release PR body. If you choose yes,
   I'll ask which provider to use (Gemini, Claude, or OpenAI)
   and tell you which secret to configure in GitHub.
────────────────────────────────────────────────────────────
```

Collect:
- `state.ci.conventional_commits = true` (always)
- `state.ci.release_please = true` (always)
- `state.ci.release_ai_summary` (bool, optional)
- If `release_ai_summary == true`: ask `state.ci.release_ai_provider` ∈ `{gemini, claude, openai}`
- `state.ci.ai_reviewer = none`
- `state.ci.security_review = false`
- `state.ci.e2e_in_ci = false` (not applicable)

---

### PART B — CD (only if features.cd == true)

> CD is **independent** of CI. CD can be enabled without CI, and vice versa.
> The only dependency is with release-please: if the chosen trigger is
> tag-based, release-please is needed to generate `v*` tags.

#### Stack detection

Auto-detect the project stack to know which deploy template to generate:

```bash
# Is it Laravel?
HAS_LARAVEL=false
[ -f composer.json ] && grep -q '"laravel/framework"' composer.json && HAS_LARAVEL=true

# Does it have package.json (frontend assets)?
HAS_NODE=false
[ -f package.json ] && HAS_NODE=true

# Determine stack
if [ "$HAS_LARAVEL" = true ] && [ "$HAS_NODE" = true ]; then
  STACK="laravel_node"
elif [ "$HAS_LARAVEL" = true ]; then
  STACK="laravel"
else
  STACK="node_pure"
fi
```

Show the user what was detected:

```
Detected stack: <Laravel + Node / Laravel / Node pure>
Correct? [yes / correct]
```

If the user corrects it, save the chosen value in `state.cd.stack_detected`.

#### CD questions

```
Do you want to configure automatic deploy to a server?

  Generates a GitHub Actions workflow that deploys your app
  to a VPS via SSH when a release is created or when you push
  to main (depending on your choice).

  [yes / no]
```

If **no**: `state.cd.enabled = false`. Skip to phase closing.

If **yes**, ask in order:

**1. Deploy trigger:**

```
When does the deploy run?

  1. On merge of a v* tag (recommended if you use release-please)
  2. On push to main (every merge deploys)

  [1 / 2]
```

- If **tag** is chosen and release-please is OFF → inform:
  ```
  To use tags you need release-please to generate them
  automatically. Should I enable it too? [yes / no]
  ```
  If yes: set `state.ci.release_please = true`,
  `state.ci.conventional_commits = true`, and continue.
  If no: the trigger will be changed to push to main (no tags without release-please).

- If **push to main** is chosen: no restrictions.

Save in `state.cd.trigger` ∈ `{tag, push_main}`.

**2. Deploy platform:**

```
Where do you deploy?

  1. VPS (GitHub Actions + SSH)
  Skip — I handle it manually

  [1 / skip]
```

If **skip** is chosen: `state.cd.platform = 'skip'`. No workflow is generated.

**3. Server runtime** (only if VPS):

```
What do you use on the server to run the app?

  Detected stack: <stack>
  <Node pure>:    1. PM2
                  2. Docker Compose
  <Laravel>:      1. Nginx + PHP-FPM
                  2. Apache + PHP-FPM
                  3. Docker Compose

  [1 / 2 / 3]
```

Save in `state.cd.vps_runtime` ∈ `{pm2, nginx_php_fpm, apache_php_fpm, docker}`.

**4. Deploy path:**

```
App path on the server:
  (default: /var/www/<project-name>/current)

  [enter to accept / enter custom path]
```

Save in `state.cd.deploy_path`.

**5. Secrets:**

Inform the user which secrets need to be configured in GitHub:

```
CD pipeline generated. Add these secrets to your repo:

  SERVER_IP   — Server IP
  SSH_USER    — SSH user
  SSH_KEY     — SSH private key (without passphrase)

On your server make sure you have:
  <Node + PM2>:       Node.js, PM2, git
  <Laravel + Nginx>:  PHP 8.x, Composer, Nginx, Supervisor, git
  <Laravel + Apache>: PHP 8.x, Composer, Apache (mod_php or PHP-FPM), git
  <Docker>:           Docker, Docker Compose, git
```

---

### PAUSE

**PAUSE — ask the CI and CD questions (all at once or one by one) and wait for the responses.**

---

> **⛔ STOP HERE — do not execute anything else.**
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json`:
> - `ci` (all CI decisions + `github_remote`)
> - `cd` (all CD decisions)
> - `features.ci`, `features.cd`, `features.release_please` (toggles)
> Mark `wf_phase_done phase47-cicd phase5`.
> Tell the user: *"CI/CD configured. Reply **continue** so I can assemble the artifacts (Builder → staging on disk, not in memory)."*
> Wait for the response. Only when they confirm, run in bash:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Normalize cd.enabled / cd.platform based on the deploy platform answer (P1-12)
FEATURES_CD=$(jq -r '.features.cd // false' .wizard-state.json)
if [ "$FEATURES_CD" = "true" ]; then
  VPS_RUNTIME=$(jq -r '.cd.vps_runtime // empty' .wizard-state.json)
  if [ -n "$VPS_RUNTIME" ]; then
    wf_state_set '.cd.enabled' 'true'
    wf_state_set '.cd.platform' '"vps"'
  else
    wf_state_set '.cd.enabled' 'false'
    wf_state_set '.cd.platform' '"skip"'
  fi
else
  wf_state_set '.cd.enabled' 'false'
  wf_state_set '.cd.platform' '"skip"'
fi

wf_phase_done phase47-cicd phase5
echo "ℹ Next phase: phase5"
cat "$WF_DIR/phase5.md"
```
