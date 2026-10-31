# /wf-onboard — Onboarding wizard for new developers

> **Note**: onboarding reads the live repo source of truth (AGENTS.md router,
> satellites). The project's protocols live packaged as
> skills in the IDE's native path (`.claude/skills/<n>/`, `.kiro/skills/<n>/`,
> `.codex/skills/<n>/`, `.windsurf/skills/<n>/`, `.devin/skills/<n>/`), with the
> universal `.agents/skills/<n>/` and flat `.agents/protocols/<n>.md` fallbacks
> (referenced by the AGENTS.md router), not embedded in AGENTS.md. When
> configuring the environment, no special action is needed: they are versioned with the repo.

> **When to use**: when you are a new developer who just cloned a repo
> that already has the AI Workflow Wizard configured. This wizard does NOT modify the repo
> — it only configures your local environment.
>
> **Why you do not run `/wf-init`**: the wizard state (`.wizard-state.json`) and manifest
> (`.wizard-managed-files.json`) are committed with the repo, so everything `/wf-init`
> discovered and decided is already there. `/wf-onboard` only prepares YOUR machine.
>
> **Difference from `/wf-init`**: `wf-init` initializes the workflow in a new repo.
> `wf-onboard` configures your machine for a repo that already has it.

---

## Agent role during onboarding

You are an onboarding wizard. Your goal is for this developer to be able to work
with the AI Workflow Wizard project on their local machine, without touching anything in the repo.

**Inviolable rules**:
1. Do NOT modify any repo files (AGENTS.md, satellites, etc.).
2. Do NOT `git add` or `git commit`.
3. All configuration goes to the developer's local machine, not the repo.
4. If a step requires manual developer action (login, API key), stop and guide them.
5. Ask for confirmation before installing anything (global commands, dependencies, git hooks).

---

## PHASE 0 — Read the repo context

Before any verification, read the project's AGENTS.md to understand:

```bash
cat AGENTS.md
```

Extract:
- The project stack (for relevant recommendations).
- The `## Project MCPs` section — this is the source of truth for which MCPs
  the developer needs to configure.

If `AGENTS.md` does not exist, this repo does not have the workflow configured:

```
This repo has no AGENTS.md — it was not initialized with /wf-init.
To initialize the workflow in this repo, run /wf-init instead.
```

Stop.

Then check that the repo carries the versioned wizard files:

```bash
for f in .wizard-state.json .wizard-managed-files.json; do
  [ -f "$f" ] && echo "✓ $f" || echo "⚠ $f not found"
done
```

If one is missing, the repo was initialized by an older wizard that kept them local.
Do NOT run `/wf-init`. Continue the onboarding and tell the developer:

```
This repo has no versioned wizard state. You can work with it normally, but /wf-refresh
and /wf-cleanup need it. Ask the maintainer who ran /wf-init to run /wf-refresh and
commit the result (it adds the state and the manifest to the repo).
```

---

## PHASE 0.5 — Prerequisites

The wizard scripts need a few tools on the developer's machine:

```bash
for tool in git jq python3 curl; do
  command -v "$tool" >/dev/null 2>&1 && echo "✓ $tool" || echo "✗ $tool missing (required)"
done
command -v gh >/dev/null 2>&1 && echo "✓ gh" || echo "ℹ gh not found (needed for GitHub MCP and PRs)"
if [ -f package.json ]; then
  command -v node >/dev/null 2>&1 && echo "✓ node $(node --version)" || echo "✗ node missing (required by this project)"
  command -v npm >/dev/null 2>&1 && echo "✓ npm $(npm --version)" || echo "✗ npm missing (required by this project)"
fi
```

If a required tool is missing, tell the developer how to install it (for example
`brew install jq`) and wait before continuing.

---

## PHASE 1 — gentle-ai

```bash
which gentle-ai 2>/dev/null && gentle-ai --version 2>/dev/null
```

**If NOT installed**: install the same as in `/wf-init` Phase 0.

```bash
brew tap Gentleman-Programming/homebrew-tap
brew trust --formula gentleman-programming/tap/gentle-ai
brew install gentle-ai
gentle-ai install
```

