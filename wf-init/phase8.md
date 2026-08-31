## PHASE 8 — Promote staging and commit

Only run because the user explicitly approved in Phase 7.

> writing is **deterministic**: promotes STAGING (`.wizard-staging/`) to
> its final destinations. There is no "writing generated content from memory" — the content
> is already on disk.

### 8.1 Promote staging files

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Add trap for staging cleanup on INTERRUPTION only (not normal EXIT)
# Use absolute /bin/rm so cleanup works even if PATH is corrupted
STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' .wizard-state.json)
PHASE8_INTERRUPTED=0
trap 'PHASE8_INTERRUPTED=1; echo "Phase 8 interrupted - cleaning up staging"; /bin/rm -rf "$STAGING"; /bin/rm -f .wizard-state.json.tmp; exit 1' INT TERM

# Active IDEs (used to gate IDE-specific artifacts below)
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)

# Create universal directories (not IDE-specific; those are created on demand by the copy loop below).
# .claude/skills is created ONLY when claude-code is an active IDE — otherwise the directory
# would appear empty in projects that do not use Claude Code.
mkdir -p .agents/protocols
if echo "$IDES" | grep -q "claude-code"; then
  mkdir -p .claude/skills
fi

# Copy the entire staging tree to the project root, preserving relative paths
# Use rsync for robust copy (handles nested dirs, perms, symlinks, timestamps)
rsync -a "$STAGING/" ./
# Note: run from a staging whose root mirrors the project root.

# ═══════════════════════════════════════════════════════════════
# MANDATORY: Verify ALL generated files were promoted from staging
# ═══════════════════════════════════════════════════════════════
# Check every file in build_plan.generated_files exists in project root
PROMOTE_FAILED=0
for f in $(jq -r '.build_plan.generated_files[].path // empty' .wizard-state.json 2>/dev/null); do
  if [ -n "$f" ] && [ ! -f "$f" ]; then
    echo "ERROR: Promoted file missing: $f" >&2
    PROMOTE_FAILED=1
  fi
done
if [ "$PROMOTE_FAILED" -ne 0 ]; then
  echo "ERROR: One or more files failed to promote from .wizard-staging/" >&2
  echo "       Staging dir: $STAGING" >&2
  echo "       Run 'ls -la $STAGING/' to debug" >&2
  exit 1
fi
echo "✓ All $(jq -r '.build_plan.generated_files | length' .wizard-state.json) generated files verified in project root"

# The hook needs execute permission
[ -f .git/hooks/post-commit ] && chmod +x .git/hooks/post-commit

# Reinsert Windsurf/Devin legacy path bridge into IDE rules files (safety net)
# Re-read active IDEs in case this block runs in a fresh shell
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  WF_RULE_FILE="$WF_DIR/temp-files/AGENTS.md"
  if [ -f "$WF_RULE_FILE" ]; then
    # Target both Windsurf and Devin rules files
    for TARGET in ".windsurf/rules/project.md" ".devin/rules/project.md"; do
      if [ ! -f "$TARGET" ]; then
        mkdir -p "$(dirname "$TARGET")"
        printf '# Project Rules\n\n' > "$TARGET"
      fi
      # Check if the rule is already present
      if ! grep -q "Gentle AI — Legacy Path Bridge" "$TARGET"; then
        # Insert the rule BEFORE the first '# ' heading (or at the top when
        # the file has none): it must stay outside the satellite's own
        # "Windsurf Rules" section and below any frontmatter, with one blank
        # line separating it from the content above and below.
        HEADING_LINE=$(grep -n '^# ' "$TARGET" | head -1 | cut -d: -f1)
        if [ -z "$HEADING_LINE" ]; then
          HEADING_LINE=1
        fi
        {
          if [ "$HEADING_LINE" -gt 1 ]; then
            head -n $((HEADING_LINE - 1)) "$TARGET"
            printf '\n'
          fi
          cat "$WF_RULE_FILE"
          # temp-files/AGENTS.md ships without a trailing newline; terminate
          # its last line, then leave one blank line before the heading below.
          if [ -n "$(tail -c1 "$WF_RULE_FILE")" ]; then printf '\n'; fi
          printf '\n'
          tail -n +"$HEADING_LINE" "$TARGET"
        } > "$TARGET.tmp"
        mv "$TARGET.tmp" "$TARGET"
      fi
      # Verify
      if grep -q "Gentle AI — Legacy Path Bridge" "$TARGET"; then
        echo "8.1 OK — Legacy path bridge present in $TARGET"
      else
        echo "8.1 ERROR — Legacy path bridge MISSING from $TARGET after reinsert." >&2
        exit 1
      fi
    done
  fi
