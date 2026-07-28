# /wf-onboard — Onboarding wizard for new developers

> **Note**: onboarding reads the live repo source of truth (AGENTS.md router,
> `openspec/config.yaml`, satellites). The project's protocols live packaged in
> `.claude/skills/<n>/` (Claude, auto-discovery) and `.agents/protocols/<n>.md` (other
> IDEs, referenced by the AGENTS.md router), not embedded in AGENTS.md. When
> configuring the environment, no special action is needed: they are versioned with the repo.

> **When to use**: when you are a new developer who just cloned a repo
> that already has the AI Workflow Wizard configured. This wizard does NOT modify the repo
> — it only configures your local environment.
>
> **Difference from `/wf-init`**: `wf-init` initializes the workflow in a new repo.
> `wf-onboard` configures your machine for a repo that already has it.

---

## Agent role during onboarding

You are an onboarding wizard. Your goal is for this developer to be able to work
with the AI Workflow Wizard project on their local machine, without touching anything in the repo.

**Inviolable rules**:
1. Do NOT modify any repo files (AGENTS.md, satellites, openspec/, etc.).
2. Do NOT `git add` or `git commit`.
3. All configuration goes to the developer's local machine, not the repo.
4. If a step requires manual developer action (login, API key), stop and guide them.

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
- The SDD backend (`openspec/config.yaml` if it exists).

If `AGENTS.md` does not exist, this repo does not have the workflow configured:

```
This repo has no AGENTS.md — it was not initialized with /wf-init.
To initialize the workflow in this repo, run /wf-init instead.
```

Stop.

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

---

## PHASE 2 — SDD and Engram

```bash
ls openspec/config.yaml 2>/dev/null && cat openspec/config.yaml | grep -E "artifact_store|backend" | head -3
```

**If `openspec/` exists**:

Read the project's backend. If it is `hybrid` or `openspec`:

```
This project uses the "<backend>" backend for SDD.
openspec/ is already in the repo — you have access to the historical specs context.

Do you want to initialize Engram for this project on your machine?
(Recommended if the backend is hybrid — it gives you cross-session memory)
[yes / no]
```

If yes: inform the developer that Engram activates automatically in any
work session with the agent — it is not exclusive to SDD. The agent uses it via
MCP tools (`mem_save`, `mem_search`, etc.) without the developer having
to run any manual command. For stdio-only agents (Claude Code, Cursor,
Windsurf, Gemini CLI, Antigravity CLI, Codex, VS Code) even a separate
server process is not needed — Engram runs embedded as a single binary with SQLite.
Only agents with an HTTP plugin (OpenCode, Pi) need `engram serve` running
in the background, and those plugins auto-start it when possible.

**If the backend is `engram` only**:

```
⚠ This project uses Engram-only as the SDD backend.
The team's SDD context lives in each developer's local Engram memory,
not in repo files. You will not have access to the team's previous decision
history in your local Engram.

If this is a problem, talk to the team about migrating to "hybrid".
```

**If `openspec/` does not exist**: inform that SDD is not initialized. It is not blocking
for work, but the agent will not be able to start SDD phases until someone runs `/sdd-init`.

---

## PHASE 3 — Project MCPs

Read the `## Project MCPs` section from the AGENTS.md you extracted in Phase 0.
For each listed MCP, verify if it is available on the developer's machine
and guide the configuration of any missing ones.

### Engram and Context7

Automatic via gentle-ai. If `gentle-ai doctor` passed in Phase 1, they are ready.
No additional action required.

### Playwright MCP

Only relevant if the project has E2E tests (detected in `openspec/config.yaml`
with `layers.e2e: true` or in `package.json` with `@playwright/test`).

```bash
npx playwright --version 2>/dev/null
```

If not installed or browsers are missing:

```bash
npx playwright install --with-deps chromium
```

The MCP itself (registered in `.claude/settings.json` of the repo) is already in the repo
and gentle-ai loads it automatically. You only need the browsers.

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

```bash
# Verify the project works
cat package.json | grep '"dev"\|"build"\|"test"'
```

Show the main project commands and confirm the developer can start:

```
Your environment is configured. Main commands for this project:

  npm run dev       → development server
  npm run build     → production build
  npm run test      → unit + integration tests
  npm run test:e2e  → E2E tests with Playwright

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
