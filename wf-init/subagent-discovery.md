# Sub-agent Discovery — executes phases 1-4

You are a project discovery agent. Your job is to run bash commands to analyze a project and save results directly to the target project's `.wizard-state.json`.

## Context you receive

- `PROJECT_PATH`: absolute path to the target project (e.g., `/home/user/my-project`)
- `WF_PATH`: absolute path to the downloaded phase directory (WF_DIR — contains `lib/` and phase files)
- `STATE_FILE`: absolute path to the state file (e.g., `/home/user/my-project/.wizard-state.json`)
- `WF_RAW`: `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`

**IMPORTANT**: The `task` tool does NOT interpolate environment variables. Use the literal `STATE_FILE` path (e.g., `/home/user/my-project/.wizard-state.json`) in all `wf_state_set` calls and when sourcing state-helpers.sh. Do NOT use `$WF_STATE` — it will be empty in the sub-agent's environment.

## Instructions

### 1. Initialize state helpers

```bash
# Set WF_STATE to the absolute path received in context
WF_STATE="{STATE_FILE}"
source "{WF_PATH}/lib/state-helpers.sh"
```

### 2. Discovery — bash commands (phase1.md)

Run in order and capture outputs:

```bash
# Root structure
ls -la "{PROJECT_PATH}"

# Package manifest
cat "{PROJECT_PATH}/package.json" 2>/dev/null || cat "{PROJECT_PATH}/composer.json" 2>/dev/null || cat "{PROJECT_PATH}/pyproject.toml" 2>/dev/null || cat "{PROJECT_PATH}/Cargo.toml" 2>/dev/null

# Previous workflow artifacts
ls "{PROJECT_PATH}/AGENTS.md" "{PROJECT_PATH}/CLAUDE.md" "{PROJECT_PATH}/GEMINI.md" 2>/dev/null
ls -d "{PROJECT_PATH}/.cursor" "{PROJECT_PATH}/.windsurf" "{PROJECT_PATH}/.devin" "{PROJECT_PATH}/.kiro" "{PROJECT_PATH}/openspec" 2>/dev/null
ls "{PROJECT_PATH}/.github/copilot-instructions.md" 2>/dev/null
ls "{PROJECT_PATH}/.git/hooks/post-commit" 2>/dev/null

# Recent Git log
git -C "{PROJECT_PATH}" log --oneline -10 2>/dev/null

# Project size
find "{PROJECT_PATH}" -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.php" 2>/dev/null | grep -v node_modules | grep -v ".git" | wc -l

# npm scripts (feeds the AGENTS.md Commands section — the Builder renders
# them from .discovery.commands; without it the section falls back to a
# generic re-detection)
# Detect package manager and emit "npm run X" / "pnpm X" / "yarn X"
node <<'NODEEOF'
const fs = require('fs');
const path = '{PROJECT_PATH}';
const pkg = JSON.parse(fs.readFileSync(path + '/package.json', 'utf8'));
const scripts = pkg.scripts || {};

// Detect package manager
let pm = 'npm';
if (pkg.packageManager) pm = pkg.packageManager.split('@')[0];
else if (fs.existsSync(path + '/pnpm-lock.yaml')) pm = 'pnpm';
else if (fs.existsSync(path + '/yarn.lock')) pm = 'yarn';

const prefix = pm === 'npm' ? 'npm run' : pm;
const cmds = Object.keys(scripts).map(s => `${prefix} ${s}`);
process.stdout.write(cmds.join('\n'));
NODEEOF
echo

# Root structure with purpose (one per line, feeds .discovery.conventions.structure)
# Output format: "folder/  # Purpose" — one entry per line for multiline tree
find "{PROJECT_PATH}" -maxdepth 1 -type d -not -name '.*' -not -path "{PROJECT_PATH}" 2>/dev/null | while read dir; do
  base=$(basename "$dir")
  case "$base" in
    src) echo "src/  # Source code";;
    components) echo "  components/  # UI components";;
    hooks) echo "  hooks/  # Custom hooks";;
    lib) echo "  lib/  # Utilities and helpers";;
    types) echo "  types/  # TypeScript definitions";;
    test|__tests__|tests) echo "  $base/  # Tests";;
    e2e) echo "e2e/  # Playwright E2E tests";;
    public) echo "public/  # Static assets";;
    *) echo "$base/";;
  esac
done

# Toolchain
node -e "process.stdout.write(require('{PROJECT_PATH}/package.json').engines?.node||'')" 2>/dev/null; echo
npm --version 2>/dev/null | cut -d. -f1
git -C "{PROJECT_PATH}" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##' \
  || git -C "{PROJECT_PATH}" remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p' \
  || echo "main"

# Committers
git -C "{PROJECT_PATH}" shortlog -sne HEAD < /dev/null 2>/dev/null | wc -l

# Existing CI/CD workflows
ls "{PROJECT_PATH}/.github/workflows/" 2>/dev/null | wc -l
```

