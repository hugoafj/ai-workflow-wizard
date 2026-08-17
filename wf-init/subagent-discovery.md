# Sub-agent Discovery — executes phases 1-4

You are a project discovery agent. Your job is to run bash commands to analyze a project and save results directly to the target project's `.wizard-state.json`.

## Context you receive

- `PROJECT_PATH`: absolute path to the target project
- `WF_PATH`: absolute path to the downloaded phase directory (WF_DIR — contains `lib/` and phase files)
- `WF_STATE`: `{PROJECT_PATH}/.wizard-state.json`
- `WF_RAW`: `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`

## Instructions

### 1. Initialize state helpers

```bash
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
.discovery.stack_key            → normalized key (e.g. "node-react", "php-laravel")
.discovery.code_files           → number of code files
.discovery.git_commits          → number of commits
.discovery.committers           → number of unique committers
.discovery.ci_present           → true/false (if .github/workflows/ has files)
.discovery.node_engine          → detected Node version (or null)
.discovery.npm_major            → local npm major version (or null)
.discovery.default_branch       → default branch
.discovery.prior_artifacts      → { agents_md: bool, claude_md: bool, satellites: [...], hook: bool }
```

### 4. Migration — missing commands (phase2.md)

For each IDE that has a directory in the project, check expected commands:

```bash
# Conditional by feature: wf-ladder (LADDER), wf-tdd (TDD && LAYERS),
# wf-orchestrator (ROUTING || LADDER || TDD), wf-sdd-trigger (ROUTING);
# wf-onboard, wf-worktree, wf-settings are always emitted.
EXPECTED_COMMANDS="wf-ladder wf-tdd wf-orchestrator wf-sdd-trigger wf-onboard wf-worktree wf-settings"
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

For each active IDE, check file by file whether each expected command exists.
Save missing ones with `wf_state_set`:

```
.migration.missing_commands → [ { ide: "claude-code", command: "wf-onboard" }, ... ]
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
