## PHASE 8 — Promote staging and commit

Only run because the user explicitly approved in Phase 7.

> writing is **deterministic**: promotes STAGING (`.wizard-staging/`) to
> its final destinations. There is no "writing generated content from memory" — the content
> is already on disk.

### 8.1 Promote staging files

```bash
STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' .wizard-state.json)

# Create universal directories (not IDE-specific; those are created on demand by the copy loop below)
mkdir -p .agents/protocols .claude/skills

# Copy the entire staging tree to the project root, preserving relative paths
( cd "$STAGING" && find . -type f -print0 | while IFS= read -r -d '' f; do
    dest="../${f#./}"; mkdir -p "$(dirname "$dest")"; cp "$f" "$dest";
  done )
# Note: run from a staging whose root mirrors the project root.

# The hook needs execute permission
[ -f .git/hooks/post-commit ] && chmod +x .git/hooks/post-commit

# Reinsert Windsurf rule into AGENTS.md (safety net — may have been lost in the copy from staging)
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  WF_RULE_FILE="$WF_DIR/temp-files/AGENTS.md"
  if [ -f "$WF_RULE_FILE" ] && [ -f AGENTS.md ]; then
    # Check if the rule is already present
    if ! grep -q "Gentle AI — Legacy Path Bridge" AGENTS.md; then
      # Extract the Windsurf rule (everything after the title line)
      WINDSURF_RULE=$(tail -n +2 "$WF_RULE_FILE")
      # Insert after the first line (after "# AGENTS.md — workflow-wizard")
      sed -i '1a\n'"$WINDSURF_RULE" AGENTS.md
    fi
  fi
fi
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

### 8.1d SDD config.yaml targeted edit (openspec/hybrid backend only)

**Gate**: only if `openspec/config.yaml` exists (created by gentle-ai's `/sdd-init` in
Phase 4.5). Skip entirely if the backend is engram-only — there is no config.yaml to edit.

The wizard NEVER regenerates or stamps `openspec/config.yaml` — it is the exclusive artifact
of `/sdd-init` (BLOCK RULE, protocol `sdd`, "Wizard-Allowed Field Edits"). This step performs
the targeted leaf-field edit deferred from Phase 4.6b: it writes the activated testing
configuration into the EXISTING file using gentle-ai's canonical schema — the exact shape its
SDD skills read. Do NOT invent new top-level keys (`configured`, `planned`, `extras`,
`conventions`, `checks_before_done`): no gentle-ai consumer reads them, and they would just
accumulate dead data in the file.

**Canonical schema (gentle-ai source of truth — `_shared/openspec-convention.md`,
`docs/openspec-config.md`, the repo's own `openspec/config.yaml`):**

```yaml
strict_tdd: true              # top-level — Phase 4.6 owns this, leave it alone
rules:
  apply:
    guidelines: [...]         # phase rules; leave as-is
    tdd: false                # leave as-is
    test_command: "npm test"  # ← sdd-apply strict-tdd reads rules.apply.test_command (override)
  verify:
    test_command: ""          # ← sdd-verify runs this
    build_command: ""         # ← sdd-verify runs this
    coverage_threshold: 0     # ← sdd-verify enforces this (docs/openspec-config.md)
testing:
  strict_tdd: true            # Phase 4.6 owns this, leave it alone
  detected: "YYYY-MM-DD"      # leave as-is
  runner:
    command: "npm test"       # ← sdd-apply detects the runner here (testing section)
    framework: "Vitest"
  layers:
    unit:        {available: true, tool: "vitest"}       # ← capability cache
    integration: {available: true, tool: "vitest"}
    e2e:         {available: true, tool: "playwright"}
  coverage:
    available: true           # ← capability cache
    command: "npm run test:coverage"
  quality:
    linter: {...}             # leave as-is — detected by /sdd-init
    type_checker: {...}
    formatter: {...}
```

Map the wizard's activated extras onto THESE fields (not onto invented ones):
`testing.runner.{command,framework}`, `testing.layers.<layer>.{available,tool}`,
`testing.coverage.{available,command}` (coverage extra), `rules.verify.coverage_threshold`
(coverage extra), `rules.apply.test_command` + `rules.verify.{test_command,build_command}`
(always). `visual_regression` and `page_object_model` stay in `.wizard-state.json` only —
gentle-ai has no field for them; they surface in the generated `playwright.config.ts` / `e2e/pages/`.

Resolve the values from state (flat schema — `testing.coverage_threshold`, not `testing.extras.*`):

```bash
if [ ! -f openspec/config.yaml ]; then
  echo "8.1d skipped — no openspec/config.yaml (engram backend or /sdd-init not run)."
  exit 0