fi

# Recompute managed files after in-place edits (AGENTS.md bridge reinsert)
# Use Python helper (recompute-managed.py) to avoid fragile NUL-delimited bash loop (Bug 1).
# The helper computes SHA256 via hashlib (stdlib), writes atomically with validation (Bug 3).
python3 "$WF_DIR/lib/recompute-managed.py" --state .wizard-state.json --in-place
echo "8.1 OK — managed files recomputed"


# Validate the AGENTS.md wf-version footer — NEVER accept "latest" or an unresolved placeholder.
# /wf-refresh Phase -1 compares local vs remote with STRICT equality; a non-semver value like
# "latest" would block every refresh forever (0.6.4-beta.1 != latest → UPGRADE REQUIRED).
# sed extraction is portable on BSD (macOS) and GNU (Linux) — `grep -oP` is GNU-only.
WF_FOOTER_VER=$(sed -n 's/.*wf-version: \([^ |]*\).*/\1/p' AGENTS.md | tail -1)
if ! printf '%s' "$WF_FOOTER_VER" | grep -qE '^v?[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$'; then
  echo "8.1 ERROR — AGENTS.md wf-version footer is not a concrete semver: '$WF_FOOTER_VER'." >&2
  echo "        Expected a concrete wizard version (e.g. v0.6.4-beta.1), never 'latest'." >&2
  echo "        Fix the Builder so it writes the EXACT wizard_version from .wizard-state.json." >&2
  exit 1
fi
echo "8.1 OK — AGENTS.md wf-version footer is a concrete semver: $WF_FOOTER_VER"

# Cross-check against the state (normalized: strip a leading v for the comparison)
WF_STATE_VER=$(jq -r '.wizard_version // ""' .wizard-state.json | sed 's/^v//')
WF_FOOTER_NORM=$(printf '%s' "$WF_FOOTER_VER" | sed 's/^v//')
if [ -n "$WF_STATE_VER" ] && [ "$WF_FOOTER_NORM" != "$WF_STATE_VER" ]; then
  echo "8.1 WARNING — AGENTS.md wf-version ($WF_FOOTER_VER) differs from state wizard_version ($WF_STATE_VER)." >&2