### 3. Save discovery to state

Use `wf_state_set` to persist to `.wizard-state.json`:

```
.discovery.stack.primary        → "node" | "php" | "python" | "rust" | "other"
.discovery.stack.framework      → "react" | "next" | "laravel" | "express" | null
.discovery.stack.detected_from  → "package.json" | "composer.json" | etc.
.discovery.stack.stack_key   → normalized key (e.g. "node-react", "php-laravel")
.discovery.code_files           → number of code files
.discovery.git_commits          → number of commits
.discovery.committers           → number of unique committers
.discovery.ci_present           → true/false (if .github/workflows/ has files)
.discovery.node_engine          → detected Node version (or null)
.discovery.npm_major            → local npm major version (or null)
.discovery.default_branch       → default branch
.discovery.commands             → [npm script names] for node stacks | null (the Builder
                                  renders the AGENTS.md Commands section from this)
.discovery.prior_artifacts      → { agents_md: bool, claude_md: bool, satellites: [...], hook: bool }
```

### 4. Migration — missing commands (phase2.md)

For each IDE that has a directory in the project, check expected commands:

```bash
# Conditional by feature: wf-ladder (LADDER), wf-tdd (TDD && LAYERS),
# wf-orchestrator (ROUTING || LADDER || TDD), wf-sdd-trigger (ROUTING);
# wf-onboard, wf-worktree, wf-settings are always emitted.
EXPECTED_COMMANDS=(
  "wf-ladder"
  "wf-tdd"
  "wf-orchestrator"
  "wf-sdd-trigger"
  "wf-onboard"
  "wf-worktree"
  "wf-settings"
)
```

| IDE | Base path | Extension |
|---|---|---|
| claude-code | .claude/commands/ | .md |
| opencode | .opencode/commands/ | .md |
| cursor | .cursor/commands/ | .md |
| windsurf | .windsurf/workflows/ | .md |
| kiro | .kiro/steering/ | .md |
| vscode-copilot | .github/prompts/ | .prompt.md |
| codex | .codex/commands/ | .md |

Determine which IDEs are active:
- If `.claude/` exists → claude-code active
- If `.cursor/` exists → cursor active
- If `.windsurf/` OR `.devin/` exists → windsurf active (Windsurf and Devin are the same IDE, dual paths for compatibility)
- If `.kiro/` exists → kiro active
- If `.opencode/` exists → opencode active
- If `.codex/` exists → codex active
- If `.github/copilot-instructions.md` exists → vscode-copilot active

For each active IDE, check file by file whether each expected command exists:

```bash
# Build the missing_commands array
MISSING_COMMANDS=()

# IDE detection and command checking
for ide_dir in ".claude" ".cursor" ".windsurf" ".devin" ".kiro" ".opencode" ".codex"; do
  if [ -d "$ide_dir" ]; then
    case "$ide_dir" in
      ".claude") IDE="claude-code"; BASE=".claude/commands"; EXT=".md" ;;
      ".cursor") IDE="cursor"; BASE=".cursor/commands"; EXT=".md" ;;
      ".windsurf"|".devin") IDE="windsurf"; BASE=".windsurf/workflows"; EXT=".md" ;;
      ".kiro") IDE="kiro"; BASE=".kiro/steering"; EXT=".md" ;;
      ".opencode") IDE="opencode"; BASE=".opencode/commands"; EXT=".md" ;;
      ".codex") IDE="codex"; BASE=".codex/commands"; EXT=".md" ;;
    esac
    
    if [ -d "$BASE" ]; then
      for cmd in "${EXPECTED_COMMANDS[@]}"; do
        if [ ! -f "$BASE/$cmd$EXT" ]; then
          MISSING_COMMANDS+=("{\"ide\":\"$IDE\",\"command\":\"$cmd\"}")
        fi
      done
    fi
  fi
done

# Check vscode-copilot separately (different structure)
if [ -f ".github/copilot-instructions.md" ]; then
  IDE="vscode-copilot"
  BASE=".github/prompts"
  EXT=".prompt.md"
  for cmd in "${EXPECTED_COMMANDS[@]}"; do
    if [ ! -f "$BASE/$cmd$EXT" ]; then
      MISSING_COMMANDS+=("{\"ide\":\"$IDE\",\"command\":\"$cmd\"}")
    fi
  done
fi

# Save to state
if [ ${#MISSING_COMMANDS[@]} -gt 0 ]; then
  # Join array with commas (IFS method, portable across macOS/Linux)
  OLDIFS="$IFS"
  IFS=","
  MIGRATION_JSON="${MISSING_COMMANDS[*]}"
  IFS="$OLDIFS"
  # wf_state_set with jq --arg will safely parse the JSON array
  wf_state_set '.migration.missing_commands' "[$MIGRATION_JSON]"
else
  # Empty array
  wf_state_set '.migration.missing_commands' "[]"
fi
```

### 5. Greenfield vs legacy classification (phase3.md)

Analyze the signals:
- **Greenfield**: fewer than 5 commits, or almost all files from the same day, or package.json with no significant production dependencies
- **Legacy**: real commit history, production dependencies, established patterns in src/

Save:

```
.discovery.classification → "greenfield" | "legacy"
```

### 6. Reverse engineering — legacy only (phase4.md)

If legacy, read 2-3 representative files from `src/` to detect conventions:

```
.discovery.conventions.naming     → "camelCase" | "PascalCase" | "kebab-case" | "snake_case"
.discovery.conventions.components → observed component pattern
.discovery.conventions.imports    → "absolute" | "relative" | "alias"
.discovery.conventions.tests      → detected framework | "no tests"
.discovery.conventions.css        → "tailwind" | "css-modules" | "styled-components" | "plain"
.discovery.conventions.state      → "useState" | "zustand" | "redux" | "context" | "other"
.discovery.conventions.structure  → short tree of main folders + their purpose (one line each;
                                    feeds the AGENTS.md Project Structure section — without it
                                    the Builder falls back to the literal word "flat")
```

If greenfield, leave `.discovery.conventions = {}`.

## Final output

After saving everything to state, print this formatted report:

```
DISCOVERY REPORT
================
Detected stack: <stack>
Framework: <framework>
Code files: ~<N>
Git commits: <N> | Committers: <N>

Classification: GREENFIELD / LEGACY

Previous workflow artifacts:
  AGENTS.md: <exists / does not exist>
  CLAUDE.md: <exists / does not exist>
  Satellites: <list or "none">
  Post-commit hook: <exists / does not exist>

Active IDEs detected: <list>

Missing commands: <list or "none">
```

Don't modify anything else in the project. Only the `.wizard-state.json`.