fi
UNIT=$(jq -r '.testing.layers | index("unit") != null' .wizard-state.json)
INTEGRATION=$(jq -r '.testing.layers | index("integration") != null' .wizard-state.json)
E2E=$(jq -r '.testing.layers | index("e2e") != null' .wizard-state.json)
if [ "$UNIT" = "true" ] && [ "$E2E" = "true" ]; then FRAMEWORK="Vitest + Playwright"
elif [ "$E2E" = "true" ]; then FRAMEWORK="Playwright"
else FRAMEWORK="Vitest"; fi
COVERAGE=$(jq -r '.testing.coverage_threshold != null' .wizard-state.json)
COVERAGE_THRESHOLD=$(jq -r '.testing.coverage_threshold // null' .wizard-state.json)
```

Apply the edits with `yq` (same tool Phase 4.6 already uses for `strict_tdd`) — atomic,
idempotent, preserves every other key byte-for-byte. `yq` creates any missing parent keys in the
canonical location, so this also works when `/sdd-init` wrote a file without a top-level
`testing:`/`rules:` block:

```bash
# 1. Runner (sdd-apply detects it from the testing section)
yq eval ".testing.runner.framework = \"$FRAMEWORK\"" -i openspec/config.yaml

# 2. Layers capability cache (sdd-apply/verify: available + tool per layer)
if [ "$UNIT" = "true" ] || [ "$INTEGRATION" = "true" ]; then
  yq eval '.testing.layers.unit.available = true' -i openspec/config.yaml
  yq eval '.testing.layers.unit.tool = "vitest"' -i openspec/config.yaml
fi
if [ "$INTEGRATION" = "true" ]; then
  yq eval '.testing.layers.integration.available = true' -i openspec/config.yaml
  yq eval '.testing.layers.integration.tool = "vitest"' -i openspec/config.yaml
fi
if [ "$E2E" = "true" ]; then
  yq eval '.testing.layers.e2e.available = true' -i openspec/config.yaml
  yq eval '.testing.layers.e2e.tool = "playwright"' -i openspec/config.yaml
fi

# 3. Coverage (extra 1 — only if activated): capability cache + sdd-verify threshold
if [ "$COVERAGE" = "true" ]; then
  yq eval '.testing.coverage.available = true' -i openspec/config.yaml
  yq eval '.testing.coverage.command = "npm run test:coverage"' -i openspec/config.yaml
  yq eval ".rules.verify.coverage_threshold = $COVERAGE_THRESHOLD" -i openspec/config.yaml
fi

# 4. Command overrides (always when testing configured)
yq eval '.rules.apply.test_command = "npm test"' -i openspec/config.yaml
yq eval '.rules.verify.test_command = "npm test"' -i openspec/config.yaml
yq eval '.rules.verify.build_command = "npm run build"' -i openspec/config.yaml
```

Never copy from `templates/protocols/sdd/config.yaml.tmpl.md` — it is a field reference, not a
file to stamp. Leave `strict_tdd` alone — Phase 4.6 owns that field. `yq` writes to the canonical
nesting (`rules.verify.*`, `testing.*`) even when the real file was written by `/sdd-init` at a
different nesting — that is correct: gentle-ai's consumers read the canonical location. If you
find the file already carries the same value at a non-canonical nesting (older `/sdd-init`
output), leave the old key in place and confirm the canonical one is now set; if in doubt, ask
the user.

Verify the edit landed — if the coverage extra was activated, the file must now contain the
threshold under `rules.verify`:

```bash
grep -n "coverage_threshold" openspec/config.yaml && echo "8.1d OK — rules.verify.coverage_threshold present"
```

### 8.1e Testing scripts + Playwright MCP registration (project files, only if testing configured)

The builder only stages NEW files. `package.json` and the IDE MCP settings are real project
files — they are modified here, after the configs exist (same content as `test-scripts.tmpl.md` /
`e2e-scripts.tmpl.md`, but applied directly to the project's package.json):

```bash
HAS_TESTING=$(jq -r '.testing.layers[]?' .wizard-state.json 2>/dev/null | wc -l)
if [ "$HAS_TESTING" -gt 0 ]; then
  # unit/integration scripts
  if jq -e '.testing.layers[] | select(. == "unit" or . == "integration")' .wizard-state.json >/dev/null 2>&1; then
    npm pkg set scripts.test="vitest" scripts.test:ui="vitest --ui" scripts.test:coverage="vitest run --coverage" 2>/dev/null || true
  fi
  # e2e scripts
  if jq -e '.testing.layers[] | select(. == "e2e")' .wizard-state.json >/dev/null 2>&1; then
    npm pkg set scripts.test:e2e="playwright test" scripts.test:e2e:ui="playwright test --ui" scripts.test:e2e:report="playwright show-report" 2>/dev/null || true
  fi
fi
```

**Playwright MCP** (only if the e2e layer is active): register `@playwright/mcp` in the active
IDE's MCP settings. The exact per-IDE format is in `playwright-mcp.settings.tmpl.md` (Claude:
`.claude/settings.json` or `.claude/settings.local.json` to avoid committing it; Cursor:
`.cursor/mcp.json`; Windsurf: `.windsurf/mcp.json`). If the format isn't clear for any active IDE,
tell the user which files to create and with what content, and wait for confirmation before writing.
`@playwright/mcp` needs no API key — it is reasonable to commit it so the whole team has it.

### 8.2 Update .gitignore

```bash
echo '.wf-status' >> .gitignore
echo '.wizard-state.json' >> .gitignore
echo '.wizard-staging/' >> .gitignore