fi
```

### 8.1b CI/CD activation (only what requires running commands)

CI/CD files were already copied from staging. Some pieces need an
activation command (run AFTER the files exist):

```bash
# Conventional commits: initialize Husky if configured (core.hooksPath → .husky)
if [ "$(jq -r '.ci.conventional_commits' .wizard-state.json)" = "true" ]; then
  # Install husky as devDependency FIRST so it persists in package.json/package-lock.json
  # (npx husky init adds "prepare": "husky" but does NOT install the package)
  if command -v npm >/dev/null 2>&1; then
    npm install --save-dev husky
  fi
  command -v npx >/dev/null 2>&1 && npx husky init 2>/dev/null || true
  # Migrate the drift hook into Husky: when the builder ran on a project WITHOUT
  # .husky/ it wrote .git/hooks/post-commit (builder-heavy.py B8). After
  # `npx husky init` core.hooksPath points to .husky, so the old hook would be
  # silently ignored. Only migrate when Husky actually initialized.
  if [ -d .husky ] && [ -f .git/hooks/post-commit ] && [ ! -f .husky/post-commit ]; then
    mv .git/hooks/post-commit .husky/post-commit
  fi
  [ -f .husky/commit-msg ] && chmod +x .husky/commit-msg
  [ -f .husky/post-commit ] && chmod +x .husky/post-commit
  # migrate drift hook to Husky: delete the old one to avoid double firing
  [ -f .husky/post-commit ] && rm -f .git/hooks/post-commit

  # Field report B5: `npx husky init` drops a factory pre-commit (`npm test`).
  # With watch-mode test scripts ("test": "vitest" — no run/--run flag) every
  # git commit hangs until killed. GGA-local already wrote its own pre-commit
  # from staging; otherwise replace ONLY the untouched factory sample with an
  # inert hook. A pre-existing user hook is never clobbered — it is reported.
  if [ -f .husky/pre-commit ] && ! grep -q "gga run" .husky/pre-commit 2>/dev/null; then
    # Bug 2 fix: grep -qx matches exact line without trailing semicolon from tr
    if grep -qx 'npm test' .husky/pre-commit 2>/dev/null; then
      printf '%s\n' \
        '# Intentionally inert — enable real pre-commit checks deliberately.' \
        '# The wizard replaced Husky'"'"'s factory "npm test": with watch-mode test' \
        '# scripts (vitest without "run") every commit would hang until killed.' \
        '# Safe example once you decide the tradeoff:' \
        '# npx vitest related --run $(git diff --cached --name-only --diff-filter=ACMR)' \
        > .husky/pre-commit
      chmod +x .husky/pre-commit
      echo "8.1b — factory .husky/pre-commit (npm test) replaced with an inert hook (watch-mode hang risk)."
    elif [ -n "$(grep -vE '^\s*(#|$)' .husky/pre-commit 2>/dev/null | head -1)" ]; then
      echo "8.1b WARNING — .husky/pre-commit holds a non-factory script; left untouched." >&2
      echo "            Verify it terminates (no watch mode) or every commit will hang." >&2
    fi
  fi
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
STACK_KEY=$(jq -r '.discovery.stack.stack_key // .discovery.stack_key // "unknown"' .wizard-state.json)
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
            echo "8.1c — installing vitest + testing-library..."
            if npm install --save-dev vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom @testing-library/dom jsdom @vitest/ui @vitest/coverage-v8 @vitejs/plugin-react; then
              echo "8.1c OK — vitest + testing-library installed"
            else
              echo "8.1c WARNING — npm install failed (exit $?). Check package.json and network." >&2
            fi
          fi
          # Check for e2e layer
          if jq -e '.testing.layers[] | select(. == "e2e")' .wizard-state.json >/dev/null 2>&1; then
            echo "8.1c — installing @playwright/test..."
            if npm install --save-dev @playwright/test; then
              echo "8.1c OK — @playwright/test installed"
            else
              echo "8.1c WARNING — npm install failed (exit $?)." >&2
            fi
            echo "8.1c — installing Playwright chromium..."
            if npx playwright install --with-deps chromium; then
              echo "8.1c OK — Playwright chromium installed"
            else
              echo "8.1c WARNING — Playwright chromium install failed (exit $?). If e2e tests need browsers later, run: npx playwright install chromium" >&2
            fi
          fi
        fi
        # commitlint for conventional commits (needed by Husky commit-msg hook)
        if [ "$HAS_CONVENTIONAL" = "true" ]; then
          echo "8.1c — installing commitlint..."
          if npm install --save-dev commitlint; then
            echo "8.1c OK — commitlint installed"
          else
            echo "8.1c WARNING — npm install failed (exit $?)." >&2
          fi
        fi
        ;;
      php-*|laravel|symfony)
        # PHP stacks: composer require for phpunit
        if [ "$HAS_TESTING" -gt 0 ]; then
          echo "8.1c — installing phpunit..."
          if composer require --dev phpunit/phpunit; then
            echo "8.1c OK — phpunit installed"
          else
            echo "8.1c WARNING — composer require failed (exit $?)." >&2
          fi
        fi
        ;;
      # Add more stacks as needed
    esac
  fi

# Generate test dummy for Node if unit tests are enabled but NO TEST FILES exist.
# Field report B9: the original check tested ONE hardcoded path, contradicting
# this comment and creating dummy files in projects that already had tests
# elsewhere. Glob the whole tree (minus node_modules) first.
# Fix #18: Use detected test convention from discovery (state.discovery.test_dir or fallback)
if [[ "$STACK_KEY" == node-* || "$STACK_KEY" == *-react || "$STACK_KEY" == *-vue || "$STACK_KEY" == *-nextjs || "$STACK_KEY" == *-node ]]; then
  if jq -e '.testing.layers[] | select(. == "unit" or . == "integration")' .wizard-state.json >/dev/null 2>&1; then
    EXISTING_TESTS=$(find . -path ./node_modules -prune -o -type f \( -name '*.test.*' -o -name '*.spec.*' \) -print 2>/dev/null | head -1)
    if [ -z "$EXISTING_TESTS" ]; then
      # Use detected test directory convention from discovery, fallback to src/__tests__/
      TEST_DIR=$(jq -r '.discovery.test_dir // "src/__tests__"' .wizard-state.json)
      TEST_FILE="${TEST_DIR}/example.test.ts"
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
    test_command: "npm run test:coverage"  # ← sdd-verify runs {test_command} --coverage (Step 5d); use the coverage script so the report is real — npm swallows a bare --coverage flag
    build_command: "npm run build"         # ← sdd-verify runs this
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
if [ -f openspec/config.yaml ]; then
  UNIT=$(jq -r '.testing.layers | index("unit") != null' .wizard-state.json)
  INTEGRATION=$(jq -r '.testing.layers | index("integration") != null' .wizard-state.json)
  E2E=$(jq -r '.testing.layers | index("e2e") != null' .wizard-state.json)
  if [ "$UNIT" = "true" ] && [ "$E2E" = "true" ]; then FRAMEWORK="Vitest + Playwright"
  elif [ "$E2E" = "true" ]; then FRAMEWORK="Playwright"
  else FRAMEWORK="Vitest"; fi
  COVERAGE=$(jq -r '.testing.coverage_threshold != null' .wizard-state.json)
  COVERAGE_THRESHOLD=$(jq -r '.testing.coverage_threshold // null' .wizard-state.json)
