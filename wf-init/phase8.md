## PHASE 8 — Promote staging and commit

Only run because the user explicitly approved in Phase 7.

> writing is **deterministic**: promotes STAGING (`.wizard-staging/`) to
> its final destinations. There is no "writing generated content from memory" — the content
> is already on disk.

### 8.1 Promote staging files

```bash
STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' .wizard-state.json)

# Create necessary destination directories (satellites, protocols, commands)
mkdir -p .github .cursor/rules .windsurf/rules .kiro/steering
mkdir -p .agents/protocols .claude/skills
mkdir -p .claude/commands .cursor/commands .windsurf/workflows .opencode/commands .github/prompts

# Copy the entire staging tree to the project root, preserving relative paths
( cd "$STAGING" && find . -type f -print0 | while IFS= read -r -d '' f; do
    dest="../${f#./}"; mkdir -p "$(dirname "$dest")"; cp "$f" "$dest";
  done )
# Note: run from a staging whose root mirrors the project root.

# The hook needs execute permission
[ -f .git/hooks/post-commit ] && chmod +x .git/hooks/post-commit
```

### 8.1b CI/CD activation (only what requires running commands)

CI/CD files were already copied from staging. Some pieces need an
activation command (run AFTER the files exist):

```bash
# Conventional commits: initialize Husky if configured (core.hooksPath → .husky)
if [ "$(jq -r '.ci.conventional_commits' .wizard-state.json)" = "true" ]; then
  command -v npx >/dev/null 2>&1 && npx husky init 2>/dev/null || true
  [ -f .husky/commit-msg ] && chmod +x .husky/commit-msg
  [ -f .husky/post-commit ] && chmod +x .husky/post-commit
  # migrate drift hook to Husky: delete the old one to avoid double firing
  [ -f .husky/post-commit ] && rm -f .git/hooks/post-commit
fi

# GGA local mode: the pre-commit hook (uses .gga + AGENTS.md, already written)
if echo "$(jq -r '.ci.gga_modes[]?' .wizard-state.json)" | grep -q local; then
  CONVCOMMITS=$(jq -r '.ci.conventional_commits' .wizard-state.json)
  if [ "$CONVCOMMITS" = "true" ]; then
    # Husky active (core.hooksPath=.husky): GGA runs via .husky/pre-commit (already written with
    # 'gga run'). Do NOT use 'gga install' — it would write to .git/hooks/ and get shadowed.
    [ -f .husky/pre-commit ] && chmod +x .husky/pre-commit
    echo "GGA local runs via .husky/pre-commit (gga run). 'gga install' is not used because Husky manages the hooks."
  else
    # Without Husky: 'gga install' writes .git/hooks/pre-commit and works.
    if command -v gga >/dev/null 2>&1; then
      gga install 2>/dev/null || echo "⚠ 'gga install' failed — install the hook manually with: gga install"
    else
      echo "⚠ binary 'gga' not found. Install with: gentle-ai install --component gga (or brew), then: gga install"
    fi
  fi
fi
```

### 8.1c Testing stack installation (stack-aware, only if testing configured)

Install testing dependencies and generate test dummy before commit. Husky hooks
will fail if these don't exist. This section is stack-aware: Node installs npm packages,
PHP would install composer packages, etc.

```bash
STACK_KEY=$(jq -r '.discovery.stack_key // "unknown"' .wizard-state.json)
HAS_TESTING=$(jq -r '.testing.layers[]?' .wizard-state.json 2>/dev/null | wc -l)
HAS_CONVENTIONAL=$(jq -r '.ci.conventional_commits // false' .wizard-state.json)

# Install dependencies by stack — only if testing or conventional commits are active
if [ "$HAS_TESTING" -gt 0 ] || [ "$HAS_CONVENTIONAL" = "true" ]; then
  case "$STACK_KEY" in
    node-*|*-react|*-vue|*-nextjs|*-node)
      # Node-based stacks: npm install for vitest, playwright, testing-library, commitlint
      if [ "$HAS_TESTING" -gt 0 ]; then
        # Check for unit/integration layers
        if jq -e '.testing.layers[] | select(. == "unit" or . == "integration")' .wizard-state.json >/dev/null 2>&1; then
          npm install --save-dev vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom @testing-library/dom jsdom @vitest/ui @vitest/coverage-v8 2>/dev/null || true
        fi
        # Check for e2e layer
        if jq -e '.testing.layers[] | select(. == "e2e")' .wizard-state.json >/dev/null 2>&1; then
          npm install --save-dev @playwright/test 2>/dev/null || true
        fi
      fi
      # commitlint for conventional commits (needed by Husky commit-msg hook)
      if [ "$HAS_CONVENTIONAL" = "true" ]; then
        npm install --save-dev commitlint 2>/dev/null || true
      fi
      ;;
    php-*|laravel|symfony)
      # PHP stacks: composer require for phpunit
      if [ "$HAS_TESTING" -gt 0 ]; then
        composer require --dev phpunit/phpunit 2>/dev/null || true
      fi
      ;;
    # Add more stacks as needed
  esac
fi

# Generate test dummy for Node if unit tests are enabled but no test files exist
if [[ "$STACK_KEY" == node-* || "$STACK_KEY" == *-react || "$STACK_KEY" == *-vue || "$STACK_KEY" == *-nextjs || "$STACK_KEY" == *-node ]]; then
  if jq -e '.testing.layers[] | select(. == "unit" or . == "integration")' .wizard-state.json >/dev/null 2>&1; then
    TEST_FILE="src/__tests__/example.test.ts"
    if [ ! -f "$TEST_FILE" ]; then
      mkdir -p "$(dirname "$TEST_FILE")"
      cat > "$TEST_FILE" << 'TESTEOF'
import { describe, it, expect } from 'vitest'

describe('Example test', () => {
  it('should pass', () => {
    expect(true).toBe(true)
  })
})
TESTEOF
      git add "$TEST_FILE"
    fi
  fi
fi
```