**If ALREADY installed**: verify that the same agents the
team uses are configured. Read the repo satellites to detect which agents the team uses:

```bash
ls .claude/ .cursor/ .windsurf/ .kiro/ .github/copilot-instructions.md 2>/dev/null
```

Compare with the agents configured on the developer's system:

```bash
gentle-ai status
```

For each team agent the developer is missing:

```
The team uses <agent> but it is not configured on your machine.
Shall I configure it now? [yes / no]
```

If yes: `gentle-ai install --agent <agent> --preset full-gentleman`

Then:

```bash
gentle-ai doctor
```

Critical checks that must be green: `tool:gentle-ai`, `tool:engram`, `state:json`.

> The `gentle_ai` block inside `.wizard-state.json` describes the machine of whoever ran
> `/wf-init`. Do NOT use it as a reference for this developer's machine: verify the local one
> as above.

---

## PHASE 1.5 — Wizard global commands and version

`/wf-init`, `/wf-refresh` and `/wf-cleanup` are **global** commands, installed once per machine
by `install.sh` (the project commands `/wf-onboard`, `/wf-worktree`, `/wf-settings` travel in
the repo). `install.sh` always writes the universal copy under `~/.agents/skills/`, so it is the
reliable indicator.

```bash
RAW="https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main"
REMOTE_VERSION=$(curl -fsSL "$RAW/VERSION" 2>/dev/null | head -1 | sed 's/^v//')

MISSING_GLOBAL=""
for cmd in wf-init wf-refresh wf-cleanup; do
  [ -f "$HOME/.agents/skills/$cmd/SKILL.md" ] || MISSING_GLOBAL="$MISSING_GLOBAL $cmd"
done
INSTALLED_VERSION=$(sed -n 's/^version: *//p' "$HOME/.agents/skills/wf-init/SKILL.md" 2>/dev/null | head -1 | sed 's/^v//')

if [ -n "$MISSING_GLOBAL" ]; then
  echo "✗ Global commands missing:$MISSING_GLOBAL"
elif [ -n "$REMOTE_VERSION" ] && [ "$INSTALLED_VERSION" != "$REMOTE_VERSION" ]; then
  echo "⚠ Global commands are v${INSTALLED_VERSION:-unknown}, latest is v$REMOTE_VERSION"
else
  echo "✓ Global commands installed (v$INSTALLED_VERSION)"
fi
```

If they are missing or outdated, explain what will happen and ask before running the installer.
It downloads and runs a script from the wizard's GitHub repo and writes only inside the
developer's home directory (their IDEs' global command folders):

```
The wizard's global commands are missing (or outdated) on this machine.
I can install them with:

  curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/install.sh | bash

Run it now? [yes / no]
```

If yes, run it and tell the developer to restart their IDE afterwards. The installer needs at
least one supported IDE already installed; if it reports none, guide the developer to install
their IDE first.

Then compare the project's wizard version with the latest one. This is informational only:
updating the project changes repo files, so it is the maintainers' call.

```bash
PROJECT_VERSION=$(jq -r '.wizard_version // empty' .wizard-state.json 2>/dev/null | sed 's/^v//')
if [ -n "$PROJECT_VERSION" ] && [ -n "$REMOTE_VERSION" ] && [ "$PROJECT_VERSION" != "$REMOTE_VERSION" ] \
   && [ "$(printf '%s\n%s\n' "$PROJECT_VERSION" "$REMOTE_VERSION" | sort -V | tail -1)" = "$REMOTE_VERSION" ]; then
  echo "ℹ This project was generated with wizard v$PROJECT_VERSION; v$REMOTE_VERSION is available."
  echo "  Do not update it from your clone without asking: /wf-refresh commits changes to the repo."
fi
```

---

## PHASE 2 · Engram