else
  echo "8.1d skipped — no openspec/config.yaml (engram backend or /sdd-init not run)."
fi
```

Apply the edits with `yq` (same tool Phase 4.6 already uses for `strict_tdd`) — atomic,
idempotent, preserves every other key byte-for-byte. `yq` creates any missing parent keys in the
canonical location, so this also works when `/sdd-init` wrote a file without a top-level
`testing:`/`rules:` block.

**If `yq` is unavailable** (install failed or no package manager): do NOT skip this step and
do NOT tell the user to update the file by hand. Apply the same edits with your `edit` tool on
`openspec/config.yaml` — changing ONLY the allowed leaf fields (Wizard-Allowed Field Edits),
preserving every other line byte-for-byte, and creating missing parent keys
(`testing.runner`, `testing.layers.<layer>`, `rules.verify`) only when the file lacks them:

| Value | Apply if |
|---|---|
| `testing.runner.framework = "$FRAMEWORK"` | always |
| `testing.layers.unit.available = true` + `testing.layers.unit.tool = "vitest"` | unit or integration active |
| `testing.layers.integration.available = true` + `testing.layers.integration.tool = "vitest"` | integration active |
| `testing.layers.e2e.available = true` + `testing.layers.e2e.tool = "playwright"` | e2e active |
| `testing.coverage.available = true` + `testing.coverage.command = "npm run test:coverage"` + `rules.verify.coverage_threshold = $COVERAGE_THRESHOLD` | coverage activated |
| `rules.apply.test_command = "npm test"` + `rules.verify.test_command = "npm test"` + `rules.verify.build_command = "npm run build"` | always when testing configured |
| `rules.verify.test_command = "npm run test:coverage"` **instead of** `"npm test"` | coverage activated — npm swallows a bare `--coverage` flag (`npm test --coverage` runs WITHOUT coverage), so the test_command must be a script that already enables it for sdd-verify's `{test_command} --coverage` (strict-tdd-verify Step 5d) to produce a real report |

With `yq` available, apply the edits atomically in a single bash subshell (variables resolved + used
in same scope):

```bash
if [ -f openspec/config.yaml ]; then
  # 1. Resolve values from state
  UNIT=$(jq -r '.testing.layers | index("unit") != null' .wizard-state.json)
  INTEGRATION=$(jq -r '.testing.layers | index("integration") != null' .wizard-state.json)
  E2E=$(jq -r '.testing.layers | index("e2e") != null' .wizard-state.json)
  if [ "$UNIT" = "true" ] && [ "$E2E" = "true" ]; then FRAMEWORK="Vitest + Playwright"
  elif [ "$E2E" = "true" ]; then FRAMEWORK="Playwright"
  else FRAMEWORK="Vitest"; fi
  COVERAGE=$(jq -r '.testing.coverage_threshold != null' .wizard-state.json)
  COVERAGE_THRESHOLD=$(jq -r '.testing.coverage_threshold // null' .wizard-state.json)

  # 2. Ensure Go mikefarah/yq is available (pip3's kislyuk/yq does NOT support `eval -i`)
  if ! command -v yq &>/dev/null || ! yq --version 2>/dev/null | grep -q "mikefarah"; then
    if command -v yq &>/dev/null && yq --version 2>/dev/null | grep -q "kislyuk"; then
      echo "8.1d WARNING — detected Python yq wrapper (kislyuk); it does not support 'eval -i'." >&2
    fi

    YQ_INSTALL_DIR="${HOME}/.local/bin"
    mkdir -p "$YQ_INSTALL_DIR"

    case "$(uname -s)-$(uname -m)" in
      Linux-x86_64)     YQ_BINARY="yq_linux_amd64" ;;
      Linux-aarch64|Linux-arm64) YQ_BINARY="yq_linux_arm64" ;;
      Darwin-x86_64)    YQ_BINARY="yq_darwin_amd64" ;;
      Darwin-arm64)     YQ_BINARY="yq_darwin_arm64" ;;
      *)
        echo "8.1d ERROR — unsupported platform for automatic yq install ($(uname -s)-$(uname -m))." >&2
        echo "        Install Go yq from https://github.com/mikefarah/yq and re-run this step." >&2
        exit 1
        ;;
    esac

    echo "8.1d INFO — installing Go yq (${YQ_BINARY}) to ${YQ_INSTALL_DIR}..."
    if command -v curl &>/dev/null; then
      curl -fsSL "https://github.com/mikefarah/yq/releases/latest/download/${YQ_BINARY}" -o "$YQ_INSTALL_DIR/yq"
    elif command -v wget &>/dev/null; then
      wget -q "https://github.com/mikefarah/yq/releases/latest/download/${YQ_BINARY}" -O "$YQ_INSTALL_DIR/yq"
    else
      echo "8.1d ERROR — curl or wget is required to install yq." >&2
      exit 1
    fi
    chmod +x "$YQ_INSTALL_DIR/yq"
    export PATH="$YQ_INSTALL_DIR:$PATH"

    # Verify yq is actually available (use full path as fallback)
    if ! command -v yq &>/dev/null; then
      if [ -x "$YQ_INSTALL_DIR/yq" ]; then
        YQ_CMD="$YQ_INSTALL_DIR/yq"
      else
        echo "8.1d ERROR — yq install to ${YQ_INSTALL_DIR} failed or the directory is not in PATH." >&2
        exit 1
      fi
    else
      YQ_CMD="yq"
    fi
  fi

  # 3. Apply edits with yq (variables UNIT, E2E, FRAMEWORK now available in same subshell)
  if [ -n "$YQ_CMD" ]; then
    # 3a. Scalar-in-path guard (field report B1): `yq eval '.a.b = v'` over a
    # path whose parent holds a SCALAR is a silent no-op — neither error nor
    # write. Some /sdd-init runs leave `runner: vitest` (string) or
    # `coverage: true` (bool) behind; setting their sub-keys then loses data.
    # Delete any non-map node first so the canonical maps below are recreated.
    for LEAF_PATH in .testing.runner .testing.coverage \
                     .testing.layers.unit .testing.layers.integration .testing.layers.e2e; do
      KIND=$($YQ_CMD eval "${LEAF_PATH} | type" openspec/config.yaml)
      if [ -n "$KIND" ] && [ "$KIND" != "!!map" ] && [ "$KIND" != "!!null" ]; then
        echo "8.1d INFO — ${LEAF_PATH} held a scalar (${KIND}); normalized to canonical map (expected for /sdd-init output)."
        $YQ_CMD eval "del(${LEAF_PATH})" -i openspec/config.yaml
      fi
    done

    # Runner: sdd-apply detects it from the testing section
    $YQ_CMD eval ".testing.runner.framework = \"$FRAMEWORK\"" -i openspec/config.yaml

    # Layers capability cache: sdd-apply/verify uses available + tool per layer
    if [ "$UNIT" = "true" ] || [ "$INTEGRATION" = "true" ]; then
      $YQ_CMD eval '.testing.layers.unit.available = true' -i openspec/config.yaml
      $YQ_CMD eval '.testing.layers.unit.tool = "vitest"' -i openspec/config.yaml
    fi
    if [ "$INTEGRATION" = "true" ]; then
      $YQ_CMD eval '.testing.layers.integration.available = true' -i openspec/config.yaml
      $YQ_CMD eval '.testing.layers.integration.tool = "vitest"' -i openspec/config.yaml
    fi
    if [ "$E2E" = "true" ]; then
      $YQ_CMD eval '.testing.layers.e2e.available = true' -i openspec/config.yaml
      $YQ_CMD eval '.testing.layers.e2e.tool = "playwright"' -i openspec/config.yaml
    fi

    # Coverage: capability cache + sdd-verify threshold (only if activated)
    if [ "$COVERAGE" = "true" ]; then
      $YQ_CMD eval '.testing.coverage.available = true' -i openspec/config.yaml
      $YQ_CMD eval '.testing.coverage.command = "npm run test:coverage"' -i openspec/config.yaml
      $YQ_CMD eval ".rules.verify.coverage_threshold = $COVERAGE_THRESHOLD" -i openspec/config.yaml
    fi

    # Command overrides: always when testing configured
    $YQ_CMD eval '.rules.apply.test_command = "npm test"' -i openspec/config.yaml
    # npm swallows bare --coverage: `npm test --coverage` runs WITHOUT coverage.
    # sdd-verify runs {test_command} --coverage (strict-tdd Step 5d), so when coverage
    # is activated the verify command must be the script that already enables it.
    if [ "$COVERAGE" = "true" ]; then
      $YQ_CMD eval '.rules.verify.test_command = "npm run test:coverage"' -i openspec/config.yaml
    else
      $YQ_CMD eval '.rules.verify.test_command = "npm test"' -i openspec/config.yaml
    fi
    $YQ_CMD eval '.rules.verify.build_command = "npm run build"' -i openspec/config.yaml
  else
    echo "8.1d ERROR — yq is not available and could not be installed." >&2
    echo "        Apply the openspec edits with your edit tool using the table above," >&2
    echo "        then re-run this step. Do NOT continue without applying them." >&2
    exit 1
  fi