> Use heredocs for any file you manually rewrite (avoid variable
> expansion). The hook already comes VERBATIM from the template; don't edit it when copying.

### 8.2 Update .gitignore

```bash
echo '.wf-status' >> .gitignore
echo '.wizard-state.json' >> .gitignore
echo '.wizard-staging/' >> .gitignore

# Exceptions for satellites that must be versioned (only generated ones, single quotes)
echo '!.cursor/' >> .gitignore        # if applicable
echo '!.windsurf/' >> .gitignore      # if applicable
echo '!.kiro/' >> .gitignore          # if applicable
echo '!.github/copilot-instructions.md' >> .gitignore   # if applicable
```

### 8.3 Force track satellites/protocols and commit

```bash
git add AGENTS.md CLAUDE.md GEMINI.md 2>/dev/null || true
git add -f .agents/ 2>/dev/null || true
git add -f .claude/ 2>/dev/null || true
git add -f .cursor/ 2>/dev/null || true
git add -f .windsurf/ 2>/dev/null || true
git add -f .kiro/ 2>/dev/null || true
git add -f .opencode/ 2>/dev/null || true
git add -f .github/copilot-instructions.md .github/prompts/ 2>/dev/null || true
# CI/CD (Block 6): workflows, conventional commits, husky, release-please, .gga
git add -f .github/workflows/ 2>/dev/null || true
git add -f .husky/ .commitlintrc.json .gga release-please-config.json .release-please-manifest.json 2>/dev/null || true
git add .gitignore

WF_VER=$(jq -r '.wizard_version // "0.0.0"' .wizard-state.json)
GA_VER=$(jq -r '.gentle_ai.version // "unknown"' .wizard-state.json)
# IMPORTANT: if conventional commits is active, commitlint validates header <=100 and
# body-max-line-length <=100. Keep ALL lines of the message <=100 characters, or the
# wizard's own commit fails. (Rule in the workflow protocol.)
git commit -m "chore: initialize AI Workflow Wizard

- Add AGENTS.md router (thin) pointing to packaged protocols
- Add protocols as Claude skills and flat files (.agents/protocols)
- Add satellite files for configured IDEs
- Add project-specific commands (decision-ladder, sdd-lite, wf-onboard)
- Add maintenance commands (wf-refresh, wf-worktree, wf-settings)
- Add post-commit hook for drift detection
- Add CI/CD (Block 6): AI review, quality guard, conventional commits
- Update .gitignore for AI workflow files

Powered by wf-init v$WF_VER | gentle-ai $GA_VER"
```

**Does NOT `git push` — that's for the user to decide.**

### 8.4 Closing

```bash
# Limpieza del staging temporal
STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' .wizard-state.json)
rm -rf "$STAGING"
```

Mark `phases.phase8.status = done` and `phase_pointer = "done"` in `.wizard-state.json`.

```
✓ WIZARD COMPLETED
===================
Files created:
  <list of written files, from state.build_plan>

Commit: chore: initialize AI Workflow Wizard
  (push pending — use: git push)

Next steps:
  1. Open the project in your preferred AI IDE.
  2. Start a new session — the agent will read AGENTS.md automatically.
  3. To validate: ask the agent "read AGENTS.md and tell me its main sections".
  4. For your first SDD feature, describe the task in natural language.

<if state.cd.missing_secrets is non-empty>:
  ⚠ MISSING SECRETS — these workflows will fail until you configure them:
  <for each entry in state.cd.missing_secrets>:
    • {{workflow}} requires the secret {{secret_name}}
      → github.com/<owner>/<repo>/settings/secrets/actions → "New repository secret"
  Without these secrets, the workflow runs but the AI reviewer fails with "API key not valid".

<if state.ci.release_please == true>:
  ⚠ RELEASE-PLEASE: the workflow already declares the necessary permissions, but the repo ALSO
  must allow Actions to create PRs. Go to:
    Settings → Actions → General → Workflow permissions
  and enable "Allow GitHub Actions to create and approve pull requests".
  Without that, release-please fails with "Resource not accessible by integration".

<if state.gentle_ai.warning_incomplete == true>:
  ⚠ REMINDER: gentle-ai was not installed. The workflow is incomplete.
  Install with: brew install gentle-ai && gentle-ai install
  Then run /wf-refresh to complete the configuration.
```

---

## Implementation notes for the agent

- **Always use `which`** to detect binaries before assuming they are installed.
- **When writing files**, use heredocs (`cat > file << 'EOF'`) to avoid variable expansion.
- **For .gitignore with `!`**, use `echo '...' >> .gitignore` with single quotes (double quotes trigger history expansion in zsh).
- **If the user interrupts or says "stop"** in any phase, stop completely. Do not auto-complete phases.
- **Do not push** under any circumstances. The user decides when.
- **If `gentle-ai install` requires interaction** (agent list), inform before running it and wait for confirmation.
- **Wizard maintenance**: when adding a new command, update `EXPECTED_COMMANDS` (phase 2 and wf-refresh) and the monitored terms (phase 0). Source of truth against missing commands/silent incompatibility.
- **`git shortlog` without range hangs** in repos without commits: always use `git shortlog -sne HEAD < /dev/null`.
- **All wizard state lives in `.wizard-state.json`** — no phase depends on conversational memory; the process is resumable.