Engram activates automatically in any work session with the agent. The agent uses it via
MCP tools (`mem_save`, `mem_search`, etc.) without the developer having to run any manual
command. For stdio-only agents (Claude Code, Cursor, Windsurf, Gemini CLI, Antigravity CLI,
Codex, VS Code) even a separate server process is not needed. Engram runs embedded as a
single binary with SQLite. Only agents with an HTTP plugin (OpenCode, Pi) need `engram serve`
running in the background, and those plugins auto-start it when possible.

No additional action is required here once `gentle-ai doctor` passed in Phase 1.

---

## PHASE 2.5 — Dependencies and git hooks

Dependencies come before the MCPs because some checks (for example Playwright) need them.

### Install dependencies

Use the lockfile so the repo files are not modified (`npm ci` never rewrites the lockfile).
Show the command and ask for confirmation before running it.

```bash
if [ -f package.json ]; then
  if   [ -f package-lock.json ]; then echo "→ npm ci"
  elif [ -f pnpm-lock.yaml ];    then echo "→ pnpm install --frozen-lockfile"
  elif [ -f yarn.lock ];         then echo "→ yarn install --frozen-lockfile"
  else echo "→ npm install   (no lockfile: this may create one; do not commit it)"
  fi
fi
```

Run the matching command. This also activates Husky: its `prepare` script points
`core.hooksPath` to the versioned `.husky/` hooks (commit-msg validation, drift detector).

For non-Node stacks, run the install command listed under `## Commands` in AGENTS.md
(for example `composer install` or `pip install -r requirements.txt`). It is not automated.

### Git hooks

The drift detector reports when `/wf-refresh` is due. It lives in one place, never both:

```bash
HOOKS_PATH=$(git config --get core.hooksPath 2>/dev/null || true)
HOOK_WANTED=$(jq -r '.features.hook // false' .wizard-state.json 2>/dev/null)

if [ -d .husky ]; then
  # Husky: the hooks are versioned in .husky/ and activated by `npm install` (prepare script).
  case "$HOOKS_PATH" in
    .husky*) echo "✓ Husky hooks active (core.hooksPath=$HOOKS_PATH)" ;;
    *) echo "⚠ Husky hooks are NOT active. Run: npm run prepare" ;;
  esac
elif [ "$HOOK_WANTED" = "true" ]; then
  HOOK_FILE=$(git rev-parse --git-path hooks/post-commit)
  [ -f "$HOOK_FILE" ] && echo "✓ post-commit hook present ($HOOK_FILE)" \
                      || echo "⚠ post-commit drift hook missing: $HOOK_FILE"
fi
```

If the plain hook is wanted but missing, `.git/hooks/` is not versioned, so recreate it from the
wizard's template (the same source `/wf-init` uses). Confirm first. Nothing is overwritten:

```bash
HOOK_FILE=$(git rev-parse --git-path hooks/post-commit)
RAW="https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main"
if [ -f "$HOOK_FILE" ]; then
  echo "ℹ $HOOK_FILE already exists; not overwriting it."
else
  mkdir -p "$(dirname "$HOOK_FILE")"
  # The template is one bash fence; \140 is a backtick (written as an escape so it does not close this block).
  curl -fsSL "$RAW/templates/protocols/cicd/hook.post-commit.tmpl.md" \
    | awk '/^\140\140\140bash/{f=1;next} /^\140\140\140/{if(f)exit} f' > "$HOOK_FILE.tmp"
  if head -1 "$HOOK_FILE.tmp" | grep -q '^#!'; then
    mv "$HOOK_FILE.tmp" "$HOOK_FILE" && chmod +x "$HOOK_FILE" && echo "✓ Installed $HOOK_FILE"
  else
    rm -f "$HOOK_FILE.tmp"; echo "✗ Could not download the hook template; try again later."
  fi
fi
```

If a `post-commit` hook already exists but differs from the template, show the difference and
let the developer decide.

---

## PHASE 3 — Project MCPs

Read the `## Project MCPs` section from the AGENTS.md you extracted in Phase 0.
For each listed MCP, verify if it is available on the developer's machine
and guide the configuration of any missing ones.

### Engram and Context7

Automatic via gentle-ai. If `gentle-ai doctor` passed in Phase 1, they are ready.
No additional action required.