fi
```

Never copy from `templates/protocols/sdd/config.yaml.tmpl.md` — it is a field reference, not a
file to stamp. Leave `strict_tdd` alone — Phase 4.6 owns that field. `yq` writes to the canonical
nesting (`rules.verify.*`, `testing.*`) even when the real file was written by `/sdd-init` at a
different nesting — that is correct: gentle-ai's consumers read the canonical location. If you
find the file already carries the same value at a non-canonical nesting (older `/sdd-init`
output), leave the old key in place and confirm the canonical one is now set; if in doubt, ask
the user.

Verify EVERY edit landed — assert each written field reads back with its exact value before
declaring OK (field report B1: two writes were lost silently and only a per-field readback
would have caught them):

```bash
if [ -f openspec/config.yaml ]; then
  ASSERT_FAIL=0
  _assert_eq() {
    GOT=$($YQ_CMD eval "$1" openspec/config.yaml)
    if [ "$GOT" != "$2" ]; then
      echo "8.1d ERROR — $1 => '$GOT' (expected '$2') — the write did NOT land." >&2
      ASSERT_FAIL=1
    fi
  }
  _assert_eq '.testing.runner.framework' "$FRAMEWORK"
  if [ "$UNIT" = "true" ]; then
    _assert_eq '.testing.layers.unit.available' "true"
    _assert_eq '.testing.layers.unit.tool' "vitest"
  fi
  if [ "$INTEGRATION" = "true" ]; then
    _assert_eq '.testing.layers.integration.available' "true"
    _assert_eq '.testing.layers.integration.tool' "vitest"
  fi
  if [ "$E2E" = "true" ]; then
    _assert_eq '.testing.layers.e2e.available' "true"
    _assert_eq '.testing.layers.e2e.tool' "playwright"
  fi
  if [ "$COVERAGE" = "true" ]; then
    _assert_eq '.testing.coverage.available' "true"
    _assert_eq '.testing.coverage.command' "npm run test:coverage"
    _assert_eq '.rules.verify.coverage_threshold' "$COVERAGE_THRESHOLD"
    _assert_eq '.rules.verify.test_command' "npm run test:coverage"
  else
    _assert_eq '.rules.verify.test_command' "npm test"
  fi
  _assert_eq '.rules.apply.test_command' "npm test"
  _assert_eq '.rules.verify.build_command' "npm run build"
  if [ "$ASSERT_FAIL" -ne 0 ]; then
    echo "8.1d ERROR — one or more canonical fields missing after write; do not continue." >&2
    exit 1
  fi
  echo "8.1d OK — all canonical fields verified"