# Exceptions for satellites that must be versioned (only generated ones, single quotes)
echo '!.cursor/' >> .gitignore        # if applicable
echo '!.windsurf/' >> .gitignore      # if applicable
echo '!.devin/' >> .gitignore         # if applicable
echo '!.kiro/' >> .gitignore          # if applicable
echo '!.github/copilot-instructions.md' >> .gitignore   # if applicable
```

### 8.3 Force track satellites/protocols and commit

```bash
# Refresh gentle-ai's skill registry so its own Skill Resolver Protocol picks up
# this project's wf-* skills (wf-orchestrator, wf-ladder, wf-sdd-trigger, wf-tdd,
# wf-sdd-config) right away, instead of waiting for the next commit's post-commit hook.
# Helps adapters whose orchestrator reads .atl/skill-registry.md before delegating (Claude
# Code, OpenCode, Cursor, Kiro, Codex). Harmless no-op for Windsurf/Devin — confirmed against
# gentle-ai's own source (internal/skillregistry/registry.go) that it never scans
# .windsurf/skills/ or .devin/skills/ at all; those two discover project skills natively from
# the filesystem instead, so running this command costs nothing but helps nothing for them.
command -v gentle-ai &>/dev/null && gentle-ai skill-registry refresh --quiet 2>/dev/null || true

git add AGENTS.md CLAUDE.md GEMINI.md 2>/dev/null || true
git add -f .agents/ 2>/dev/null || true
git add -f .claude/ 2>/dev/null || true
git add -f .cursor/ 2>/dev/null || true
git add -f .windsurf/ 2>/dev/null || true
git add -f .devin/ 2>/dev/null || true
git add -f .kiro/ 2>/dev/null || true
git add -f .opencode/ 2>/dev/null || true
git add -f .github/copilot-instructions.md .github/prompts/ 2>/dev/null || true
# CI/CD (Block 6): workflows, conventional commits, husky, release-please, .gga
git add -f .github/workflows/ 2>/dev/null || true
git add -f .husky/ .commitlintrc.json .gga release-please-config.json .release-please-manifest.json 2>/dev/null || true
# SDD artifacts (openspec/): created by /sdd-init in Phase 4.5 + targeted edit in 8.1d
git add openspec/ 2>/dev/null || true
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
- Add project-specific commands (wf-ladder, wf-onboard)
- Add maintenance commands (wf-refresh, wf-worktree, wf-settings)
- Add post-commit hook for drift detection
- Add CI/CD (Block 6): AI review, quality guard, conventional commits
- Update .gitignore for AI workflow files

Powered by wf-init v$WF_VER | gentle-ai $GA_VER"
```

**Does NOT `git push` — that's for the user to decide.**

### 8.3b Post-init instructions

Show the user:

```
✓ AI Workflow Wizard initialized successfully!

Next steps:

1. Open AGENTS.md and review the generated content.

2. If you want to add custom rules or policies to AGENTS.md:
   
   Wrap them with protection markers so /wf-refresh will never touch them:

   <!-- WF: DO NOT REGENERATE -->
   ## Your Custom Section
   Your content here
   <!-- /WF: DO NOT REGENERATE -->

3. Commit your custom changes (if any):
   git add AGENTS.md
   git commit -m "feat: add team-specific rules and policies"

4. Open the project in your preferred AI IDE.
   The agent will read AGENTS.md automatically on the next session.

5. To validate: ask the agent "read AGENTS.md and tell me its main sections".

6. For your first task, describe it in natural language.
   The agent (via `wf-orchestrator`/`wf-sdd-trigger`) will classify it as `wf-no-sdd` (direct),
   or confirmed `wf-force-sdd` route.

7. When the project evolves (new dependencies, new test frameworks, etc.),
   run /wf-refresh to keep AGENTS.md synchronized.
```

<if state.cd.missing_secrets is non-empty>:
  ```
  ⚠ MISSING SECRETS — these workflows will fail until you configure them:
  <for each entry in state.cd.missing_secrets>:
    • {{workflow}} requires the secret {{secret_name}}
      → github.com/<owner>/<repo>/settings/secrets/actions → "New repository secret"
  Without these secrets, the workflow runs but the AI reviewer fails with "API key not valid".
  ```

<if state.ci.release_please == true>:
  ```
  ⚠ RELEASE-PLEASE: the workflow already declares the necessary permissions, but the repo ALSO
  must allow Actions to create PRs. Go to:
    Settings → Actions → General → Workflow permissions
  and enable "Allow GitHub Actions to create and approve pull requests".
  Without that, release-please fails with "Resource not accessible by integration".
  ```

<if state.gentle_ai.warning_incomplete == true>:
  ```
  ⚠ REMINDER: gentle-ai was not installed. The workflow is incomplete.
  Install with: brew install gentle-ai && gentle-ai install
  Then run /wf-refresh to complete the configuration.
  ```

---

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