### Playwright MCP

Only relevant if the project has E2E tests (detected in `package.json` with
`@playwright/test`).

```bash
npx playwright --version 2>/dev/null
```

If not installed or browsers are missing:

```bash
npx playwright install --with-deps chromium
```

The MCP itself (registered in `.claude/settings.json` of the repo) is already in the repo
and gentle-ai loads it automatically. You only need the browsers.

**Windsurf exception**: Windsurf has no project-level MCP config, so the repo cannot carry it.
If the developer uses Windsurf, each member registers it once in
`~/.codeium/windsurf/mcp_config.json` (a global file on their machine). Show them the snippet
and wait for confirmation before editing that file; keep any servers it already has:

```json
{ "mcpServers": { "playwright": { "command": "npx", "args": ["@playwright/mcp"] } } }
```

### GitHub MCP

If the AGENTS.md lists GitHub MCP:

```bash
gh auth status 2>/dev/null
```

If not authenticated:

```
GitHub MCP requires authentication. Run:
  gh auth login

Follow the interactive flow and choose "GitHub.com" + "HTTPS" + browser authentication.
Let me know when you are done.
```

Wait for developer confirmation.

### MCPs with API key (Supabase, Stripe, Postgres, or others)

For each MCP that AGENTS.md marks as "API key in `.env.local`":

```
<Name> MCP requires local credentials.

Do you have access to the <name> credentials for this project?
[I have the keys / no, I will ask the team / skip for now]
```

If the developer has the keys:

```
Add these variables to your `.env.local` (create it if it does not exist — it is in .gitignore):

<VARIABLE_NAME>=<your-key-here>

The .env.local file is NOT committed. Each developer has their own.
Let me know when you have saved the variables.
```

If they do not have the keys: register as pending and continue.

### MCP summary

At the end of the phase, show the status of each MCP:

```
MCP Status:
  Engram        ✓ active
  Context7      ✓ active
  Playwright    ✓ browsers installed
  GitHub        ✓ authenticated as <user>
  Supabase      ⚠ pending — ask team for keys
```

---

## PHASE 4 — Final verification

Show the project's real commands. They come from the versioned state (detected by `/wf-init`
from `package.json`), so nothing here is hardcoded:

```bash
jq -r '.discovery.commands // empty' .wizard-state.json 2>/dev/null \
  || grep -A15 '^## Commands' AGENTS.md
gentle-ai doctor 2>/dev/null | tail -5
```

Show the main project commands and confirm the developer can start:

```
Your environment is configured.

  Global commands      ✓ /wf-init /wf-refresh /wf-cleanup (v<version>)
  gentle-ai            ✓ healthy
  Dependencies         ✓ installed
  Git hooks            ✓ Husky active  |  ✓ post-commit drift hook  |  — none required
  MCPs                 <status from Phase 3>

Main commands for this project (from the wizard state):
  <one line per command in discovery.commands>

To start working:
1. Open the project in your IDE from the ROOT of the repo (not from the parent folder).
2. The agent will read AGENTS.md automatically on start.
3. Ask for any change in natural language — the agent classifies the route (A/B/C)
   and applies TDD Protocol automatically if tests are configured.

MCPs pending configuration:
  <list of MCPs that are still pending, if any>
```

---

## PHASE 5 — README recommendation

If the project README does not mention `/wf-onboard`, suggest (without modifying anything):

```
Suggestion: add this line to the project README.md so future
developers know what to do:

  ## Setup for new developers
  Clone the repo and run `/wf-onboard` in your IDE to configure your local environment.

Do you want me to draft the full paragraph for you to copy? [yes / no]
```

---

> **Codex CLI**: unlike Claude Code, Cursor, Windsurf and other IDEs, Codex CLI treats skills as passive reference context — it can ignore the Decision Ladder and TDD Protocol gates. If you use Codex, having `AGENTS.md` and `.agents/` configured is not enough; you need to paste the protocol instructions at the end of each prompt. The wizard does not automate this; it is a client limitation.

---