fi
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
IDE's MCP settings. The exact per-IDE format is in `$WF_DIR/templates/protocols/testing/playwright-mcp.settings.tmpl.md` (Claude:
`.claude/settings.json` or `.claude/settings.local.json` to avoid committing it; Cursor:
`.cursor/mcp.json`; Windsurf: `.windsurf/mcp.json` — **Windsurf only supports global scope at `~/.codeium/windsurf/mcp_config.json`, not project-level**). If the format isn't clear for any active IDE,
tell the user which files to create and with what content, and wait for confirmation before writing.
`@playwright/mcp` needs no API key — it is reasonable to commit it so the whole team has it.

### 8.2 Update .gitignore

```bash
# Re-read active IDEs in case this block runs in a fresh shell
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)

# Idempotent appends: skip lines already present so re-running /wf-init
# does not duplicate .gitignore entries (same guard as /wf-refresh R6).
_gi_add() {
  local line="$1"
  if ! grep -qxF "$line" .gitignore 2>/dev/null; then
    if [ -f .gitignore ] && [ "$(tail -c1 .gitignore | wc -l)" -eq 0 ]; then
      echo >> .gitignore
    fi
    printf '%s\n' "$line" >> .gitignore
  fi
}

_gi_add '.wf-status'
_gi_add '.wizard-state.json'
_gi_add '.wizard-state.json.tmp'
_gi_add '.wizard-staging/'

# Exceptions for satellites that must be versioned (only generated ones, single quotes)
_gi_add '!.agents/'
if echo "$IDES" | grep -q "cursor"; then
  _gi_add '!.cursor/'
fi
if echo "$IDES" | grep -qE "windsurf|devin"; then
  _gi_add '!.windsurf/'
  _gi_add '!.devin/'
fi
if echo "$IDES" | grep -q "kiro"; then
  _gi_add '!.kiro/'
fi
if echo "$IDES" | grep -q "claude-code"; then
  _gi_add '!.claude/'
fi
if echo "$IDES" | grep -q "codex"; then
  _gi_add '!.codex/'
fi
if echo "$IDES" | grep -q "gemini-cli"; then
  _gi_add '!.gemini/'
  _gi_add '!GEMINI.md'
fi
if echo "$IDES" | grep -q "opencode"; then
  _gi_add '!.opencode/'
fi
if echo "$IDES" | grep -q "vscode-copilot"; then
  _gi_add '!.github/copilot-instructions.md'
  _gi_add '!.github/prompts/'
fi
```

### 8.3 Write .wizard-managed-files.json

After all files are promoted, write a manifest of wizard-managed files for `/wf-refresh` to use during future refreshes.

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Recompute managed files from the actual promoted files
# Use Python helper (recompute-managed.py) to avoid fragile NUL-delimited bash loop (Bug 1).
# The helper computes SHA256 via hashlib (stdlib), writes atomically with validation (Bug 3).
python3 "$WF_DIR/lib/recompute-managed.py" --state .wizard-state.json --in-place
echo "8.3 OK — managed files recomputed"

# Read back the recomputed generated_files for the manifest
GENERATED_FILES=$(jq -c '.build_plan.generated_files' .wizard-state.json)

WIZARD_VERSION=$(jq -r '.wizard_version // "0.7.1-beta.1"' .wizard-state.json)
GENERATED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jq -n --arg version "$WIZARD_VERSION" --arg generated_at "$GENERATED_AT" --argjson files "$GENERATED_FILES" \
   '{wizard_version: $version, generated_at: $generated_at, files: $files}' > .wizard-managed-files.json

# Add to .gitignore (so it's not committed)
if ! grep -q "\.wizard-managed-files\.json" .gitignore 2>/dev/null; then
  echo ".wizard-managed-files.json" >> .gitignore
fi
```

---

### 8.4 Force track satellites/protocols and commit

```bash
# Re-read active IDEs in case this block runs in a fresh shell
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)

# Refresh gentle-ai's skill registry so its own Skill Resolver Protocol picks up
# this project's wf-* skills (wf-orchestrator, wf-ladder, wf-sdd-trigger, wf-tdd,
# wf-onboard, wf-worktree, wf-settings)
# right away, instead of waiting for the next commit's post-commit hook.
# Fix #20: Only run for IDEs that use .atl/skill-registry.md (Claude Code, OpenCode, Cursor, Kiro, Codex)
# Windsurf/Devin discover project skills natively from filesystem — no-op for them.
SKILL_REGISTRY_IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null | grep -E 'claude-code|opencode|cursor|kiro|codex' || true)
if [ -n "$SKILL_REGISTRY_IDES" ] && command -v gentle-ai &>/dev/null; then
  echo "8.4 — refreshing gentle-ai skill registry..."
  if gentle-ai skill-registry refresh --quiet; then
    echo "8.4 OK — gentle-ai skill registry refreshed"
  else
    echo "8.4 WARNING — gentle-ai skill-registry refresh failed (exit $?). Run manually later if needed." >&2
  fi
fi

# Fix: Re-apply Windsurf sdd-new.md after any gentle-ai sync that may have overwritten it
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  SDD_BACKEND=$(jq -r '.sdd.backend // "hybrid"' .wizard-state.json)
  PROJECT_NAME=$(jq -r '.answers.project_name' .wizard-state.json)
  WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
  SDD_PATH="$SDD_BACKEND"
  [ "$SDD_BACKEND" = "hybrid" ] && SDD_PATH="openspec"
  mkdir -p .windsurf/workflows
  cp "$WF_DIR/temp-files/sdd-new.md" .windsurf/workflows/sdd-new.md
  if [ "$SDD_BACKEND" = "engram" ]; then
    sed -i.bak "s|{{sdd.backend}}/changes/<name>/proposal.md|Engram memory:|g" .windsurf/workflows/sdd-new.md
  else
    sed -i.bak "s|{{sdd.backend}}/changes/|$SDD_PATH/changes/|g" .windsurf/workflows/sdd-new.md
  fi
  sed -i.bak "s/{{sdd.backend}}/$SDD_BACKEND/g" .windsurf/workflows/sdd-new.md
  sed -i.bak "s|{project}|$PROJECT_NAME|g" .windsurf/workflows/sdd-new.md
  rm -f .windsurf/workflows/sdd-new.md.bak
  echo "8.4 OK — Windsurf sdd-new.md re-applied (in case gentle-ai sync overwrote it)"
fi

git add AGENTS.md
[ -f GEMINI.md ] && git add GEMINI.md
[ -f ANTIGRAVITY.md ] && git add ANTIGRAVITY.md
git add -f .agents/ 2>/dev/null || true
# CLAUDE.md and .claude/ exist only when claude-code was selected (see 8.1)
if echo "$IDES" | grep -q "claude-code"; then
  git add CLAUDE.md 2>/dev/null || true
  git add -f .claude/ 2>/dev/null || true
fi
git add vitest.config.ts 2>/dev/null || true
git add playwright.config.ts 2>/dev/null || true
git add -f e2e/ 2>/dev/null || true
git add src/test/setup.ts 2>/dev/null || true
git add -f .cursor/ 2>/dev/null || true
git add -f .windsurf/ 2>/dev/null || true
# .devin/rules/ holds local IDE rules (not wizard artifacts) — never force-add
# the whole .devin/ tree. Commit only the generated skills directory.
git add -f .devin/skills/ 2>/dev/null || true
git add -f .kiro/ 2>/dev/null || true
git add -f .codex/ 2>/dev/null || true
git add -f .opencode/ 2>/dev/null || true
# gemini-cli (when selected): builder emits .gemini/skills/<skill>/SKILL.md (see builder.md B7)
git add -f .gemini/ 2>/dev/null || true
# PR Agent config staged by the builder (builder-heavy.py) — commit it too
[ -f .pr_agent.toml ] && git add -f .pr_agent.toml 2>/dev/null || true
git add -f .github/copilot-instructions.md .github/prompts/ 2>/dev/null || true
# CI/CD (Block 6): workflows, conventional commits, husky, release-please, .gga
git add -f .github/workflows/ 2>/dev/null || true
# CRITICAL: do NOT suppress errors here — these files MUST be committed (Bug 1 fix)
git add -f .husky/ .commitlintrc.json .gga release-please-config.json .release-please-manifest.json
[ -f package.json ] && git add package.json 2>/dev/null || true
[ -f package-lock.json ] && git add package-lock.json 2>/dev/null || true
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
- Add protocols as IDE native skills + universal .agents/skills + flat files (.agents/protocols)
- Add satellite files for configured IDEs
- Add project commands: wf-ladder, wf-tdd, wf-orchestrator, wf-sdd-trigger
- Add project commands: wf-onboard, wf-worktree, wf-settings
- Add post-commit hook for drift detection
- Add CI/CD (Block 6): AI review, quality guard, conventional commits
- Update .gitignore for AI workflow files

Powered by wf-init v$WF_VER | gentle-ai $GA_VER"

# Post-commit verification: ensure all managed files from build_plan.generated_files were committed (Bug 1 fix)
COMMITTED_FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null || git ls-files)
MISSING=0
for f in $(jq -r '.build_plan.generated_files[].path' .wizard-state.json 2>/dev/null); do
  if [ -n "$f" ] && ! echo "$COMMITTED_FILES" | grep -qx "$f"; then
    echo "ERROR: $f was NOT committed!" >&2
    MISSING=1
  fi
done
if [ "$MISSING" -eq 1 ]; then
  echo "ERROR: One or more wizard-managed files missing from commit. Aborting." >&2
  exit 1
fi
echo "8.4 OK — all wizard-managed files verified in commit"
```

**Does NOT `git push` — that's for the user to decide.**

### 8.5 Post-init instructions

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

### 8.6 Closing

```bash
# Clean up temporary staging (only if not already cleaned up by interruption trap)
if [ "${PHASE8_INTERRUPTED:-0}" -eq 0 ]; then
  STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' .wizard-state.json)
  rm -rf "$STAGING"
  
  # ═══════════════════════════════════════════════════════════════
  # MANDATORY: Verify staging directory was actually removed
  # ═══════════════════════════════════════════════════════════════
  if [ -d "$STAGING" ]; then
    echo "ERROR: Staging directory $STAGING still exists after cleanup!" >&2
    echo "       This indicates the rm -rf failed or directory was recreated." >&2
    exit 1
  fi
  echo "✓ Staging directory $STAGING successfully removed"
fi
```

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Validate state before final phase transition (phase-aware validation)
wf_phase_done phase8 done
```

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
