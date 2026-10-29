# AI Workflow Wizard

> Master document for the professional AI development workflow.
> Maintainer: hugoafj.

---

## ⚙ wf-init wizard architecture

> The `/wf-init` wizard is a **state machine with state persisted on disk**:
>
> - **State** (user responses + discovery) → `.wizard-state.json` at the project root
>   (contract: `wf-init/lib/state.md`; read/write helpers in `wf-init/lib/state-helpers.sh`;
>   refresh orchestrator in `wf-init/lib/refresher.md`). The process is resumable even if the
>   conversation is lost between phases.
> - **Permanent knowledge** (wf-ladder, CI/CD,
>   Testing, IDEs, Commands, Architecture) → `templates/protocols/<module/>` as **single
>   source of truth**, packaged as skills for each IDE (installed via `install.sh`).
> - **Assembly** → Deterministic Builder (`wf-init/lib/builder-core.py` B1-B6 + `wf-init/lib/builder-heavy.py` B7-B9; `wf-init/lib/builder.md` is the specification reference) that assembles artifacts
>   from state + templates to a staging area on disk. No "in-memory generation".
> - **AGENTS.md** → thin router that points to protocols, no longer embeds them.

---

## How to read this document (if you're new to AI-assisted dev)

This document describes a development workflow where AI does most of the coding, and you act as architect + critical reviewer. It is not a single-product manual: it is a complete system that combines several tools (gentle-ai, Engram, MCPs, AI IDEs/CLIs, CI/CD) into a coherent flow.

**Read it in this order if it's your first time**:

1. **Quick Glossary** (below). Saves you confusion throughout the rest of the document.
2. **Workflow Philosophy** (section 1). Why this system exists and what problem it solves.
3. **The Architecture: Two Layers** (section 2). The mental model. Come back here when you get lost.
4. **The Day-to-Day Cycle** (section 3). What working with this looks like in practice.
5. **gentle-ai · The Foundation** (section 4). What gentle-ai is and why the wizard installs it for you.
6. **Block 1 · Context Layer** (section 5). Start applying the workflow in a project.
7. **Blocks 2-7**. In order, as you progress through your project.

If you are going to try the workflow as you learn, **stop at the end of each block** and apply the tutorial steps. Do not advance to the next block without having tried the previous one. The idea is to refine with real usage.

---

## Quick Glossary

Terms that appear constantly. No need to memorize them; come back to this section when something doesn't sound familiar.

**Agent** — An AI program that executes tasks (not just answers questions). Claude Code, Cursor, Copilot, Windsurf, Codex CLI are agents. Each one uses AI models underneath, but the agent is what you invoke.

**AGENTS.md** — Markdown file at the root of your repo that gives the agent project context: conventions, commands, structure, constraints. 2026 standard read by most agents (some directly, others via satellite).

**Satellite** — File in a specific location in your repo (`CLAUDE.md`, `.cursor/rules/`, `.windsurf/rules/`, etc.) that points to `AGENTS.md`. It is necessary for agents that do not read `AGENTS.md` natively.

**Skill** — A reusable "routine" or "pattern" that the agent can apply. For example: a React 19 skill teaches the agent modern React conventions. Skills live in `~/.claude/skills/`, `~/.cursor/skills/`, etc.

**MCP (Model Context Protocol)** — Standard protocol for agents to talk to external tools (databases, GitHub, browsers, etc.). An "MCP server" is a program that exposes functions the agent can invoke.

**Engram** — The agent's persistent memory. It is a local program (Go binary with SQLite) that the agent uses via MCP to save decisions, context, bugs, learnings between sessions. Without Engram, each session starts from zero.

**gentle-ai**: Ecosystem configurator. It is a binary installed once on your machine that configures ALL your agents (Claude Code, Cursor, etc.) with Engram, skills, MCPs, ODD, persona, and permissions. It is the foundation of this workflow.

**ODD (Organic Driven Development)**: The feature workflow that gentle-ai runs natively for every agent. Small, understood changes go straight to implementation. For substantial, authorized work the agent creates one feature document, `odd/tasks/<feature>.md`, with the specs, the tasks, and a log, and mirrors it to Engram. You do not invoke it: you describe what you want.

**GGA (Gentleman Guardian Angel)** — AI code review tool from the gentle-ai ecosystem. Reviews diffs and PRs applying defined standards. Provider-agnostic (works with Claude, Gemini, Codex, Ollama).

**RDD (Receipt-Driven Development)**: Independent review of a frozen change candidate, run by gentle-ai. It is on by default and opt-out: `gentle-ai review mode disable` turns it off. Medium and high risk candidates ask for consent first.

**TDD (Test-Driven Development)**: Methodology where you write the test BEFORE the code. In this workflow, when a relevant runnable test exists, the agent writes it first, watches it fail, then implements until it passes. Test-first is the default, not an optional mode.

**Conventional commits** — Commit message convention with prefixes (`feat:`, `fix:`, `chore:`, etc.) that enables automatic changelog generation and releases.

**Worktree** — Isolated git folder that shares the same repo. Useful for having multiple agents working in parallel without stepping on each other, each in their own worktree.

**Wizard `/wf-init`**: Global slash command for this workflow that initializes a project: installs and verifies gentle-ai automatically (Phase 0), discovers the project (Phases 1-4), asks which optional features to enable (Phase 0c), generates `AGENTS.md` with its Testing Approach section (Phases 6a and 6b), configures a post-commit hook that detects AGENTS.md drift. Installed with `install.sh` as a global slash command. Architecture: orchestrator (`templates/commands/wf-init/_base.md`) + phase files in `wf-init/` (read on-demand from disk).

**Hook (git hook)** — Script that git executes automatically on certain events (commit, push). Runs only on your local machine, not on GitHub. We use it to detect drift in AGENTS.md.

**Drift** — When something in the project changes and leaves `AGENTS.md` outdated. The hook detects it. `/wf-refresh` corrects it.

**MCP App** — External application connected via MCP. Example: Atlassian MCP lets you create issues in Jira from the agent.

---

## Table of Contents

1. [Workflow Philosophy](#1-workflow-philosophy)
2. [The Architecture: Two Layers](#2-the-architecture-two-layers)
3. [The Day-to-Day Cycle](#3-the-day-to-day-cycle)
4. [gentle-ai · The Foundation](#4-gentle-ai--the-foundation)
   - 4.1 [What is gentle-ai in practical terms](#41-what-is-gentle-ai-in-practical-terms)
   - 4.2 [Automatic installation via the wizard](#42-automatic-installation-via-the-wizard)
   - 4.3 [Manual installation (reference)](#43-manual-installation-reference)
   - 4.4 [Extra stack skills](#44-extra-stack-skills-optional-but-recommended)
   - 4.5 [Environment variable for OpenCode](#45-environment-variable-for-opencode)
   - 4.6 [Verification and health check](#46-verification-and-health-check)
   - 4.7 [Update](#47-update)
   - 4.8 [Scope per project (advanced)](#48-scope-per-project-advanced)
   - 4.9 [Troubleshooting](#49-troubleshooting)
   - 4.10 [gentle-ai TUI](#410-gentle-ai-tui)
   - 4.11 [Engram TUI](#411-engram-tui)
5. [Block 1 · Context Layer](#5-block-1--context-layer)
   - 5.1 [Understanding AGENTS.md](#51-understanding-agentsmd)
   - 5.2 [Stack-adapted template](#52-stack-adapted-template)
   - 5.3 [Wizard `/wf-init` (greenfield + legacy)](#53-wizard-wf-init-greenfield--legacy)
   - 5.4 [Project-specific satellites: what they are and why we need them](#54-project-specific-satellites-what-they-are-and-why-we-need-them)
   - 5.5 [Context auto-update](#55-context-auto-update)
   - 5.6 [Step-by-step tutorial · Test the wizard on a clean project](#56-step-by-step-tutorial--test-the-wizard-on-a-clean-project)
   - 5.7 [Ensuring multi-IDE fidelity · Strategy and specific fixes](#57-ensuring-multi-ide-fidelity--strategy-and-specific-fixes)
   - 5.8 [Optional behavior improvements · wf-ladder](#58-optional-behavior-improvements--wf-ladder)
6. [Block 2 · Feature Tracking (ODD)](#6-block-2--feature-tracking-odd)
   - 6.1 [ODD philosophy](#61-odd-philosophy)
   - 6.2 [How gentle-ai runs ODD for you](#62-how-gentle-ai-runs-odd-for-you)
   - 6.3 [The feature document](#63-the-feature-document)
   - 6.4 [Work units, delivery and the 400-line budget](#64-work-units-delivery-and-the-400-line-budget)
   - 6.5 [Review and consent (RDD)](#65-review-and-consent-rdd)
   - 6.6 [Judgment Day: dual-judge review](#66-judgment-day-dual-judge-review)
7. [Block 3 · MCPs, Testing Stack and Commands](#7-block-3--mcps-testing-stack-and-commands)
8. [Block 4 · Orchestration and worktrees](#8-block-4--orchestration-and-worktrees)
    - 8.1 [What gentle-ai automates vs. what the wizard provides](#81-what-gentle-ai-automates-vs-what-the-wizard-provides)
   - 8.2 [Sub-agents and delegation](#82-sub-agents-and-delegation-native-to-gentle-ai)
   - 8.3 [Model choice](#83-model-choice)
   - 8.4 [Worktrees — `/wf-worktree`](#84-worktrees--wf-worktree-built-in-this-block)
9. [Block 5 · Testing: test-first and Playwright](#9-block-5--testing-test-first-and-playwright)
    - 9.1 [Test-first by default](#91-test-first-by-default)
    - 9.2 [Playwright dual loop](#92-playwright-dual-loop-when-to-explore-before-versioning)
    - 9.3 [data-testid convention](#93-data-testid-convention-mandatory-when-e2e-is-present)
    - 9.4 [Optional extras](#94-optional-extras-coverage-targets-visual-regression-page-object-model)
    - 9.5 [Strategy for legacy projects without tests](#95-strategy-for-legacy-projects-without-tests)
    - 9.6 [/wf-settings: toggle optional modules after installation](#96-wf-settings-toggle-optional-modules-after-installation)
10. [Block 6 · CI/CD pipeline + GGA](#10-block-6--cicd-pipeline--gga)
11. [Block 7 · Bootstrap automation (slash commands)](#11-block-7--bootstrap-automation-slash-commands)
12. [Appendices](#appendices)

---

## 1. Workflow Philosophy

The fundamental paradigm shift: the engineer stops being the one who writes code and becomes a **product engineer + context architect + critical reviewer**. AI is the executor. The main work becomes:

- Define clearly what to build (clear specs).
- Give AI the correct context (this workflow).
- Distribute work among agents when warranted.
- Aggressively validate what they produce.

**Mental rule**: treat AI as a team of very fast juniors. They need clear specs, reference code, tests that validate their work, mandatory code review, and an onboarding (`AGENTS.md`) that tells them how things work around here.

---

## 2. The Architecture: Two Layers

The workflow has **two clearly separated layers**:

### 2.1 Foundation Layer · gentle-ai

Provides the base ecosystem that is **the same across all your projects**. Lives **globally** on your machine (`~/.claude/`, `~/.cursor/`, `~/.kiro/`, etc.). A single installation serves all projects.

What it provides:

- **Engram**: persistent memory via MCP, across sessions, with full-text search.
- **ODD (Organic Driven Development)**: the feature workflow the agent follows on every request. Substantial work gets a feature document, and you don't have to learn slash commands.
- **Skills**: curated library (embedded foundation + community in `Gentleman-Skills`).
- **Preconfigured MCPs**: Context7 (live framework docs), Engram.
- **Automatic multi-IDE config**: configures Claude Code, OpenCode, Cursor, Windsurf, Codex CLI, Kiro, VS Code Copilot, Gemini CLI, Antigravity CLI, Pi, OpenClaw, Trae.
- **Persona**: senior architect teaching-oriented (or neutral if you prefer).
- **Permissions**: blocks destructive commands and sensitive paths (`.env`, `.ssh`, etc.) by default.
- **Model routing**: gentle-ai can assign models to agents. Section 8.3 lists the models this workflow approves.
- **GGA (Gentleman Guardian Angel)**: AI code review (activated in Block 6).
- **Auto-updates**: via Homebrew/Scoop.

### 2.2 Custom Layer · Your project-specific workflow

On top of gentle-ai, in each repo. This is what you maintain. What it provides:

- **AGENTS.md**: project-specific context (stack, conventions, constraints, exact commands). gentle-ai's skills + persona still apply, but AGENTS.md tells the agent HOW THIS specific repo is.
- **Wizard `/wf-init`**: slash command that installs gentle-ai if not present, verifies system state, and bootstraps the project (generates AGENTS.md, configures hooks, adjusts .gitignore).
- **Post-commit hook**: detects structural drift and warns when AGENTS.md may need an update.
- **Project-specific satellites**: files in `.cursor/rules/`, `.windsurf/rules/`, `.kiro/steering/`, `CLAUDE.md`, etc. that point to the repo's AGENTS.md. **gentle-ai does NOT generate these satellites**, because gentle-ai is global and knows nothing about your individual repo. All satellites are always from the custom workflow (section 5.4 explains them in detail).
- **CI/CD pipeline**: GitHub Actions with quality guard + AI review (Claude Code Action or GGA).
- **Conventional commits + release-please**: traceable releases and automatic changelog.
- **`/wf-onboard`**: local setup command for devs who clone the repo (project-specific MCPs, etc.).

### 2.3 How they complement each other without clashing

gentle-ai writes to **global** folders (`~/.claude/`, etc.). Our custom satellites write to **project** folders (`.claude/`, `.cursor/`, etc.). Different files, different locations, **coexist without conflict**.

When you open an IDE in a project:

1. The IDE first reads the global config (from gentle-ai) → persona, skills, MCPs, permissions.
2. Then reads the project config (your AGENTS.md + satellites) → repo-specific context.
3. The agent combines both. The two layers complement each other.

---

## 3. The Day-to-Day Cycle

When everything is set up, a typical feature looks like this:

1. **New or existing repo** → you start in any state.
2. **`/wf-init`** once per repo → installs gentle-ai if missing, generates AGENTS.md + satellites + hooks.
3. **You open your AI IDE** → skills, MCPs, Engram, and ODD already active (courtesy of gentle-ai).
4. **You request a feature in natural language**. You don't learn slash commands.
5. **ODD sets the depth**: small work proceeds directly; substantial work gets a feature document that tracks specs, tasks, and evidence.
6. **Sub-agents work per task** when the work is large enough to delegate, each with fresh context.
7. **You stay in control of delivery**: you give consent for medium and high risk reviews, and you decide what gets committed and pushed.
8. **Human review gate** before commit: the agent shows you the full diff, waits for your approval.
9. **Commit with conventional commits** + the post-commit hook detects if AGENTS.md may need an update.
10. **PR + CI/CD pipeline**: Quality Guard (lint, types, tests, build) + AI review (GGA or Claude Code Action) + security scan.
11. **Merge + release-please** prepares the automatic release PR with changelog.
12. **Engram saves what was learned** for the next session.

---

## 4. gentle-ai · The Foundation

gentle-ai is the foundation of this workflow: it configures the complete AI agent ecosystem on your machine (persona, skills, ODD, Engram, MCPs, permissions). **You don't need to install it manually before starting.** The `/wf-init` wizard detects it, installs it if missing, and configures it (all in its Phase 0).

This section exists as **reference**: what it is, what it installs, and advanced options you might need later.

### 4.1 What is gentle-ai in practical terms

It is a binary written in Go. It lives on your machine (`/opt/homebrew/bin/gentle-ai` on macOS, similar on Linux/Windows). When you run it, it **configures all the AI agents you have installed** to work better: connects Engram (persistent memory), installs skills, registers MCPs, injects persona, etc.

**It is model-agnostic**: works with Claude, GPT/Codex, Gemini, etc. **It is IDE-agnostic**: configures all the ones it detects.

What it installs on your machine (once, globally):

- **Engram**: persistent memory via MCP. Local SQLite, full-text search, shared across all IDEs.
- **ODD**: the feature workflow the agent follows natively, so there is nothing to install for it.
- **Foundation skills**: workflow and testing, plus Judgment Day for dual review. Embedded in gentle-ai.
- **Preconfigured MCPs**: Context7 (live framework docs), Engram.
- **Persona**: senior architect teaching-oriented. Applies to all configured IDEs.
- **Permissions**: blocks destructive commands and sensitive paths by default.
- **GGA (Gentleman Guardian Angel)**: AI code review. Activated per project in Block 6.

### 4.2 Automatic installation via the wizard

**Do not install manually.** When running `/wf-init` on any repo, Phase 0 of the wizard:

1. Detects if gentle-ai is installed (`which gentle-ai`).
2. If not: installs it automatically with brew (macOS/Linux) or scoop (Windows), then runs `gentle-ai install` to configure the detected agents.
3. If already installed: checks if an update is available and recommends whether it is mandatory or suggested.
4. Runs `gentle-ai doctor` and verifies it is green.
5. Confirms which agents you will use in the project.

If you want to install gentle-ai before running the wizard (for example, to configure it on a new machine without a project yet), use the commands in section 4.3.

### 4.3 Manual installation (reference)

You only need this if you want to install on a new machine before having a project, or if the wizard fails and you need to do it manually.

**macOS / Linux** (Homebrew):

```bash
brew tap Gentleman-Programming/homebrew-tap
brew trust --formula gentleman-programming/tap/gentle-ai
brew install gentle-ai
gentle-ai install
```

**Windows** (Scoop):

```powershell
scoop bucket add gentleman https://github.com/Gentleman-Programming/scoop-bucket
scoop install gentle-ai
gentle-ai install
```

**Alternative** (Go install, any platform):

```bash
go install github.com/gentleman-programming/gentle-ai/cmd/gentle-ai@latest
gentle-ai install
```

`gentle-ai install` detects the IDEs/CLIs you already have on your machine and configures them. If any are missing, add them manually:

```bash
gentle-ai install --agent claude-code --preset full-gentleman
gentle-ai install --agent cursor --preset full-gentleman
gentle-ai install --agent windsurf --preset full-gentleman
gentle-ai install --agent kiro-ide --preset full-gentleman
gentle-ai install --agent opencode --preset full-gentleman
gentle-ai install --agent vscode-copilot --preset full-gentleman
gentle-ai install --agent codex --preset full-gentleman
```

> `--preset full-gentleman` activates everything: persona, skills, MCPs, permissions. It is the preset the wizard uses by default.

### 4.4 Extra stack skills (optional but recommended)

gentle-ai comes with embedded foundation skills. For specific framework skills (React 19, Tailwind 4, TypeScript, Zod, Playwright, etc.) you clone the community repo and copy what you need:

```bash
cd ~
git clone https://github.com/Gentleman-Programming/Gentleman-Skills.git

# Copy the ones you will use (example for this stack)
cp -r ~/Gentleman-Skills/curated/react-19 ~/.claude/skills/
cp -r ~/Gentleman-Skills/curated/typescript ~/.claude/skills/
cp -r ~/Gentleman-Skills/curated/tailwind-4 ~/.claude/skills/
cp -r ~/Gentleman-Skills/curated/playwright ~/.claude/skills/

# Or all:
cp -r ~/Gentleman-Skills/curated ~/.claude/skills/
```

For other agents, skills go to different folders (`~/.cursor/skills/`, `~/.kiro/skills/`, etc.). gentle-ai loads skills from the active agent's folder.

> **For dummies**: a skill is a `SKILL.md` file with framework instructions. When the agent detects you are working with React 19, it loads that skill and applies modern patterns without you asking.

### 4.5 Environment variable for OpenCode

If you use OpenCode, enable experimental features (sub-agents, beta plugins):

```bash
echo 'export OPENCODE_EXPERIMENTAL=true' >> ~/.zshrc
source ~/.zshrc
```

### 4.6 Verification and health check

```bash
gentle-ai doctor
```

What you should see:

- `tool:gentle-ai` → ok
- `tool:engram` → ok
- `tool:gga` → ok
- `state:json` → ok, showing the configured agent list
- `engram:reachable` → ok (if it fails, the agent starts it on-demand — non-blocking)
- `disk:space` → ok

```bash
gentle-ai status   # view configured agents specifically
```

### 4.7 Update

```bash
brew upgrade gentle-ai      # upgrade the binary
gentle-ai upgrade           # upgrade internal components (skills, sub-agents, configs)
gentle-ai --version         # verify version
```

The wizard checks for updates automatically on each run (Phase 0, Step 0.3).

### 4.8 Scope per project (advanced)

If you work with clients that prohibit modifying global IDE config, you can install gentle-ai per-project:

```bash
gentle-ai install --scope=workspace
```

Writes to the project folder instead of `~/`. Only use this if a client requires it; for personal use, **global is the correct default**.

### 4.9 Troubleshooting

**`gentle-ai: command not found` after installing**: close and reopen the terminal, or `source ~/.zshrc`. Verify with `which gentle-ai` that it is in `/opt/homebrew/bin/` (Mac M1/M2) or `/usr/local/bin/` (Mac Intel).

**`engram:reachable [fail]`**: Engram is not running. Some agents launch it on-demand. If you need it running 24/7: `engram serve --daemon`.

**`brew install` fails with tap untrusted**: run `brew trust --formula gentleman-programming/tap/gentle-ai` before install.

**Doctor shows "2 copies found in PATH"**: you have a duplicate binary (typically nvm + brew). Cosmetic, non-critical. Clean with `which -a <binary>` and uninstall the extra copy.

**Any other problem**: `gentle-ai doctor` provides detailed diagnostics with a Remedy column.

### 4.10 gentle-ai TUI

When you run `gentle-ai` without arguments (or `gentle-ai install`), the interactive TUI opens. It is built with Bubble Tea (Go) and has a Rose Pine theme. Here is what you can do from it that is not obvious from the CLI:

**Basic navigation**: arrows or `j/k` to move, `Enter` to select, `Esc` to go back, `q` to exit.

**Main screens and what they are for**:

- **Install / Configure agents**: select which IDEs/CLIs to configure. Shows detected agents on your machine with checkmarks. You can check/uncheck without running additional commands.
- **Configure Models**: assign models to the sub-agents gentle-ai installs, including Judgment Day (jd-judge-a, jd-judge-b, jd-fix-agent). Also configures Codex lanes (strong/mid/cheap).
- **Backup & Rollback**: lists automatic configuration snapshots (gentle-ai backs up before each install/sync/upgrade). You can pin a backup with `p` to protect it from auto-pruning (by default it keeps the 5 most recent). Useful if an update broke something.
- **Uninstall**: removes specific components from specific agents without deleting everything. Example: remove only `persona` from Cursor without affecting Claude Code.
- **Doctor**: equivalent to `gentle-ai doctor` in terminal, but with visual formatting.

**Useful shortcuts that are not obvious**:

- `p` in Backup & Rollback: pins the selected backup (not deleted by auto-pruning).
- In Configure Models: you can assign models without needing the CLI.
- Upgrade from the TUI: if an update is available, the TUI shows the prompt "Apply now? [Y/n]". When updating gentle-ai from the TUI, the app restarts automatically after you confirm the result.

> **For dummies**: the TUI is useful for exploring what gentle-ai has installed and changing models per sub-agent. For daily use, you don't need to open it. The workflow runs in the background. Open it when you want to adjust which model a sub-agent uses or review/restore a configuration backup.

### 4.11 Engram TUI

Engram has two available user interfaces: CLI for quick search from terminal, and TUI for visually exploring memory history.

**CLI — everyday commands**:

```bash
engram search "auth bug"          # search past decisions with full-text search
engram projects list              # list all projects with memory counts
engram projects consolidate       # fix name drift ("my-app" vs "My-App")
engram serve                      # start HTTP server on port 7437 (needed
                                  # only for OpenCode and Pi — Claude Code does not require it)
```

**TUI — visual memory explorer**:

```bash
engram tui
```

The Engram TUI is a persistent memory browser. It shows:

- **Project list**: all projects with saved memories, with counts.
- **Memories by project**: list of entries with timestamp, type (decision, bug, context), and content preview.
- **Detailed view**: the full content of a memory, including metadata the agent saved.
- **Search**: full-text search within memories, equivalent to `engram search` but interactive.

**Navigation**: arrows to move, `Enter` to open, `/` to search, `q` to exit.

**When to use it**:

- To see what the agent remembers about a project before starting an important session.
- To detect obsolete or contradictory memories (for example, an architecture decision that changed).
- To verify that the agent correctly saved a decision after a feature session.
- To diagnose why the agent proposed something unexpected ("what did it remember about the project?").

**What it does NOT show**: Engram TUI only shows explicit persistent memories (those the agent saved with `mem_save`). It does not show in-memory session context or the feature documents in `odd/tasks/`, which are plain files in your repo. They are different layers.

**Note about `engram serve`**: most agents (Claude Code, Antigravity CLI, Gemini CLI, Codex, VS Code, Cursor, Windsurf) launch Engram as an automatic stdio subprocess — you never run `engram serve` manually for them. Only OpenCode and Pi need `engram serve` running in the background for their HTTP integration. If you see `engram:reachable [fail]` in `gentle-ai doctor` and you use Claude Code, ignore it — it is not blocking for that agent.

---

## 5. Block 1 · Context Layer

### 5.1 Understanding AGENTS.md

**What it is**: Markdown file at the repo root, automatically read by most AI agents when starting a session. It gives the agent the minimum context needed to avoid acting like a junior who just joined your team.

**What it is NOT**: documentation for humans (that goes in `README.md`). `AGENTS.md` is a **runtime instruction set**: it loads directly into the agent's context window every time a session opens.

#### Optimal size

2026 research (Augment Code + ETH Zurich) showed:

- **Optimal**: 150-200 lines in the root file.
- **Upper limit observed in successful repos**: 371 lines.
- **Above that**: the agent suffers lost-in-the-middle. If your AGENTS.md grows large, modularize with nested `AGENTS.md` files in subdirectories.
- **LLM-generated AGENTS.md without human curation**: reduces task success ~3% and increases inference costs 20-23%. Human curation is mandatory post-generation.

#### The 6 sections that actually move the needle

These do improve agent behavior. The rest is noise that wastes tokens.

**1. Commands** — Exact commands for build, test, lint, dev server, deploy. With real flags. Not `npm test`, but `npm run test:unit -- --coverage --bail`.

**2. Code Style & Conventions** — Only the non-obvious. Do NOT include things the agent can deduce from code (camelCase, indent size). DO include rules like "never use `any` in TypeScript outside files marked with comment-pragma", "all interactive components have `data-testid`".

**3. Project Structure** — A short tree view of the main folders and what goes in each. NOT the full tree; only the points where the agent might get confused.

**4. Critical Constraints** — What the agent must NOT do. Exact versions of sensitive libs, prohibited libraries, read-only paths, patterns banned due to historical trauma.

**5. Testing Approach** — Which framework, what each test type covers, what is considered mandatory for PR, naming convention.

**6. Programmatic Checks** — Commands the agent must run before declaring a task done. E.g.: `npm run lint && npm run typecheck && npm run test:unit && npm run build`.

#### What does NOT go in AGENTS.md

Wastes tokens without improving behavior:

- Abstract architectural overview ("we use clean architecture").
- Tech stack that the agent can read from `package.json` / `composer.json` / `requirements.txt`.
- Project history.
- Team contact info ("ask Juan").
- Roadmap.
- Justifications of past decisions (unless counter-intuitive).

**Past decisions and "why"** go in **Engram** (gentle-ai's persistent memory). Engram has semantic search and only brings relevant context; AGENTS.md burns fixed tokens every session.

#### About the agent's role

With gentle-ai installed, **the agent's role/persona is provided by gentle-ai globally**. You don't need to write it in AGENTS.md unless you want a project-specific override. gentle-ai's default persona is "senior architect teaching-oriented". If you want another, configure it globally with `gentle-ai persona neutral` or the equivalent slash command.

#### Behavior preferences

A section typically at the end of AGENTS.md with operational preferences from the human about how they want the agent to work in this specific repo:

- Review gate before commit ("show me the diff and wait for my OK").
- No opportunistic refactor ("stick to the new pattern only in new code").
- Drift detection ("if you find inconsistency between code and AGENTS.md, report it with a tag").

### 5.2 Stack-adapted template

The `AGENTS.md` is **per-repository, not per-developer**. Each project has its own AGENTS.md adapted to the stack it uses.

**When the Decision Ladder is enabled**, the router lists `wf-ladder` among its protocols, and the agent loads it before proposing an implementation. The protocols live in skills and in `.agents/protocols/`, so the router itself stays short.

**What changes between stacks** (mental map):

| Stack | Emphasis on Code Style | Emphasis on Critical Constraints |
| --- | --- | --- |
| React + Vite + TS | Component patterns, hooks rules, Tailwind syntax | React and Tailwind versions |
| Next.js fullstack | App Router vs Pages, server vs client components, fetching | Server/client boundaries, env vars, caching |
| Laravel + PHP | Eloquent patterns, queue handling, FormRequest, middleware | Artisan commands, namespaces, migrations |
| Backend Node/Express | Error handling, API contracts, auth, validation | Transactions, idempotency, rate limiting |
| Python FastAPI / Django | Type hints, Pydantic schemas, async patterns | DB sessions, dependency injection |

#### Concrete example: AGENTS.md for `crud-tasks-demo`

Stack: Vite 8 + React 19.2 + TS 6 + Tailwind 4 + ESLint 9 flat config. Size: ~82 lines. Covers the 6 mandatory sections + Behavior preferences + Trigger 3 of drift detection + version footer.

> **For dummies**: the AGENTS.md lives in the `AGENTS.md` file at the root of your repo. The agent reads it on its own. To validate it works, ask the agent for something and verify it respects the written rules.

### 5.3 Wizard `/wf-init` (greenfield + legacy)

Slash command that orchestrates the complete workflow bootstrap in a project. Split architecture — the orchestrator (`templates/commands/wf-init/_base.md`) is the only thing attached to the chat; phases, deterministic Builder scripts and lib contracts/helpers (`state.md`, `state-helpers.sh`, `builder.md`, `builder-core.py`, `builder-heavy.py`, `refresher.md`) live in `wf-init/` and the agent reads them from disk on-demand. This solves the "lost in the middle" problem a monolithic file would have: the agent only keeps the orchestrator + the active phase in context at any time.

The wizard phases:

- **Phase 0** — Self-contained prerequisite. Installs/verifies gentle-ai, runs `gentle-ai doctor`, confirms active agents for this project.
- **Phase 0b** — System health check. Verifies `gentle-ai doctor` critical checks, warns on disk space and Engram reachability.
- **Phase 0c**: Workflow feature selection. Lets the user toggle the Decision Ladder, testing, CI/CD, release-please, and the branch-PR override before discovery.
- **Phase 1** — Discovery (lists files, manifests, previous satellites, commits; also saves npm scripts to `discovery.commands` and the root folder summary for the AGENTS.md Commands / Project Structure sections).
- **Phase 2** — Migration of previous artifacts (if any with their own content).
- **Phase 3** — Mode: greenfield vs legacy (auto-detect + confirmation).
- **Phase 4** — Reverse engineering (legacy only).
- **Phase 4.6**: Testing stack setup (conditional, only if testing is enabled in Phase 0c). Detects or installs the selected testing layers (unit, integration, E2E), asks about the optional extras (coverage targets, visual regression, Page Object Model), and registers the Playwright MCP when applicable. Layer detection checks wiring, not just dependencies: a Playwright dependency without `playwright.config.ts` counts as NOT configured and the wizard offers to generate the config. The Page Object Model extra stages a minimal `e2e/pages/HomePage.ts` scaffold plus an AGENTS.md convention line.
- **Phase 4.7** — CI/CD configuration (conditional, only if CI, CD, or release-please is enabled). Collects AI reviewer, security review, conventional commits, release-please, E2E in CI, and tag-based deploy preferences; writes no files here.
- **Phase 5** — Minimum questions (4-5 depending on path).
- **Phase 6a**: Deterministic assembly (Builder-Core): `AGENTS.md`, packaged protocols, and per-IDE satellites into `.wizard-staging/` on disk (does not promote to the project root yet). Runs the deterministic script `wf-init/lib/builder-core.py` (`python3 "$WF_DIR/lib/builder-core.py" --state .wizard-state.json --staging .wizard-staging --raw "$WF_RAW" --wf-dir "$WF_DIR"`); it hard-fails on unresolved placeholders instead of guessing. List state fields render as UTF-8 markdown bullets (`critical_constraints` → readable rule list, never escaped JSON); missing satellite templates hard-fail with the affected IDE listed instead of skipping silently. The Testing Approach section is built from the active test layers: it carries the coverage matrix, the Playwright guidance, and, when E2E is active, the `data-testid` convention.
- **Phase 6b** — Deterministic assembly (Builder-Heavy): per-IDE commands, post-commit hook, testing configs, and CI/CD into `.wizard-staging/`. Runs the deterministic script `wf-init/lib/builder-heavy.py` with the same argument contract (B7-B9).
- **Phase 7** — Human review gate (preview incl. the Phase-8 install side effects — husky/commitlint/vitest/playwright installs and package.json script additions — approval).
- **Phase 8**: Write, handle `.gitignore`, install post-commit hook (detects AGENTS.md drift), commit. When Windsurf is active, re-inserts the Gentle AI legacy path bridge rule for Windsurf/Devin after the staging copy (portable head/tail/cat, verified with a loud failure check). The staging router does not carry the rule. Validates the `AGENTS.md` `wf-version` footer is a concrete semver (never `latest` or an unresolved placeholder) and fails loudly if it is not. A non-semver footer blocks every `/wf-init` and `/wf-refresh`. It also cross-checks the footer against the state's `wizard_version` and warns on mismatch (it does not abort, so a manually advanced footer does not break a refresh). When conventional commits is active it neutralizes Husky's factory `pre-commit` (`npm test`) with an inert hook unless GGA-local wrote one or a non-factory user hook exists (watch-mode scripts would hang every commit); the dummy-test creation globs the whole tree instead of one hardcoded path.

**How it is invoked**: with `install.sh` it is installed as a global slash command on all detected IDEs. You invoke it with `/wf-init` from any repo. The agent detects and reads the phase files from the repo as it progresses.

### 5.4 Project-specific satellites: what they are and why we need them

**Important clarification**: gentle-ai does NOT generate project-specific satellites. gentle-ai is **global**: it only knows about your machine (persona, skills, MCPs, permissions). It has no way to know your individual repo or how to "point" to your project's specific `AGENTS.md`. **All project satellites are generated by the `/wf-init` wizard**.

#### What gentle-ai installs globally (NOT project satellites)

These files live in `~/`, are common to all your projects, and do NOT know your repo:

- `~/.claude/`: persona, skills, MCP wiring.
- `~/.windsurf/`: persona, MCP, skills (Plan Mode).
- `~/.kiro/steering/gentle-ai.md`: global steering.
- `~/.config/opencode/`, `~/.codex/`, `~/.gemini/`, etc.

#### What your `/wf-init` wizard generates (these ARE project satellites)

These live in the repo. Each one connects its specific IDE to THIS project's `AGENTS.md`:

- `AGENTS.md` — the content (source of truth).
- `CLAUDE.md` with `@AGENTS.md` — only when Claude Code is an active IDE (Claude Code does not read AGENTS.md natively).
- `.github/copilot-instructions.md` — self-contained always-on gates + project facts (Copilot's progressive skill disclosure is unreliable, so the wizard inlines what Copilot must comply with; see "Satellite templates" below).
- `.cursor/rules/project.mdc` (optional in 2026; Cursor already reads AGENTS.md natively).
- `.windsurf/rules/project.md` with `trigger: always_on` (Windsurf does not read AGENTS.md).
- `.kiro/steering/project-context.md` (Kiro partial).
- `GEMINI.md` (Gemini CLI partial) — `ANTIGRAVITY.md` (Antigravity CLI).
- `.devin/rules/project.md` — generated whenever Windsurf is active, reusing the Windsurf satellite (Devin is a Windsurf fork; see spec Step B6 in `wf-init/lib/builder.md`).
- `post-commit` hook for drift detection.
- Exceptions in `.gitignore` so satellites are versioned.

#### How both layers coexist without clashing

When you open an IDE in a project, the agent loads both:

1. **gentle-ai global config** → persona, skills, MCPs, permissions.
2. **Project-specific config (satellites)** → repo context.

Example with Kiro:

```
~/.kiro/steering/gentle-ai.md           ← gentle-ai global: persona + skills bindings
.kiro/steering/project-context.md       ← our satellite: points to repo's AGENTS.md
```

Both files are in `steering/`, both load with `inclusion: always`, they don't conflict because they are different files. gentle-ai gives you "how I work in general"; our satellite gives you "how I work in THIS particular repo". **They are complementary, not redundant.**

#### Satellite templates

**`CLAUDE.md`**:

```markdown
@AGENTS.md

<!--
MIGRATION NOTE: Claude Code does not read AGENTS.md natively (June 2026).
This file imports AGENTS.md via @-syntax. When Claude Code adopts AGENTS.md
native support, delete this file. Feature request: github.com/anthropics/claude-code/issues/6235
-->
```

**`.github/copilot-instructions.md`** (self-contained, always-on):

Copilot does read `AGENTS.md` natively in 2026, but its **skill discovery is progressive**:
only the `name+description` of a skill stays resident, and the SKILL.md body only loads when
the model decides it is relevant. That makes chained wizard protocols (the ladder and the testing
rules) unreliable when they live only in skills/AGENTS.md. The wizard therefore generates a
self-contained instructions file that inlines the mandatory gate checklist, the active
protocols' requirements, and the project facts — with zero dependence on AGENTS.md or on skill
discovery. It is rendered by the shared `render_resolved` pipeline (same `<if>` conditionals
and `{{placeholders}}` as `AGENTS.router.md`), so the active protocols and facts never drift
from AGENTS.md.

```markdown
# GitHub Copilot Instructions — <project>
...
## ⛔ MANDATORY WORKFLOW GATE (before ANY edit, write, or generation)
- Features table (only ACTIVE features) + GATE CONFIRMATION CHECKLIST, output VERBATIM
- Hard rule: one turn = one action
- Active protocol sections (only those the user enabled): 🪜 wf-ladder
- Project facts (same placeholders as AGENTS.md): Commands, Code Style, Layout, Testing
  Approach, Project MCPs, Critical constraints, Validate before done
- Deep-dive references to .github/skills/* and registered / commands
<!-- wf-version: ... features: ladder=..., ci=..., cd=..., release=... -->
```

**`.cursor/rules/project.mdc`** (OPTIONAL in 2026):

```markdown
---
description: Project context. Applies to all files.
globs: ["**/*"]
alwaysApply: true
---
@AGENTS.md
<!-- MIGRATION NOTE: Cursor reads AGENTS.md natively. This satellite only if you need globs/activation modes. -->
```

**`.windsurf/rules/project.md`**:

```markdown
---
trigger: always_on
---
# Windsurf Rules — Project Context
Apply the conventions defined in `AGENTS.md` in all your responses.
@file ../AGENTS.md

<!-- Windsurf/Devin compatibility: Devin reads AGENTS.md natively, so no separate .devin/rules/ is needed.
     Project-level skills are written to both .windsurf/skills/ and .devin/skills/ for dual IDE support. -->
```

**`.kiro/steering/project-context.md`**:

```markdown
---
inclusion: always
---
# Kiro Steering — Project Context
Apply the conventions defined in `AGENTS.md` in all your responses.
```

**`GEMINI.md`** (if Gemini CLI) / **`ANTIGRAVITY.md`** (if Antigravity CLI):

```markdown
# Gemini CLI Context
Apply the conventions defined in `AGENTS.md` in all your responses.
@AGENTS.md
```

**`.opencode/AGENTS.md`** (if OpenCode) / **`.codex/AGENTS.md`** (if Codex CLI):

```markdown
<!--
OpenCode/Codex read AGENTS.md from the repository root natively (no @-import
syntax). This satellite exists for parity with the other IDE satellites and
simply points back to the source of truth.
-->
Project rules: see `AGENTS.md` at the repository root — OpenCode loads it automatically.
```

Both templates live in `templates/satellites/` (`opencode.tmpl`, `codex.tmpl`). A missing
satellite template is a hard builder failure naming the affected IDE — never a silent skip.

#### About `.gitignore`

Many developers have `.cursor`, `.windsurf`, `.kiro` in their global gitignore because historically they were local config. With this architecture **they must be versioned**. The wizard automatically adds exceptions to the project's `.gitignore`:

```gitignore
# AI agent satellites — project files, not local config
!.cursor/
!.windsurf/
!.kiro/
!.github/copilot-instructions.md
```

And uses `git add -f` to force tracking. If you add it manually with zsh shell, **use single quotes** because `!` with double quotes triggers history expansion:

```bash
echo '!.cursor/' >> .gitignore   # ✓ works
echo "!.cursor/" >> .gitignore   # ✗ zsh: event not found
```

### 5.5 Context auto-update

Solves two different problems:

**Problem A**: the project evolves (stack, scripts, structure) and `AGENTS.md` becomes outdated.

**Problem B**: the workflow evolves (improved templates, corrected frontmatter) and the repo files are left on an old template version.

#### Golden rule: never auto-apply, always propose

`AGENTS.md` always has human curation in the loop. The mechanisms only detect and propose, never apply on their own.

#### Solution Problem A: the project evolves

**Trigger 1 · Git hook post-commit**. Detects changes to key files (`package.json`, `tsconfig.json`, framework configs) and warns without blocking the commit:

```
┌─────────────────────────────────────────────────────┐
│  ⚠  AGENTS.md may need update                      │
└─────────────────────────────────────────────────────┘
  Changed: package.json, vite.config.ts
  Run: /wf-refresh to update AI agent context.
```

**Git hooks run ONLY locally**, not on GitHub or CI. Each developer installs them on their machine. The distribution problem is solved with **Husky** (configured in the CI/CD block), which registers hooks via `package.json` so they install automatically with `npm install`.

**Trigger 2 · Slash command `/wf-refresh`**. When invoked, the agent runs eight phases (builder-driven, orchestrated by `wf-init/lib/refresher.md`, using `wf-init/lib/state-helpers.sh` for state access). The command bootstrap first extracts and runs refresher.md's **Setup: create helper library** section so `${WF_DIR}/lib/refresh-lib.sh` exists before any phase sources it, and its `_extract_phase` helper is **placeholder-safe**: awk programs use a getline loop in BEGIN (plus brace-form shell positionals) instead of any bare dollar+digits tokens, because OpenCode expands those tokens in command bodies as positional placeholders (`placeholderRegex /\$(\d+)/g` in `session/prompt.ts`), which used to inject `"undefined"`/empty strings and break extraction on every phase. The block-coverage counter also tolerates `grep -c`'s exit status 1 when a single-block phase emits no markers (the assignment would otherwise propagate that status into any caller not wrapped in `||`, killing the run under `set -e`). **Resume/pending state lives OUTSIDE `${WF_DIR}`**: the bootstrap exports `WF_STATE_DIR` as `<TMPDIR-with-trailing-slash-stripped>/wf-refresh-state-<cksum-of-pwd>` (macOS `TMPDIR` ends in `/`; stripping it avoids paths like `.../T//wf-refresh-state-...`) and both `.wizard-resume-phase` and `.wizard-pending-prompts` live there (plus the Phase R5 full review file), because the bootstrap `rm -rf`s `${WF_DIR}` at the start of every run — a documented re-run before resuming used to destroy pending resume state (field report M3):

- **Phase R-1** (Global): Fetch wizard version from GitHub; skip refresh if already up-to-date. If the remote version cannot be fetched, refresh ABORTS with a clear error (no hardcoded fallback version, no silent continuation). If a global update is applied (install.sh succeeds), refresh STOPS and asks for a new session + re-run, so the updated wizard drives the refresh. In non-tty runs the `Update global commands?` prompt has restart semantics: when unanswered it emits `GENTLE_AI_WF_REFRESH_NEEDS=prompt=Update global commands?` and exits 3 IMMEDIATELY (before R0-R4 do any work), because answering `yes` replaces the wizard itself and would waste everything computed afterwards.
- **Phase R0** (Validate): Validate `.wizard-state.json` structure and detect active IDEs
- **Phase R1** (Discover): Re-discovers the project (stack, node engine, commands from `package.json`, etc.) and detects drift — writes accepted drift to the STAGING state, not root. **Commands are ALWAYS re-detected from `package.json` on every refresh** (never gated on empty state); the fresh list is merged with descriptions from the current AGENTS.md Commands section (the parser strips backticks and allows `:` inside script names, so both the documented rich format `` - `npm run dev` — Start development server `` and canonical npm scripts like `test:e2e` merge correctly) and written as backticked bulleted list (`- \`npm run <name>\` — <description>`) to `discovery.commands`, logging the honest merged/total description count instead of an unconditional success message. A **regeneration-first merge** replaces the old conditional backfill: structure is regenerated from the live filesystem tree (depth 2, excluding `node_modules`, `.git`, `dist`, `build`, `coverage`, `playwright-report`, `test-results` and `.wizard-*` — both the directories themselves and their children) while preserving the original section's entry order and inline comments (tree-drawing glyphs like `├──`/`│` are normalized before matching so comments survive from tree-formatted sections; surviving entries keep their comments, genuinely new directories are appended, removed ones dropped). A **downgrade guard** never trades a richer section for a poorer one: fenced/tree-formatted originals are preserved verbatim (the deterministic regeneration is dirs-only at depth 2), and when regeneration would drop every inline comment the original had, the original section wins with a warning. MCPs are re-detected from known config files (`.mcp.json`, `.cursor/mcp.json`, `.windsurf/mcp.json`, `.github/copilot-instructions.md`) and merged with purpose/setup from the old AGENTS.md 3-column table. Code Style is composed from structured `discovery.conventions.{naming,components,imports,tests,css,state}` fields as bullets when any is present, falling back to preserving the AGENTS.md section verbatim when all are absent. The old "backfill only when empty" guard is replaced — richer regenerated content supersedes stale preserved text. In non-tty runs the `Use updated project info?` prompt is **fail-fast**: when unanswered, R1 stops IMMEDIATELY (before any staging work), emits `GENTLE_AI_WF_REFRESH_NEEDS=prompt=Use updated project info?`, writes `.wizard-resume-phase`, and exits 3 — continuing on a default answer would build staging from stale info and an answer collected later would have no consumer.
- **Phase R2** (Migrate): Migrate state schema; run unconditional legacy normalization (testing.layers dict→array, flat `discovery.stack_key`→nested); ask about new optional features. Feature prompts (`Enable <FEATURE>?`) share R1's fail-fast semantics: unanswered non-tty prompts stop R2, emit the manifest, write `.wizard-resume-phase`, and exit 3
- **Phase R3**: Re-run Builder (B1-B9) to generate all artifacts into `.wizard-staging/` via the deterministic scripts `lib/builder-core.py` + `lib/builder-heavy.py` (first snapshots the pre-Builder managed files for deletion detection)
- **Phase R4**: Before diffing, a **placeholder gate** fails the phase loudly if any wizard-owned template namespace (`{{answers.*}}`, `{{discovery.*}}`, `{{features.*}}`, `{{version}}`, `{{PROTOCOL_BODY:*}}`, etc.) appears unresolved in staging. Arbitrary `{{ }}` text quoted in project docs is NOT flagged. Then compares the R3 baseline snapshot with staging using SHA256 hashes; classify files as add/update/delete/unchanged (the staged `wizard-state.json` copy is never part of the plan). After classification, R4 computes a **behavioral diff over curated config keys** (`auto_improve`, `e2e_in_ci`, `release_ai_summary`, `release_ai_provider`) between the project copy and staging for every updated file, persisting flips into the plan's `behavioral_changes` array so Phase R5 can surface them FIRST instead of hiding a semantic toggle among hash-classified mechanical updates
- **Phase R5**: Show grouped diff and collect user approvals; unanswered review prompts batch into ONE combined manifest (plus `apply_mode`) with a `.wizard-resume-phase=R5` marker; offers apply+commit, apply without commit, or cancel (cancel cleans the staging directory). Behavioral changes print first, then previews per `WF_REFRESH_PREVIEW`
- **Phase R6**: Apply approved changes only; on approval commit via an explicit pathspec (the user's other staged work is never unstaged), then update the STAGING state's `build_plan` (promoted to root by the final copy) and write `.wizard-managed-files.json`; a failed commit rolls the working tree, the index and the state back; in apply-only mode files are copied to the working tree but never staged or committed; a fully declined refresh writes nothing

**Trigger 3 · Rule in AGENTS.md**. The most effective. A line in "Behavior Preferences":

```markdown
- If in any task you detect that existing code contradicts something in this
  file (a script that doesn't exist, a folder not where Project Structure
  indicates, a convention the code doesn't follow), report it at the end
  of your response with the tag `[AGENTS.md drift detected: <description>]`.
  Do not fix the AGENTS.md yourself.
```

The agent already reading the code is the one who best detects inconsistencies. Zero operational cost.

#### Solution Problem B: the workflow evolves

Footer of `AGENTS.md` with version + GitHub source URL + accepted optional features:

```markdown
<!-- wf-version: 0.7.1-beta.1 | source: github.com/hugoafj/ai-workflow-wizard | stack: vite-react-ts | features: ladder=no, tdd=no, routing=no, ci=no, cd=no, release=yes -->
```

The `features` field is new and critical. It tracks which optional features of the wizard the user accepted or rejected. Without it, every time the wizard ships a new feature, the system wouldn't know if the user already considered it or if it's new to them.

**Three wizard distribution options**:

1. **GitHub as source of truth** (recommended). Wizard lives in repo `github.com/hugoafj/ai-workflow-wizard` with tagged versions. Agent fetches + compares when running `/wf-refresh`.
2. **Package manager** (npm/composer/pip). For large teams.
3. **Manual convention with changelog**. No additional infrastructure.

**Recommendation**: Option 1 to start.

#### Builder-driven refresh mechanism

`/wf-refresh` is now builder-driven: it re-runs the same Builder (B1-B9) that `/wf-init` uses, ensuring a single source of truth. This solves the core problem: when new wizard versions ship with new features, the user does NOT have to clean up and re-run the wizard. Refresh integrates them incrementally using hash-based comparison.

**Key concepts**:

1. **Single source of truth**: The Builder (B1-B9) is the only rendering engine, implemented as the deterministic scripts `lib/builder-core.py` (B1-B6) and `lib/builder-heavy.py` (B7-B9). No parallel template logic in `/wf-refresh`.
2. **Hash-based diff**: Each file is compared using SHA256 hashes. Unchanged files are skipped; only changed files are proposed.
3. **Explicit approval**: User approves adds, updates, and deletions separately before any changes are applied.
4. **Custom content preservation**: Sections inside `<!-- WF: DO NOT REGENERATE -->` markers in `AGENTS.md` are preserved.
5. **State migrations**: Schema and feature migrations are applied automatically; user is asked about new optional features.

**Phases R-1, R0, R1–R6 in detail**:

- **Phase R-1 · Global version check**: Fetches wizard version from remote; exits early if already up-to-date. When a global update is applied, it stops with a "new session + re-run" message so old and new wizard versions never mix in one session — and it exits 3 (not 0) so the orchestrator's `|| exit` actually stops instead of rolling into R0 with stale wizard code. In non-tty runs the `Update global commands?` prompt is restart-semantics: if it cannot be answered, R-1 emits `GENTLE_AI_WF_REFRESH_NEEDS=prompt=Update global commands?`, exits 3, and NO refresh work runs (R0-R4 would be wasted once `install.sh` replaces the wizard). On resume (`WF_REFRESH_RESUME=1`) R-1 consumes the answer first: `yes` runs install.sh then exits 3 demanding a new session; `no` continues the pipeline. When the remote version cannot be fetched, R-1 aborts (exit 1) with a clear network-error message instead of continuing with a hardcoded version or the local one — no silent stale refresh.
- **Phase R0 · Pre-flight state checks**: Validates `.wizard-state.json` exists and contains minimal required structure; detects active IDEs; copies the state to staging.
- **Phase R1 · Project content drift**: Re-discovers the project (stack, node engine, commands from `package.json`, etc.) and detects changes; accepted drift is written to the STAGING state (a root-only write would be clobbered by R6's final promotion). A conditional **backfill** then preserves richer documentation from the current `AGENTS.md` into flat staging discovery fields: `discovery.commands`, `discovery.conventions.code_style`, `discovery.conventions.structure`, and `mcps` (the last parsed from the `## Project MCPs` markdown table into `[{name, active}]`). Each field is backfilled only when the staging value is empty AND the current section differs from the builder's generic fallback (`npm run build`, `camelCase`, `flat`, `None configured`), so an already-rich state is never overwritten and newly-added wizard sections still flow in from the fresh router.
- **Phase R2 · State/schema migration**: Migrates `.wizard-state.json` to current schema; runs an unconditional, idempotent legacy normalization (`testing.layers` dict → array, flat `discovery.stack_key` → nested `discovery.stack.stack_key`); **normalizes corrupted `discovery.node_engine`/`discovery.npm_major` values (`"None"` or `""`) to `null` so the builder's coalesced defaults ("22"/"10") apply correctly**; asks about new optional features.
- **Phase R3 · Builder re-run**: Re-runs B1-B9 to generate all artifacts into `.wizard-staging/` by executing the deterministic scripts directly: `python3 "$WF_DIR/lib/builder-core.py"` (B1-B6) then `python3 "$WF_DIR/lib/builder-heavy.py"` (B7-B9), both with `--state .wizard-staging/wizard-state.json --staging .wizard-staging --raw "$WF_RAW" --wf-dir "$WF_DIR"` (the `--raw` base and `--wf-dir` come from `wf-refresh/_base.md`). No sub-agent delegation. It **never follows the `/wf-init` phase 7/8 tail** (no `wf_phase_done phase6 phase7`, no `cat phase7.md`). After Builder-Heavy validation it returns to Phase R4. Staging validation checks the generated artifacts (e.g. `AGENTS.md`) and requires the staged state copy (`.wizard-staging/wizard-state.json`, written by R0) to exist. The builders fetch over IPv4-first DNS (preferring `AF_INET` so `urllib` does not hang on IPv6-first resolution) and print a `>>> fetching <url>` progress line per download plus per-attempt failure lines on retry. **Step 0 runs first**: it snapshots the pre-Builder `managed_paths`/`generated_files` into `.wizard-refresh-baseline.json` because the Builder overwrites `build_plan` with the new staging set. The baseline snapshot, both builder invocations, and the validation block are fenced bash blocks that `_extract_phase` concatenates in order, with a post-extraction coverage check (count of ```bash fences vs extracted blocks) that fails loudly instead of silently truncating multi-block phases. After `preserve_custom_agents` and `reinsert_legacy_bridge`, R3 runs a **dynamic `EXPECTED[]` validation** built from the state features (the active ladder skill and protocol, the always-included commands per active IDE, quality-guard when CI, release-please+commitlint when release, vitest/playwright when testing layers). A missing artifact fails the phase loudly.
- **Phase R4 · Hash-based diff**: Compares the R3 baseline snapshot (not the live `build_plan`, which the Builder already overwrote) against staging; classifies files as add/update/delete/unchanged, with `deleted_modified` flagged when the user edited a file since the last refresh. **Updated entries now carry `local_modified: true` when the working-tree file differs from HEAD (fallback: recorded `generated_files` hash), so locally-modified files are tracked separately.** An explicit `DEPRECATED_PATHS` list is extended with **per-IDE skill dirs for the deprecated commands** (`wf-cicd`, `wf-cleanup`, `wf-refresh`, `wf-init`, and the retired wizard commands) across **8 IDE skill roots** (`.claude/skills`, `.cursor/skills`, `.opencode/skills`, `.windsurf/skills`, `.codex/skills`, `.kiro/skills`, `.github/skills`, `.devin/skills` when Windsurf active). These are deleted even when absent from the baseline, because they are installed globally by `install.sh` and never belong in a project. Deletion paths are deduplicated (`unique_by(.path)`). The `## Project MCPs` table now renders **3-column (`| MCP | Purpose | Required setup |`)** when purpose/setup are known (from re-detection + merge), falling back to 2-column (`| MCP | Active |`)** otherwise.
- **Phase R5 · Review gate**: Prints **behavioral changes FIRST** (curated keys like `ci.auto_improve` whose value flips between the project copy and staging — a semantic toggle must not hide among N mechanical updates), then shows a real content preview (added → staged content; updated → `diff -u` against staging; deleted/deleted_modified → current content), bounded by `MAX_PREVIEW_LINES` (default 120) per file, then collects user approvals. The full review is ALWAYS written to `$WF_STATE_DIR/refresh-review.md` (outside `.wizard-staging`, so R6's cleanup trap cannot delete it) with its path printed; inline verbosity follows `WF_REFRESH_PREVIEW=full|summary|none` — default `full` keeps the historical complete dump, `summary` prints counts + behavioral changes only, `none` only the pointer. Then collects user approvals. **Dedicated warning block lists `updated` files with `local_modified: true` and asks a separate approval: `Overwrite locally-modified files?` (stored as `build_plan.approval.overwrite_local`).** The final gate offers three choices: apply+commit (default), apply without commit, or cancel. **In non-tty/agent contexts, if any prompt lacks an answer, R5 emits a structured manifest `GENTLE_AI_WF_REFRESH_NEEDS="prompt=<p1>|prompt=<p2>|...|apply_mode=..."` and exits with code 3 (not 2), leaving staging/plan intact. Review prompts accumulate during the review and are emitted as that single manifest right before approvals are stored; each prompt satisfied from `WF_REFRESH_ANSWERS`/`WF_REFRESH_DEFAULT_ANSWER`/cancel semantics is removed from `$WF_STATE_DIR/.wizard-pending-prompts` immediately, so resumed runs never re-ask already-answered questions. The restart-semantics `Update global commands?` prompt never reaches this manifest — R-1 resolves it (or cuts the run) before any refresh work.** `WF_REFRESH_RESUME=1` re-enters via the `$WF_STATE_DIR/.wizard-resume-phase` marker: pre-R5 stops (R1/R2 fail-fast prompts) resume at exactly the marked phase — earlier phases skip themselves, the marked phase consumes `WF_REFRESH_ANSWERS` and re-runs fully — and the pipeline flows through R5 normally; runs stopped at R5 write a marker of `R5`, so on resume R-1..R4 skip via that same marker and R5 consumes it before re-running the review (the legacy no-marker path still validates staging/plan exist and re-enters R5 with the preserved state).** In non-tty contexts the choice comes from `WF_REFRESH_APPLY_MODE=commit|apply-only|cancel`; anything else aborts instead of guessing — the missing-value case emits `GENTLE_AI_WF_REFRESH_NEEDS=apply_mode=` with exit 3, the same contract as every other gate.
- **Phase R6 · Apply and close**: Applies approved changes, commits them, and only then updates the STAGING state's `build_plan` and writes `.wizard-managed-files.json` (the final `cp` promotes the complete staging state to root). A failed commit rolls the working tree, the index and the state back. The Project Structure is regenerated on the final tree, so an approved refresh is not offered again on the next run. Bookkeeping only runs when at least one category is approved; a declined refresh writes nothing. In **apply-only mode**, approved `deleted`/`deleted_modified` files are removed with plain `rm -f` (unstaged), **not** `git rm`, and the closing message accurately states: "changes left in the working tree (unstaged). Review with: git status && git diff". Locally-modified `updated` files are only overwritten when `overwrite_local` approval is true. The commit uses an explicit pathspec so it contains only approved paths and never unstages unrelated user work. The staged `wizard-state.json` copy is excluded from the diff plan.

**New optional features** are handled in Phase R2:

When running `/wf-refresh`, Phase R2 does the following:

1. Reads `.wizard-state.json` features (e.g., `features.decision_ladder`).
2. After `migrate_state`, checks the protocol features that can be enabled without
   the full phase47-cicd questionnaire: `decision_ladder`.
3. **For each feature not in the local state**: asks you. In non-interactive/agent
   contexts set `WF_REFRESH_ANSWERS="<prompt>=yes|..."` per-question (exact prompt
   match) or the global `WF_REFRESH_DEFAULT_ANSWER=yes|no` so the migration can
   proceed without stdin; otherwise it fails loudly instead of silently defaulting
   to NO. The per-question map wins over the global default, and an answer value
   that is not yes/no aborts with a clear error.
   (`ci`, `cd`, and `release_please` are NOT asked here — they require the full
   phase47-cicd questionnaire and are configured via `/wf-settings` or `/wf-init`.)
4. Example:

```
New optional feature available: decision_ladder
Enable decision_ladder? [y/n]
```

5. For each user response, updates `features.*` in `.wizard-state.json`.
6. Features marked as disabled are recorded explicitly and not asked again in future refreshes.

#### Projects set up by an older wizard

Projects initialized before the SDD removal carry files and state that the current wizard no longer uses. The next `/wf-refresh` migrates them:

- **Retired wizard files** (`wf-tdd`, `wf-sdd-trigger`, `wf-orchestrator`, `sdd-lite`, the `sdd/*` protocols, `sdd-new.md`) are removed when they still match the hash recorded at install. A file you edited, or one with no recorded hash, is listed for approval, and it stays if you answer no.
- **Declined removals** are recorded in `.migrations.retired_pending` and asked again on the next run.
- **Retired files that are not in git's HEAD** (files you created or staged yourself) are never offered for deletion. `/wf-refresh` prints one notice for each, then records them in `.migrations.kept_not_in_head` and stays quiet about them on later runs.
- **State** moves to schema 4. `features.tdd_protocol` maps to `features.testing`, so your test infrastructure stays. The `sdd`, `routing_abc`, and `tdd_mode` keys and the `phase45` and `phase46b` phase keys are dropped. An in-flight pointer on `phase45` or `phase46b` resumes at `phase46`. The migration is stamped once in `migrations.sdd_removed`.
- **`openspec/`** is removed only after an explicit "yes" to "Remove the SDD openspec/ directory from this project?" (default No). It is removed only when git tracks it and it is clean, and only its tracked files go.
- **`.wf-status`** is deleted only when it carries the old SDD drift text. The post-commit hook writes a new one when drift appears.

SDD text inside your `<!-- WF: DO NOT REGENERATE -->` blocks is reported with line numbers. The refresh never rewrites those blocks, so you remove those lines by hand.

#### When refresh is NOT enough and you need to re-run the wizard

Rare cases where refresh cannot resolve the change:

- **Complete restructuring of the AGENTS.md schema** (e.g., if in v3.0 we change from 7 sections to 4 renamed sections). In that case the footer marks `major-version-bump-required: true` and refresh recommends re-running `/wf-init` in migration mode (preserves custom content marked with `<!-- WF: DO NOT REGENERATE -->`).
- **Fundamental change in workflow architecture** (e.g., if we decided to switch from gentle-ai to Superpowers as foundation). In that case refresh does not apply; it is a manual migration with explicit guidance.

These cases are rare (1-2 times per year max) and are announced in the wizard changelog with a "Breaking changes" section. **Design goal: 99% of workflow evolutions are handled via refresh, not by re-running the wizard**.


### 5.6 Step-by-step tutorial · Test the wizard on a clean project

> The wizard (`/wf-init`) verifies and installs gentle-ai automatically in its Phase 0 — you don't need to do it beforehand. You can run the wizard in any project state: clean, with previous artifacts, or legacy with existing code.

#### Step 1 · Open the project from its root

This is the only thing that matters before running the wizard: **open the IDE exactly from the repo root folder**, not from a parent folder. If you open from the parent, the agent won't find `AGENTS.md` because its working directory is not the repo's.

```bash
# Correct
cd ~/projects/my-project
code .          # VS Code / Cursor / Windsurf from root
claude          # Claude Code from root

# Incorrect — the agent sees ~/projects/, not ~/projects/my-project/
cd ~/projects
code my-project
```

If the project already has previous workflow artifacts (AGENTS.md, satellites, hook), the wizard detects them in Phase 1 and asks whether to migrate or replace them — you don't have to delete them manually.

#### Step 2 · gentle-ai handles Phase 0 of the wizard

**You don't need to verify gentle-ai manually** before running the wizard. Phase 0 does it all: detects if installed, installs if not, checks if update needed, and runs `gentle-ai doctor`. You just answer the questions it asks.

If you want to check your machine's status at any time outside the wizard:

```bash
gentle-ai doctor
```

#### Step 3 · Have the wizard ready

The wizard lives in the `workflow-wizard` repo: the orchestrator is `templates/commands/wf-init/_base.md` and the phase files are in `wf-init/`. Make sure you have the repo cloned on your machine. The agent detects the location automatically.

#### Step 4 · Open a new Claude Code session (or your preferred IDE/CLI)

> Important: **new session**, do not continue one you had open. The wizard needs to start from scratch.

```bash
cd ~/path/to/your-project
claude
```

(or `cursor`, `opencode`, etc., depending on your IDE)

#### Step 5 · Paste the orchestrator as the first prompt

Open `templates/commands/wf-init/_base.md` in another editor. Select all (Cmd+A / Ctrl+A). Copy it. Paste it into the new AI IDE session as the first message.

> Don't add anything before or after. The agent will locate the phase files on your machine and read each one as it progresses. You don't need to attach anything else.

#### Step 6 · Follow the interactive phases

The agent will process the wizard phase by phase. **Each phase ends with a PAUSE and a question**. Answer, wait for the next phase, repeat.

What you will see, in order:

**Phase 0 — Self-contained prerequisite**. The agent checks if gentle-ai is installed. If not, it installs it automatically (asks for confirmation and explains why it is mandatory). If already installed, it compares local vs remote version and recommends whether the update is mandatory or suggested. Then runs `gentle-ai doctor` and shows you the health summary. At the end it asks which configured agents you will use in this project — that determines the satellites generated in Phases 6a and 6b.

**Phase 1 — Discovery report**. The agent lists the files it found, the detected stack, etc. Approve to continue.

**Phase 2 — Migration**. If it found satellites with their own content (shouldn't happen on a clean project), it asks what to do. On a clean project it jumps directly to Phase 3.

**Phase 3 — Mode**. Tells you if it classified as greenfield or legacy. Confirm.

**Phase 4 — Reverse engineering**. Legacy only. Reports detected conventions. Confirm or correct.

**Phase 4.6: Testing stack setup** (conditional, only if testing is enabled). Detects or installs the selected testing layers, and asks about the optional extras (coverage targets, visual regression, Page Object Model).

**Phase 4.7 — CI/CD configuration** (conditional, only if CI, CD, or release-please is enabled). Collects AI reviewer, security review, conventional commits, release-please, and tag-based deploy preferences; writes no files here.

**Phase 5 — Minimum questions**. 4-5 questions depending on path. Answer short and specific. The key question is **which IDEs/CLIs you will use** — that determines the custom satellites generated.

**Phase 6a — Staging generation (Builder-Core)**. Runs the deterministic script `wf-init/lib/builder-core.py` (B1-B6), which assembles `AGENTS.md`, packaged protocols, and per-IDE satellites into `.wizard-staging/` on disk but does NOT promote them to the project root yet.

**Phase 6b — Staging generation (Builder-Heavy)**. Runs the deterministic script `wf-init/lib/builder-heavy.py` (B7-B9), which assembles per-IDE commands, post-commit hook, testing configs, and CI/CD into `.wizard-staging/`.

**Phase 7 — Review gate**. Shows you the complete AGENTS.md and the list of files to be created. **Read them carefully**. If something doesn't fit, say "let me edit X first" and describe the change. The agent adjusts and shows again.

**Phase 8 — Write and commit**. Only if you said "yes" in Phase 7. The agent writes files, handles `.gitignore`, installs the hook, does `git add -f` and `git commit`. **Does NOT push** — that's your decision.

#### Step 7 · Validate the result

After the wizard finishes, in another terminal:

```bash
# View the commit
git log -1 --stat

# Verify created files
ls -la AGENTS.md
ls -la CLAUDE.md   # only if you selected Claude Code
ls -la .github/copilot-instructions.md
ls -la .windsurf/rules/project.md   # if you checked Windsurf
ls -la .kiro/steering/project-context.md   # if you checked Kiro

# Verify the hook is executable
ls -la .git/hooks/post-commit
# Expected output: -rwxr-xr-x ...

# View the updated .gitignore
tail -10 .gitignore
```

Read `AGENTS.md` completely. Ask yourself:

- Does it correctly reflect your stack?
- Are the commands in the Commands section the real project ones?
- Does the Project Structure section make sense?
- Are the Critical Constraints accurate?

If something is wrong, edit it manually. The AGENTS.md is yours.

#### Step 8 · Test agent behavior

**Restart the IDE** (close Claude Code, open it again) so it loads the new context.

Ask it for a small task. Example for a React project:

```
Create a Button component with primary and secondary variants,
using this project's conventions.
```

Validate:

- Did it use the AGENTS.md conventions? (export style, type vs interface, Tailwind syntax, etc.)
- Did it place it in the correct folder according to Project Structure?
- Before committing, did it show the diff and wait for your OK? (review gate)

If all goes well, the AGENTS.md is working.

#### Step 9 · Test the drift detection hook

Modify a file the hook considers "structural", for example `package.json`:

```bash
# Open package.json and change the description (any simple field)
nvim package.json

git add package.json
git commit -m "test: verify post-commit hook fires"
```

Immediately after the commit, you should see the hook notice:

```
┌─────────────────────────────────────────────────────┐
│  ⚠  AGENTS.md may need update                      │
└─────────────────────────────────────────────────────┘
  Changed: package.json
  ...
```

If you see it, the hook works. Revert the test commit:

```bash
git reset HEAD~1
git restore package.json
```

#### Step 10 · Next steps

With Block 1 working end-to-end:

- **Work a few days normally** with the agent on your project. Observe which AGENTS.md rules are well respected, which need adjustment, what's missing to document.
- **If the agent detects drift** (`[AGENTS.md drift detected: ...]` at the end of some response), run `/wf-refresh` to apply the complete Decision Ladder, or adjust manually.
- **When you're ready**, advance to Block 2 (ODD) to see how a substantial feature gets its feature document.


### 5.7 Ensuring multi-IDE fidelity · Strategy and specific fixes

This section complements the fidelity matrix with **real solutions** for IDEs that don't respect AGENTS.md well. It's the section you apply when an IDE on your team is second or third tier.

#### Before looking for complicated fixes: verify the basics

Lesson learned from real testing: if an IDE "doesn't respect AGENTS.md", the first check is **where the project is opened in the IDE**. If you opened a parent folder that contains your repo (`~/projects/`) instead of the repo itself (`~/projects/my-app/`), the IDE won't find AGENTS.md because it looks in the root of the opened folder, not in subfolders. This applies to Kiro, Windsurf, VS Code Copilot, practically all.

**Checklist before declaring an IDE "broken"**:

1. Verify you opened the project at the exact repo root (where `AGENTS.md` lives).
2. Verify the IDE's satellite exists and has content (`.kiro/steering/project-context.md`, `.cursor/rules/project.mdc`, etc.).
3. Close and reopen the IDE — some cache the previous session's context.
4. Verify with `git status` that the satellites are committed.
5. Explicitly ask the agent: "read AGENTS.md and tell me its main sections". If it responds correctly, the file is loading; if not, there's a real problem.

If all this passes and it still doesn't respect AGENTS.md, then apply the fixes in the following subsections.

#### General strategy

Three principles:

**1. AGENTS.md is the source of truth for humans and first-tier IDEs** (Claude Code, OpenCode CLI with Claude). Don't touch.

**2. For IDEs with their own native mechanisms** that don't load AGENTS.md well, it may be worth generating files in their native format with duplicated rules. This is tactical duplication: redundancy for reliability. **But before duplicating, validate the checklist above** — many times the problem is the opened folder location, not IDE fidelity.

**3. For absolutely critical rules**, treat them as "hard contract" — enforced not by the agent but by **CI/CD** (Block 6). Lint rules, type checks, AI review on PR. AGENTS.md suggests, CI enforces.

#### Fix for Windsurf with GPT and VS Code Copilot with GPT

GPT models are weaker at respecting secondary rules. Three options:

**Option A · Switch to Claude model in those IDEs when the project has critical rules**. This is the most direct.

**Option B · Inject rules into critical project files** as comments. For example, if you have a rule "always use `data-testid` on interactive components", add a `src/components/CONVENTIONS.md` file that's impossible to ignore because the agent reads it when exploring the folder.

**Option C · CI/CD enforce** (Block 6). Rules that GPT doesn't respect, CI catches: custom linter, AI review on PR with GGA, etc.

**Recommendation**: combine A + C. If you can't change the model, you depend 100% on CI.

#### Fix for hidden hooks in IDEs (OpenCode, VS Code Copilot, etc.)

The problem: the hook executes correctly but the IDE captures/hides stdout. Solution: make the hook **leave persistent evidence on the filesystem** in addition to stdout output.

**Recommended hook**: does three things instead of one:

1. **Prints to stderr** (better compatibility with IDEs that only show errors).
2. **Creates a `.wf-status` file at the repo root** when it detects drift. This file is visible in ANY file explorer, in ANY IDE, and persists until the dev reads and deletes it.
3. **On macOS**: system notification via `osascript` (optional, silently fails on Linux/Windows).

**Self-trigger guard**: the hook exits 0 on wizard refresh commits (subject matching `chore: refresh workflow to vX.Y.Z`) — those commits write wizard-managed files (AGENTS.md, IDE commands/satellites/skills, vitest/playwright configs) by design, and warning about them would re-trigger the very flow that produced the commit.

**Content of the `.wf-status` file when there is drift**:

```markdown
# ⚠ Workflow drift detected

**Commit**: <hash>
**Date**: <iso date>

The following structural files changed:
- package.json

## Action required

The AGENTS.md may be out of date with the project. Either:
1. Run `/wf-refresh` in your IDE/CLI to update AI agent context, or
2. If the changes don't affect AI context, delete this file: `rm .wf-status`

This file persists across IDE sessions until you act on it.
```

**How to use it**: when the dev opens the project in any IDE, they see `.wf-status` in the file tree. Open it, read the notice, act (refresh or delete). Impossible to miss.

**Add `.wf-status` to the project's `.gitignore`** so it doesn't get accidentally committed:

```gitignore
# Workflow drift status (local-only)
.wf-status
```

#### Summary of when to use which strategy

| Situation | Strategy |
|---|---|
| First-tier IDE (Claude Code, OpenCode + Claude) | Only AGENTS.md + satellite. Works. |
| Any IDE that seems not to respect AGENTS.md | First validate checklist above (correct folder, satellite exists, reopen IDE). |
| Windsurf / Copilot + Claude | AGENTS.md + satellite + strong dependency on CI/CD (Block 6). |
| Windsurf / Copilot + GPT | Consider switching to Claude model. If not, CI/CD is the only guarantee. |
| Hidden hooks in any IDE | Persistent `.wf-status` file. |
| Absolutely critical rules | Treat as hard contract: AI review on PR, custom lint, tests. AGENTS.md does not guarantee fidelity. |

### 5.8 Optional behavior improvements · wf-ladder

This section documents an optional improvement: the **Decision Ladder**, a short checklist that stops over-engineering before the agent writes code. It ships as the optional `wf-ladder` protocol.

#### The problem it solves

AI agents by default have a significant bias toward **over-engineering**: they tend to write new code when something equivalent already exists, add unnecessary abstractions, install heavy dependencies when a native feature suffices, write helpers already in the standard library. The result is bloated code, unnecessary dependencies, and costly maintenance.

#### The decision ladder

Before writing any code, the agent must follow this priority ladder. Only descend to the next step if the previous one doesn't apply.

1. **Does this really need to exist?** If not, skip it. (Extreme YAGNI.)
2. **Does it already exist in this codebase?** If yes, reuse instead of rewriting.
3. **Does the language's standard library already do it?** If yes, use the standard library.
4. **Is it a native platform feature?** If yes, use the native approach. Example: native HTML `<input type="date">` instead of installing a heavy calendar library.
5. **Is there already a dependency installed in the project that serves?** If yes, use it.
6. **Can it be done in a single line?** If yes, do it in one line.
7. Only if none of the above apply: write the minimum necessary code that works.

#### How it is enabled

Phase 0c asks whether to enable the Decision Ladder. When it is enabled, the router lists `wf-ladder` among its protocols, and the agent loads it before proposing an implementation. The `/wf-ladder` command (section 7.5) forces it on demand. The output lists each rung with its answer and ends with the rung that was used.

The ladder declares each rung and then stops for your confirmation before any code is written. That pause is the ladder's only interruption, and it exists because you chose to enable the ladder. To disable it, run `/wf-settings` and choose option 1.

#### Related frameworks (future reference, don't integrate now)

If in the future you evaluate replacing the gentle-ai foundation with another, the serious candidates are:

- **Superpowers** (`github.com/obra/superpowers`): 93k-150k stars. Agentic skills framework with a spec-first methodology, brainstorming, automatic worktrees, subagent-driven dev, strict TDD, code review. Works with Claude Code, Cursor, Codex, Gemini CLI, Copilot CLI, OpenCode, Pi, Antigravity, Kimi Code, Factory Droid. Created by obra (Jesse Vincent, ex-Anthropic). Technical difference with gentle-ai is small; community/maturity difference favors Superpowers. **Reason not to migrate now**: gentle-ai is already installed and validated in your setup, and Engram (persistent memory) is a real differentiator of gentle-ai that Superpowers has no equivalent for. The day you decide to migrate, the only thing that changes is section 4 of the master document (the foundation); the rest of the workflow stays the same because the foundation is replaceable by design.

- **Decision Ladder** — Anti-over-engineering prioritization pattern (origin: Ponytail project, `github.com/DietrichGebert/ponytail`). Integrated as a practice in this workflow (see section 5.8).

- **EDD (Evaluation-Driven Development)** — Pending evaluation. EDD means different things depending on context: prioritizing eval datasets in AI-internal systems (chatbots, agents, RAG), a variant of TDD for performance-critical code, or a generalist "pre-evaluation" approach. Useful if you build products that use AI internally; overkill for typical CRUD apps. Will be covered in Block 5 if the project warrants it.

---

## 6. Block 2 · Feature Tracking (ODD)

### 6.1 ODD philosophy

#### The problem it solves

Working with AI without structure produces a predictable pattern: vague prompt → code that seems to work → you ask for adjustments → the model "fixes" things → you lose context between sessions → after 3-5 iterations the code diverges. The industry calls it **vibe coding**: trusting that a good prompt and the smartest model are enough. They are not.

**ODD (Organic Driven Development)** keeps the explore, implement, and check loop, and adds one thing: substantial work leaves a durable record. Small, understood work stays lightweight. Substantial work gets one feature document that states what to build, what is done, and what the evidence was, so a session can end and the next one can resume without rebuilding the plan.

#### The principle

Explore first, then write. The agent reads the code and the requirements before it changes anything, and it asks you only about real product decisions. AI implements fast, so the slow phase is understanding what you want. If the target is clear before implementation starts, the agent reaches it quickly. If not, it moves fast in the wrong direction.

#### Two layers of context

- **AGENTS.md** = persistent **project** context. How to work in this repo.
- **Feature document** = context per **change**. What to build in this feature and what has been verified so far.

The agent reads both. The two separate layers keep the context window clean.

### 6.2 How gentle-ai runs ODD for you

gentle-ai runs ODD natively in every agent it configures, so you install and invoke nothing. The agent follows the same protocol on every request:

1. **Authorize.** Questions, reviews, and proposals stay read-only until you ask for a change.
2. **Explore.** The agent reads the relevant code and requirements first, in proportion to the request.
3. **Resolve uncertainty.** It asks one focused question only for a real product decision.
4. **Classify.** Small work is understood, contained, and can be resumed from the request plus `git diff`. Substantial work fails that test. File and test counts never decide it.
5. **Track.** Substantial work gets its feature document and Engram mirror before the first source write, and the agent tells you which document it created (section 6.3).
6. **Implement task by task.** Each task follows the test-first policy (section 9.1). A task is checked only after its outcome is observed, and it closes with a Conventional Commit on the feature branch.
7. **Close.** The agent reports the verified outcome, every failed or pending check, and the next step.

ODD adds no CLI, no state engine, and no mandatory planning phase. It is shared agent guidance. Your interface is natural language.

### 6.3 The feature document

For substantial, authorized work, the agent creates one feature document, `odd/tasks/<feature-name>.md`, after exploration and before the first source write. The file has a short header (objective, scope, applicable checks) and three sections, read in this order:

- **`## Specs`**: numbered `S#` requirements. They quote your exact strings, error messages, and examples verbatim, and they carry the acceptance criteria and checks.
- **`## Tasks`**: one line per task, with a stable ID (`T1`, `T2`), the linked specs, the route, and the commit that holds it.
- **`## Log`**: last. `L1` is your original request, verbatim. Corrections, evidence, and rationale are appended as the work goes on.

```markdown
# filter-by-status

Objective: filter the task list by status, with the filter kept in the URL.

## Specs
S1. The list accepts `status=open` or `status=done`. Any other value shows an error.
S2. Reloading the page keeps the active filter.

## Tasks
- [x] T1 (S1) inline, commit a1b2c3d
- [ ] T2 (S2) delegated, pending

## Log
L1. Original request, verbatim: "add a status filter to the task list..."
```

A requirement change rewrites only the affected spec and reopens only its task. Checkboxes record observed outcomes. They grant no approval and no review receipt.

The same content is mirrored to Engram under the project-scoped topic `odd/<feature-name>/tasks`, together with the file locator. When the agent resumes, it reads the Engram context, the feature-scoped search result, and the full observation, then the file itself, and reconciles them before it continues. Both writes are read back, because they are not atomic. If Engram is unavailable, the agent keeps local progress and reports the mirror as pending.

The feature document is plain markdown in git, so any IDE can read it, and Engram is shared across the IDEs on your machine. A new IDE does not inherit the previous conversation, so tell it which feature to continue, for example: `Continue odd/tasks/filter-by-status.md from T2.`

### 6.4 Work units, delivery and the 400-line budget

- **Work units.** Each task closes with at least one commit on the feature branch. When you are on the default branch, the agent creates the branch first. Commits use Conventional Commits, and tests and docs go in the same commit as the behavior they cover.
- **Budget.** About 400 authored changed lines (additions plus deletions) per slice is a planning heuristic, not a hard cap or an automatic stop. The agent keeps the smallest coherent behavior with its tests and docs. It does not remove blank lines or minify to fit the number, and it does not split artificially.
- **Delivery strategy.** The feature document records one strategy. `ask-on-risk` (the default) asks once which chain strategy to use when the forecast passes about 400 lines. `auto-chain` slices automatically once a chain strategy is chosen. `single-pr` and `exception-ok` keep one PR. Chained PRs follow the `chained-pr` skill, and the feature document records which commits each PR holds.
- **Delivery is yours.** Push, pull request creation, and merge are your decisions under ordinary repository policy.

### 6.5 Review and consent (RDD)

Receipt-Driven Development (RDD) is gentle-ai's independent review of a frozen change candidate. It is on by default. `gentle-ai review mode status` reads the switch without changing it, `gentle-ai review mode disable` turns it off, and `gentle-ai review mode enable` turns it back on. An explicit OFF choice stays off until you change it.

When RDD is on, each candidate is assessed for risk first:

- **Passive risk**: no reviewer and no prompt. The agent runs the structural checks and moves on.
- **Medium or high risk**: the agent asks for consent for that candidate. If you grant it, gentle-ai runs the review plan, with at most one bounded correction. If you decline, the change continues under ordinary repository policy. A decline applies to that candidate only. It does not turn RDD off.
- **Failed assessment**: the agent never assumes low risk.

Review results are informational. They never authorize a commit, a push, a PR, or a release. Turning RDD off is a user decision: the agent does not switch it off on its own.

### 6.6 Judgment Day: dual-judge review

gentle-ai includes the `judgment-day` skill, which runs a dual review: two judges review the same change in parallel, with no communication between them. Each reports issues such as bugs, vulnerabilities, contradictions with the feature's specs, and convention violations. The orchestrator then sorts the findings:

- **Confirmed** (both judges found it): fix it.
- **Suspect A or Suspect B** (only one judge found it): triage it.
- **Contradiction** (the judges disagree): you decide.

A fix agent applies the confirmed fixes, and both judges run again. Judges only detect: they never commit, push, or change code during review. Warnings that need an unlikely setup are reported as theoretical and do not block.

Invoke it manually with `/judgment-day` when you want a second opinion: before merging a risky PR, after a change to a shared contract, or when the agent implemented something without a spec. The order is implementation, then the Programmatic Checks in AGENTS.md, then Judgment Day if you invoke it, then your human review, then the commit. Human review still happens when Judgment Day passes.

---

## 7. Block 3 · MCPs, Testing Stack and Commands

### 7.1 Preconfigured MCPs

These already work without additional configuration:

- **Engram**: cross-session persistent memory. Connects automatically via MCP stdio.
- **Context7**: live framework documentation. The agent queries real React 19, Tailwind 4, etc. docs instead of using its training knowledge (which may be outdated).

### 7.3 Additional MCPs by stack

The wizard detects additional MCPs in Phase 4.6 by reading `package.json` and `.env.example`. Relevant MCPs are registered in the `## Project MCPs` section of the generated AGENTS.md — that section is the source of truth that `wf-onboard` reads to configure new machines.

**MCPs the wizard automatically detects by dependency**:

| Detected dependency | Suggested MCP | Required setup |
|---|---|---|
| `@playwright/test` | Playwright MCP | `npx playwright install --with-deps chromium` |
| `@supabase/supabase-js` | Supabase MCP | API key in `.env.local` |
| `pg`, `postgres`, `@neondatabase` | Postgres MCP | Connection string in `.env.local` |
| `stripe` | Stripe MCP | Test API key in `.env.local` |
| `@octokit/rest`, `@octokit/core` | GitHub MCP | `gh auth login` |

**Engram and Context7** don't appear in this table because they are already active via gentle-ai on all machines — they don't require per-project configuration.

**Format of the `## Project MCPs` section** in AGENTS.md (generated by the wizard):

```markdown
## Project MCPs

| MCP | Purpose | Required setup |
|---|---|---|
| Engram | Cross-session persistent memory | Automatic via gentle-ai |
| Context7 | Live framework docs | Automatic via gentle-ai |
| Playwright | Browser control for E2E | `npx playwright install --with-deps chromium` |
| GitHub | PRs, issues, code review | `gh auth login` |
```

This section is read by `/wf-onboard` to guide each new developer through the exact steps for their machine.

### 7.4 Testing stack — automatic configuration

The wizard's goal is that the agent runs tests as part of every change, without the user having to remember commands. For that, the wizard configures the complete stack.

**When it is configured**: in Phase 0c (feature selection) and Phase 4.6 (testing stack), when the user confirms they want testing. It can also be configured later with `/wf-settings`.

**What the wizard installs and configures** (with user confirmation for each layer):

```
What testing layers do you want to configure in this project?

1. Unit tests (Vitest + Testing Library)
   → The agent writes unit tests for hooks, utilities, and pure logic.
   → Command: npm run test

2. Integration tests (Vitest + Testing Library with component render)
   → The agent verifies components integrate correctly.
   → Same runner as unit, files separated by convention.

3. E2E tests (Playwright)
   → The agent verifies complete flows in the browser.
   → Activates the Playwright MCP so the agent can launch and observe the browser.
   → Command: npx playwright test

Which layers should I activate? [1 / 2 / 3 / 1,2 / 1,2,3 / none for now]
```

After the selection, the wizard:

1. Installs dependencies (`npm install --save-dev vitest @testing-library/react @playwright/test`, according to selection).
2. Generates config files (`vitest.config.ts`, `playwright.config.ts`).
3. Adds scripts to `package.json` (`test`, `test:ui`, `test:e2e`, `test:coverage`) — Phase 8, step 8.1e, from `test-scripts.tmpl.md` / `e2e-scripts.tmpl.md`.
4. Injects the extra fragments into the generated configs (Phase 6b, step B8a, promoted in Phase 8): `coverage-thresholds.tmpl.md` into `vitest.config.ts` when `state.testing.coverage_threshold` is a number, and `visual-snapshots.tmpl.md` into `playwright.config.ts` when `state.testing.visual_regression` is true.
5. Updates `AGENTS.md` "Testing" section with the real commands.
6. If the user activated Playwright: configures the Playwright MCP in the agent's folder (Phase 8, step 8.1e, from `playwright-mcp.settings.tmpl.md`).
7. Everything with human review gate before writing any files.

This makes the Programmatic Checks in AGENTS.md go from `lint + build` to `lint + build + test` (or `lint + build + test + e2e` depending on layers). The agent runs them before it declares a change done.

**Test-first** (section 9.1): when testing is configured, the agent writes the relevant test before it implements each change, watches it fail, and then implements until it passes. It picks the layer from the coverage matrix in AGENTS.md (unit for pure logic, integration for components, e2e for complete user flows). There is no proposal menu to answer.

E2E naming conventions: one file per user flow named by the flow, not by the component (`persistence.spec.ts`, `task-creation.spec.ts`). The convention lives in the `AGENTS.md` "Testing Approach" section (written in Phase 4.6).

When the Decision Ladder is enabled, the order is: 🪜 WF-LADDER rungs, your confirmation, then test-first implementation.

### 7.5 Project-specific commands

Commands the wizard generates in Phases 6a/6b and writes in Phase 8. They are project-specific markdown files — live in the repo, not globally. They are used as slash commands in the IDE (correct format per IDE).

**`/wf-ladder`**: forces explicit wf-ladder with visible `🪜` output per rung (only if the Decision Ladder is enabled).
**`/wf-onboard`** — stub that points to `wf-onboard.md` for new developer onboarding.
**`/wf-settings`**: toggle optional modules: testing, testing extras, Decision Ladder, CI/CD, release strategy, and active IDEs/CLIs.
**`/wf-worktree`** — git worktree management with automatic port assignment.

**Global vs project-specific commands**: `wf-init`, `wf-refresh`, and `wf-cleanup` are installed globally with `install.sh`. `wf-onboard`, `wf-settings`, and `wf-worktree` are generated per project in Phases 6a/6b. `wf-ladder` is project-specific too, conditional on the Decision Ladder. `/wf-cicd` was archived; CI/CD and release-strategy re-configuration happen through `/wf-settings` (options 6–13), whose single source is the `cicd` protocol.

**Skills 1:1** — every command in this section is also packaged as a SKILL.md, so it can be invoked as a slash command AND by natural language. Project commands are emitted by Builder B4 in the IDE's native skill path (`.claude/skills/`, `.cursor/skills/`, `.kiro/skills/`, `.codex/skills/`, `.gemini/skills/`, `.windsurf/skills/`, `.devin/skills/`) plus the universal `.agents/skills/<cmd>/SKILL.md` and the flat `.agents/protocols/<cmd>.md`. Global commands get the same 1:1 from `install.sh` (each detected IDE's skill path + `~/.agents/skills/`).

**Correct paths and formats per IDE** (verified against official documentation):

| IDE | Directory | Format |
|---|---|---|
| Claude Code | `.claude/commands/` | Plain markdown, no frontmatter |
| Cursor | `.cursor/commands/` | Plain markdown, no frontmatter |
| Windsurf/Devin | `.windsurf/workflows/` | Frontmatter with `description:` required |
| Kiro | `.kiro/steering/` | Frontmatter with `inclusion: manual` |
| OpenCode | `.opencode/commands/` | Plain markdown, no frontmatter |
| Copilot | `.github/prompts/` | Suffix `.prompt.md` + `agent: 'agent'` |

**Important**: `.cursor/rules/` and `.windsurf/rules/` are for context rules (always-on) — a different concept from slash commands. In Kiro, `inclusion: manual` turns a file into a slash command; `inclusion: always` makes it always-on (already covered by satellites).

The wizard detects active IDEs: on new projects it uses the Phase 5 list; on upgrades it reads existing satellites in the repo.

### 7.6 How to test that wf-ladder works

Three concrete tests. The ladder shows its rungs in the output and stops for your confirmation before any code is written.

**Test 1, reuse at rung 2:**

```
I need to show the number of completed tasks in the app header.
```

Expected: `🪜 WF-LADDER` stops at rung 2 because `useTasks` already exposes `tasks.filter(t => t.completed).length`. Success signal: the change reuses that expression from `useTasks`, with no new hooks or state.

**Test 2, reach rung 7:**

```
I need to validate that a task title doesn't have special characters like <, >, &.
```

Expected: rungs 1 to 6 do not apply, and the ladder stops at rung 7 with a minimum validation function. If it proposes installing a validation library, it did not apply rung 5 correctly.

**Test 3, a substantial feature:**

```
Add a priority system to tasks (high, medium, low) with visual badge and ability to sort by priority.
```

Success signals:

- The ladder runs first, and its rungs do not end at reuse, because the change touches several coordinated files.
- Because the change is substantial, the agent creates a feature document in `odd/tasks/` with its specs and tasks, and mirrors it to Engram.
- Each task follows the test-first policy, and the agent observes its checks before it starts the next task.

### 7.7 `/wf-onboard` — new developer cloning the repo

`wf-onboard.md` is the onboarding wizard for developers who clone a repo that already has the workflow configured. It does not modify the repo — only configures the local environment.

**Wizard phases**:

- **Phase 0**: reads the repo's AGENTS.md, especially the `## Project MCPs` section — source of truth for which MCPs each developer needs to configure.
- **Phase 1**: verifies and installs gentle-ai if missing. Detects which agents the team uses (by reading the repo's satellites) and compares them with the agents configured on the developer's machine. Configures missing ones.
- **Phase 2**: verifies Engram, the persistent memory that mirrors each feature document. The feature documents in `odd/tasks/` are the shared record in the repo.
- **Phase 3**: verifies and guides configuration of each project MCP. Automatic ones (Engram, Context7): no action. Playwright: verifies browsers. GitHub: `gh auth login` if missing. API key MCPs (Supabase, Stripe, Postgres): guides creation of local `.env.local`.
- **Phase 4**: final verification with status summary and project commands.
- **Phase 5**: suggests adding a mention to `/wf-onboard` in the README if it doesn't exist.

**How to use**: generated as a project-specific slash command in Phases 6a/6b of `/wf-init`. Invoked with `/wf-onboard` from the cloned repo root.

**The project README should include**: "If you are new to this repo, run `/wf-onboard` to configure your local environment."

---

## 8. Block 4 · Orchestration and worktrees

### 8.1 What gentle-ai automates vs. what the wizard provides

| Capability | Does gentle-ai provide it? | Detail |
|---|---|---|
| Delegation to sub-agents | Yes, native | Via Agent tool in Claude Code, native system in OpenCode, inline (without spawning a separate process) in others |
| Rules for when to delegate | Yes, native | "Delegation Stop Rules" — see 8.2 |
| Model routing per sub-agent | Depends on the agent | Configured in gentle-ai (`Configure Models` in the TUI, section 4.10). The wizard does not change models |
| Worktrees | No | gentle-ai does not create, list, or clean worktrees. It only has a reactive rule: if it detects a worktree/git accident, it requires a fresh audit before continuing |

### 8.2 Sub-agents and delegation (native to gentle-ai)

When the orchestrator agent (the one in your main session) delegates work to a sub-agent (for example, an exploration sub-agent that reads code before a change is planned), that sub-agent is not a dumb script. It is a full agent with its own session, its own tools, and its own context.

**How this runs depending on which agent you use**:

| Agent | How it delegates |
|---|---|---|
| Claude Code | Via the Agent tool (Task tool) — the orchestrator launches focused sub-agents and injects already resolved project rules |
| OpenCode | Native sub-agent system: each sub-agent is a dedicated agent with its own model, tools and permissions defined in `opencode.json` |
| Cursor | Native sub-agents |
| Kiro | Native sub-agents with orchestration via steering |
| Windsurf Cascade | No sub-agents (solo-agent, per gentle-ai's own installed content), so work runs inline |
| Devin (fork of Windsurf) | gentle-ai has no dedicated adapter for Devin, so it inherits Windsurf's "no sub-agents" content by accident. In practice Devin does support real subagent delegation (`run_subagent()`-style tool) — check your actual session toolset rather than trusting the inherited label |
| Codex | Native sub-agents in `~/.codex/agents/` |
| Copilot | Runs inline in a single session, without spawning separate processes |
| Gemini CLI | Runs inline in a single session, without spawning separate processes |
| Antigravity CLI | Runs inline in a single session |

You don't need to configure any of this — the `gentle-ai install` wizard sets it up when you choose your preset. What IS worth understanding are the rules that tell the orchestrator *when* to delegate instead of doing everything in the same session.

**Delegation Stop Rules** (rules gentle-ai applies automatically):

| Rule | Triggers when | Expected behavior |
|---|---|---|---|
| 4-file rule | Reading 4+ files to understand a flow | Delegate exploration or run a dedicated exploration phase |
| Multi-file write rule | Touching 2+ non-trivial files | Use a single writer, or require fresh review before marking done |
| PR rule | Before commit, push, or PR after code changes | Run a fresh review, unless the diff is trivial text/docs |
| Incident rule | After a wrong cwd, a worktree/git accident, merge recovery, confusing test command, or environment patch | Run a fresh audit before continuing |
| Long session rule | After ~20 tool calls, 5 exploratory reads, or 2 non-mechanical edits with increasing complexity | Pause and delegate, replan, or justify why not |
| Fresh review rule | Adversarial review of diffs, conflicts, PR readiness, or incidents | Use fresh context when the agent platform supports it |

**For you as a developer, this means**: if you see your agent suddenly "opens" a sub-task instead of continuing everything in the same conversation, this is working — it's not a bug or a weird model decision. It's the mechanism that prevents a long session from accumulating complexity without control.

### 8.3 Model choice

gentle-ai can assign models to agents and sub-agents (section 4.10 shows where). This workflow does not set models per phase, because ODD has no phases. Use one model per session, and switch it in your IDE or CLI when a session needs a different one.

> **Note for Improving**: the organization-approved models are Claude Sonnet and Claude Haiku. Opus, Fable, and Mythos are not approved for use in this stack. Use Haiku for read-only exploration and Sonnet for everything else. If a project needs more capacity, request an exception from Global IT Services; do not change the model on your own.

> **Codex CLI**: treats skills as passive reference context, so it can skip the Decision Ladder gate even after reading it. Workaround: add the protocol instructions at the end of the prompt (`--prompt "..."` or paste in UI) instead of relying on it reading from `AGENTS.md` or `.agents/`. The wizard documents this but doesn't automate it because the limitation is on the client side, not the config.

### 8.4 Worktrees — `/wf-worktree` (built in this block)

gentle-ai does not manage worktrees. The only thing it does is the "Incident rule" from 8.2: if it detects something went wrong with a worktree, it requires an audit before continuing — but it doesn't create, list, or clean worktrees for you. That's why the worktree wizard exists: `/wf-worktree` is a project-specific slash command generated in Phases 6a/6b.

#### 8.4.1 What it solves

A worktree is an isolated git folder that shares the same repository (same `.git`, different working folder). It allows having multiple agents working in parallel without stepping on each other — each in its own folder and its own branch, without needing to clone the repo multiple times.

`/wf-worktree` automates three operations and adds two capabilities that the manual pattern doesn't solve alone: **automatic free port assignment** (so worktree dev servers don't conflict) and **natural language invocation**, in addition to the explicit command.

#### 8.4.2 Reference manual pattern

To make clear what the command hides, here's how it would be done manually:

```bash
# Create a new worktree for a feature, in a sibling folder to the repo
git worktree add ../myrepo-feature-x -b feature/x

# Work there as if it were a separate clone
cd ../myrepo-feature-x
# open the AI IDE/CLI there — AGENTS.md is already in the repo, looks the same

# When done:
cd ../myrepo
git worktree remove ../myrepo-feature-x
git branch -d feature/x   # if already merged
```

The developer decides everything manually: branch name, folder convention, and — the most error-prone point — which port to use if each worktree starts its own dev server. Without coordination, two worktrees trying `npm run dev` on port 3000 will conflict.

#### 8.4.3 `/wf-worktree new` — create one or more worktrees

**Explicit invocation**:
```
/wf-worktree new feature-x
/wf-worktree new 3 tasks: feature-x, fix-y, feature-z
```

**Natural language invocation** (mapping lives inside `wf-worktree.md`, not in AGENTS.md — see 8.4.7):
```
"launch a worktree for feature x"
"I need 3 worktrees to work on feature-x, fix-y and feature-z in parallel"
```

**What it does, step by step**:

1. Detects the current repo name and the parent folder where to create sibling worktrees.
2. For each requested task, generates a branch name following project convention (`feature/`, `fix/`, etc. — reads `AGENTS.md` if it documents a convention, otherwise asks once and reuses for the rest).
3. Runs `git worktree add ../<repo>-<task> -b <branch>` for each one.
4. **Automatic port detection and assignment**: reads `package.json`, `vite.config.*`, or the project's dev script to identify the default port (e.g., 3000, 5173). For each new worktree, checks which ports are free on the machine (`lsof -i :<port>` or equivalent) and assigns a different one per worktree, exporting it as an environment variable (`PORT=3001`, `PORT=3002`, etc.) in a `.env.local.worktree` file inside each worktree — never modifies the original repo's `.env.local`.
5. If the project has heavy `node_modules`, asks whether you prefer a shared symlink (`ln -s ../myrepo/node_modules`) or independent installation per worktree — each option has its tradeoff (symlink is faster but can break if dependencies diverge between branches; independent installation is slower but safer).
6. Shows a summary:

```
Worktrees created:
  ../myrepo-feature-x   (branch: feature/x, port: 3001)
  ../myrepo-fix-y       (branch: fix/y,     port: 3002)
  ../myrepo-feature-z   (branch: feature/z, port: 3003)

To work on each one, open your AI IDE/CLI in that folder —
AGENTS.md is already available there because it's the same repo.
```

**Never does `git push`** — same as the rest of the wizards in this workflow.

#### 8.4.4 `/wf-worktree list` — see what's active

**Invocation**: `/wf-worktree list` or "list worktrees" / "what worktrees do I have open".

```bash
git worktree list --porcelain
```

Shows each worktree with its branch, last commit, and — if the wizard created it — the assigned port (reading each one's `.env.local.worktree`):

```
Active worktrees:
  myrepo (main)                   main            a1b2c3d
  myrepo-feature-x                feature/x       f4e5d6c   port 3001
  myrepo-fix-y                    fix/y           9c8b7a6   port 3002
```

Useful especially if you have multiple agents working in parallel and want a quick view of what's open without remembering it.

#### 8.4.5 `/wf-worktree clean` — safe cleanup

**Invocation**: `/wf-worktree clean` or "clean old worktrees".

1. List active worktrees (same as 8.4.4).
2. For each one, verify if its branch has already been merged to the main branch:
```bash
git branch --merged main | grep <branch-del-worktree>
```
3. If merged, proposes it for cleanup. If not, leaves it out of the proposal without asking (avoids accidentally deleting work in progress).
4. Shows the proposal and waits for explicit confirmation — **never deletes automatically**:

```
Worktree candidates for cleanup (branch already merged to main):
  myrepo-feature-x   (feature/x, merged 2 days ago)

Do you confirm the cleanup? [yes / no / review one by one]
```

5. Only with confirmation, execute:
```bash
git worktree remove ../myrepo-feature-x
git branch -d feature/x
```

#### 8.4.6 `/wf-worktree parallel` — end-to-end, with review gate

**Invocation**: describe several changes and ask for them to end up merged,
for example "I need 2 changes in different worktrees and at the end merge
into this branch: 1- remove underline from delete button 2- remove trash icon".

This mode goes beyond creating empty worktrees: it creates each worktree
(reusing full 8.4.3, including the mandatory `node_modules` check),
**implements** the corresponding change in each one,
**commits** with individual confirmation per worktree, returns to the main
checkout, and **merges** each branch to the target — with a mandatory
consolidated review gate just before touching that branch, shown
independently of the individual commit confirmations.

```
Ready to merge to "main":
   1. feature-remove-underline   — removed underline from delete button
   2. feature-remove-icon        — removed trash icon from delete button

Do you confirm merging both branches to "main"? [yes / no / review diffs first]
```

If a real merge conflict appears, the agent shows it as-is —
never silently picks a side — and waits for the developer's indication on
how to resolve it, offering to propose an integration of both changes if
explicitly asked.

When all merges are done, it suggests (without forcing) running `clean` on the
recently used worktrees, since their branches have been merged:

```
Merge complete. "main" now includes both changes.
Should I run cleanup now (/wf-worktree clean) or would you prefer to leave them for now?
```

> **Origin of this mode**: in the maintainer's first real test, a
> capable agent (Claude Code) already correctly extrapolated most of
> this complete orchestration from a prompt like the invocation example
> above, without it being explicitly written in
> `wf-worktree.md` — including showing diffs and asking for confirmation before
> merging. This mode formalizes that behavior in writing so it doesn't
> depend on the agent inferring it correctly each time, particularly the
> merge review gate, which is too important to leave to
> case-by-case inference.

#### 8.4.7 Natural language recognition — where it lives

The mapping of natural language phrases to the four operations (`new`, `list`, `clean`, `parallel`) lives **inside `wf-worktree.md`**, as internal instructions of the file itself — it is not added to `AGENTS.md`. This maintains the convention already established with `wf-ladder`: those commands also live as standalone files briefly referenced from `AGENTS.md`, not duplicated there. Putting the full mapping in `AGENTS.md` inflates its target size (150-200 lines, see Appendix D) unnecessarily — `AGENTS.md` is a lightweight index, not the source of truth for every feature.

The command stub in `AGENTS.md` (or in the IDE's commands directory) simply indicates: "if the user asks for something equivalent to create/list/clean/merge worktrees in parallel in natural language, follow the instructions in `wf-worktree.md`". The file itself contains the example phrases and decision logic.

#### 8.4.8 Installation as command (same pattern as Block 3)

Same as `wf-ladder` and `wf-onboard`, `/wf-worktree` is generated in Phases 6a/6b of `wf-init` (or added via `/wf-refresh` if the project is already initialized) for each active IDE, with the same path table and formats from section 7.5:

| IDE | Path | Format |
|---|---|---|
| Claude Code | `.claude/commands/wf-worktree.md` | Plain markdown, no frontmatter |
| Cursor | `.cursor/commands/wf-worktree.md` | Plain markdown, no frontmatter |
| Windsurf | `.windsurf/workflows/wf-worktree.md` | Frontmatter with `description:` required |
| Kiro | `.kiro/steering/wf-worktree.md` | Frontmatter with `inclusion: manual` |
| OpenCode | `.opencode/commands/wf-worktree.md` | Plain markdown, no frontmatter |
| Copilot | `.github/prompts/wf-worktree.prompt.md` | Suffix `.prompt.md` + frontmatter `agent: 'agent'` |

It is a **project-specific** command (like `wf-ladder`), not global — depends on the repo you're in, although its internal logic is generic.

The complete `wf-worktree.md` file is already built as a standalone file (same format as `wf-onboard.md`): three operations (`new`, `list`, `clean`), free port detection per worktree, internal natural language mapping, and inviolable rules to never push or delete without explicit confirmation. It is included in the `EXPECTED_COMMANDS` and in the per-IDE command generation — a project running `/wf-init` from scratch receives it right away, and one already initialized receives it via `/wf-refresh` (builder-driven refresh, check for missing commands).

---

## 9. Block 5 · Testing: test-first and Playwright

### 9.1 Test-first by default

The agent writes the test first whenever a relevant runnable test exists. The policy has four parts:

1. **Observe RED.** Write a test for the requested behavior, and watch it fail for the expected reason before you implement.
2. **Implement to GREEN.** Write the least code that makes the test pass.
3. **Refactor** while the tests stay green.
4. **Explain the exceptions.** When no meaningful runnable test exists (passive documentation, no runner yet), the agent says so and runs the applicable functional checks instead. It never invents a runner or RED evidence.

The coverage matrix in AGENTS.md maps each change type to the layers that apply:

| Change type | Unit | Integration | E2E |
|---|---|---|---|
| Logic in a hook or `lib/` | Yes | No | No |
| Component with its own state | Yes | Optional | No |
| Multi-component flow | No | Yes | No |
| Complete user feature | No | Yes | Yes |
| Bug fix with possible regression | Based on origin | No | No |
| Pure UI or styles | No | No | No |

The matrix is a guideline. If logic could break silently and the table does not cover it, add tests anyway.

You choose testing in Phase 0c. Phase 4.6 then asks which layers to set up (unit, integration, E2E), installs them, and registers the Playwright MCP when E2E is chosen. Test-first is not a mode you select: it applies whenever the project has a runnable test for the change.

### 9.2 Playwright dual loop: when to explore before versioning

The pattern consists of two different loops for the same tool:

- **Loop 1 — exploration (Playwright MCP, no new files)**: the agent controls a real browser interactively — navigates, clicks, captures screenshots — to visually confirm that a flow behaves as expected, before committing to write a spec.
- **Loop 2 — versioning (`@playwright/test`, real spec in `e2e/`)**: once confirmed, the agent writes the spec that gets committed and runs in any future pipeline, without needing the interactive browser.

**It is not a mandatory step in all cases** — forcing visual exploration before every spec, even in trivial and well-known flows, would be unnecessary ceremony, contrary to gentle-ai's own principle of "small request, no ceremony". The agent evaluates:

- **Explore first if**: the flow has multiple visual states, transitions or animations; it's the first time that interaction is tested; or the user explicitly asks for it.
- **Go direct to spec if**: it's a simple known CRUD (create → appears in list, edit → updates) without complex visual states, or a similar template spec already exists.

This criterion lives in the Testing Approach section of `AGENTS.md` (the "Playwright dual loop" subsection). Whenever E2E specs were generated, the agent also shows the headed command for the exact spec before it declares the task done, so you can watch it run in the browser:

```bash
npm run test:e2e -- --headed --workers=1 --project=chromium e2e/<exact-name>.spec.ts
```

### 9.3 `data-testid` convention, mandatory when E2E is present

When the project activates the E2E layer in Phase 4.6, `/wf-init` adds to the Testing Approach section of `AGENTS.md` the requirement that every interactive element (buttons, inputs, links) receives its own `data-testid` **at component creation time**, not later when a test needs it. Format: `data-testid="<context>-<element>"` in kebab-case. The practical reason: without this, E2E specs depend on visible text or Tailwind classes, both fragile against copy or style changes that have nothing to do with the behavior the test is trying to verify.

### 9.4 Optional extras: coverage targets, visual regression, Page Object Model

All three are asked in Phase 4.6, after the layers, and **none activate without the user explicitly requesting it**. Each has a real cost that isn't justified in every project:

| Extra | What it does | Real cost | When it's worth it |
|---|---|---|---|---|
| Coverage targets | Minimum coverage threshold; fails `npm run test -- --coverage` if not met | Nearly zero — one config line in `vitest.config.ts` | Almost always — cheap and provides an objective quality signal |
| Visual regression (snapshots) | Compares screenshots against a saved reference | Real and ongoing — each run is slower, and references need manual re-generation when design intentionally changes | Projects with stable UI where an accidental visual change would be costly |
| Page Object Model | Organizes Playwright selectors into reusable classes. Activating it stages a minimal `e2e/pages/HomePage.ts` scaffold plus an AGENTS.md convention line; real page objects emerge as features add specs | None at runtime, but it's an abstraction layer | Projects with multiple E2E specs; for 2-3 flows it's over-engineering, same logic the workflow's Decision Ladder already applies |

Integration with CI/CD (so the coverage threshold also blocks the pipeline, not just the local run) is pending until Block 6 exists — today the gate can only apply locally.

### 9.5 Strategy for legacy projects without tests

Unchanged from the original criteria: no mass retrofitting of tests onto legacy code without coverage. Testing entry is organic — new feature comes with its new tests, bug fix comes with a regression test that first reproduces the bug and then confirms the fix, and the suite grows with the team's real work instead of a dedicated "let's cover all the legacy this sprint" effort.

### 9.6 `/wf-settings`: toggle optional modules after installation

Once `/wf-init` has run, several decisions the developer made (testing, testing extras, Decision Ladder, CI/CD, release strategy, active IDEs/CLIs) are fixed in the project, but they are not immutable, and it shouldn't require editing files by hand or re-running full `wf-init` to change them. `/wf-settings` (new standalone file, same format as `wf-onboard.md` and `wf-worktree.md`) closes that gap.

**The modules it manages** (options 1–15 in `/wf-settings`):

| Module | What it toggles | Risk when changing |
|---|---|---|
| Decision Ladder (1) | `wf-ladder` enabled or not | Real: it's an anti-over-engineering safeguard, removing it requires additional explicit confirmation |
| Testing infrastructure (2) | Enable or disable the testing layers (unit, integration, E2E) | Medium: adds or removes the test runner setup |
| Testing extras (3–5) | Coverage targets / Visual regression / Page Object Model, each independent | Low: only config, although deactivating visual regression or POM doesn't automatically rewrite existing specs |
| CI (6) | Enable or disable the CI quality guard | Real: adds/removes `.github/workflows/quality-guard.yml` and related files |
| AI Reviewer (7) | GGA / Copilot / Claude Code / Gemini / None | Medium: rewrites the AI review workflow |
| AI Review Suggestions (8) | Enable or disable auto-improve / inline suggestions | Low: config change only |
| Dedicated Security Review (9) | Claude / Gemini / OFF | Low: config change only |
| E2E in CI (10) | Include E2E tests in the quality guard | Low–Medium: may slow CI; no effect on local tests |
| release-please standalone (11) | Publish releases automatically from conventional commits | Medium: `release-please-config.json` now uses `release-type` resolved from `state.discovery.stack` (`node` for Node projects, `simple` default; resolved via `discovery.stack.primary`, falling back to `discovery.stack_key` when absent, e.g. legacy states migrated by R2) |
| CD (12) | Automatic deploy to VPS | Real: writes `deploy.yml` and requires server secrets |
| Release strategy (13) | Tag-based (`v*`) or push-to-main deploy trigger | Medium: changes how CD fires |
| IDEs/CLIs (14) | Add/remove an active IDE: generates (satellite + commands + skills) or deletes everything related, downloading templates from the wizard's raw source | Real: creates or removes project files; requires explicit confirmation |
| Branch PR override (15) | Project-local override for the branch-pr skill | Low: switches the override on or off |

**Note**: Option numbering in `/wf-settings` runs from 1 to 15. Option 1 maps to `wf-ladder`, option 2 to the testing infrastructure, and option 14 manages IDEs and CLIs.

**Interaction pattern**: the command always shows the real state first (reading `.wizard-state.json` and `AGENTS.md` directly, never assuming what the developer remembers choosing), lets you choose one or several changes, applies and confirms each individually, and asks "anything else?" before closing with a consolidated commit, without `git push`, like the rest of this workflow.

**Why it's project-specific and not global**: just like `/wf-worktree`, its behavior depends entirely on the real state of the active repo (which backend, which extras are on) — it doesn't make sense as a global command installed once for all projects.

The `/wf-init` and `/wf-refresh` slash commands already include `wf-settings` in their `EXPECTED_COMMANDS`, so it is auto-generated in new projects and offered to add in existing projects that don't have it.

---

## 10. Block 6 · CI/CD pipeline + GGA

Block 6 automates the "quality gatekeeper" of your repo: every time you make a commit or
open a Pull Request, automatic reviews (AI + linter + tests + security) run that
catch problems BEFORE they reach `main`. It's like having a senior reviewing every line,
without depending on a human being available.

**Why it has real value**:
- A single dev cannot self-review with objectivity. The pipeline can.
- In a team, it prevents "it works on my machine": what doesn't respect the standard, CI stops.
- It turns your `AGENTS.md` into **enforced** rules, not just documented ones.

The block consists of two independent features: **CI** (continuous integration: quality,
review, security, conventional commits) and **CD** (continuous delivery: automatic deploy).
They can be activated separately via `/wf-settings`.

### CI (Continuous Integration)

| Piece | What it does | Concrete value |
|---|---|---|
| **Quality Guard** | GitHub Action: lint + types + tests + build + e2e on every PR and push | Nothing broken gets merged; green is the requirement |
| **AI Review on PR** | An AI reads the PR diff and comments on issues | 24/7 quality review without waiting for a human |
| **Security Review** | SAST scan by AI (pr-agent or Claude) | Catches leaked secrets, injections, etc. |
| **Conventional Commits** | Husky + commitlint enforce `feat:`, `fix:` format... | Readable history + enables automatic changelog |
| **release-please** | Generates release PR + changelog based on commits | Traceable releases without writing changelog manually |

The **AI Review** has four possible providers (plus `None`):
- **GGA (Gentleman Guardian Angel) — recommended.** Provider-agnostic (Claude, Gemini,
  Codex, OpenCode, Ollama, LM Studio, GitHub Models). Uses your `AGENTS.md` as review
  rules. Two modes: local pre-commit hook (`gga init && gga install`) and PR review via CI
  (`gga run --pr-mode`). Binary via `gentle-ai install --component gga` or
  `brew install gentleman-programming/tap/gga`.
- **Claude Code Action** (if you have an Anthropic API key).
- **Copilot review** (no API key, integrated in GitHub).
- **Gemini via pr-agent** (free alternative, requires Google API key).

### CD (Continuous Delivery)

CD automatically deploys your app to a VPS when a release PR is merged. Supports:
- **PM2 + Nginx** for Node.js apps.
- **Nginx + PHP-FPM** for PHP apps.
- **Docker** for containerized apps.

The release strategy is independently configurable: tag-based (tag v* → deploy) or
push to main. CD can be activated even without CI — each feature is independent.

### Hook coexistence

GGA = pre-commit · drift detector = post-commit · commitlint = commit-msg. No conflict.
Workflow/config templates are a single source of truth in `templates/protocols/cicd/`.

### How to configure

`/wf-init` asks you about CI and CD in its configuration flow (Phase 4.7) and generates
the artifacts in Phases 6a/6b (the Builder, to staging). If you already initialized the project and want to change something,
use `/wf-settings` (CI options, AI Reviewer, Security Review, CD, etc.) for complete
CI/CD block re-configuration (single source: `templates/protocols/cicd/_base.md`).

---

## 11. Block 7 · Bootstrap automation (slash commands)

> The workflow is distributed as a product via `install.sh` — one line to install global slash commands on all detected IDEs.

### install.sh

```bash
curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/install.sh | bash
```

- Detects IDEs by directories in `~/` (Claude, Cursor, Windsurf, Kiro, Codex, Copilot, Antigravity, OpenCode, Devin)
- Installs `/wf-init`, `/wf-refresh`, and `/wf-cleanup` as self-contained slash commands
- Applies correct format per IDE (plain `.md` for Claude/Cursor/Codex/OpenCode, frontmatter `description:` for Windsurf workflows, SKILL.md with `name:`/`description:` for Windsurf/Devin/Copilot/Antigravity, `inclusion: manual` for Kiro)
- Installs the matching SKILL.md (1:1) in each detected IDE's global skills path (`~/.claude/skills/`, `~/.cursor/skills/`, `~/.codex/skills/`, `~/.config/opencode/skills/`, Windsurf/Devin/Copilot/Antigravity) plus `~/.agents/skills/` (read by Codex, OpenCode, Gemini/AGY app, and Devin; AGY CLI does NOT read it — Antigravity coverage comes from the `~/.gemini/antigravity-cli/builtin` + `~/.gemini/config/skills` installs)
- Supports `--uninstall` to remove only the installed commands

### Global vs project-specific commands

| Type | Commands | Installation |
|---|---|---|
| **Global** | `/wf-init`, `/wf-refresh` | `install.sh` → per-IDE global paths |
| **Project-specific** | `/wf-onboard`, `/wf-settings`, `/wf-worktree` | `/wf-init` Phases 6a/6b → repo |
| **Global** | `/wf-cleanup` | `install.sh` → per-IDE global paths |
| **Project-specific** | `/wf-ladder` (optional, Decision Ladder) | `/wf-init` Phases 6a/6b → repo |

Global paths written by `install.sh` per command:

| IDE | Paths |
|---|---|
| Claude / Cursor / Codex / OpenCode | `~/.<ide>/commands/<cmd>.md` (plain markdown) + `~/.<ide>/skills/<cmd>/SKILL.md` (1:1 skill) |
| Windsurf (legacy) | `~/.codeium/windsurf/global_workflows/<cmd>.md` (frontmatter `description:`) + `~/.codeium/windsurf/skills/<cmd>/SKILL.md` |
| Devin (Windsurf rebrand) | `~/.config/devin/skills/<cmd>/SKILL.md` — detected via `~/.config/devin/`; written by the Windsurf block too when Devin is not detected separately |
| Kiro | `~/.kiro/steering/<cmd>.md` (frontmatter `inclusion: manual`) |
| Copilot | `~/.copilot/skills/<cmd>/SKILL.md` |
| Antigravity | `~/.gemini/antigravity-cli/builtin/skills/<cmd>/SKILL.md` (CLI) + `~/.gemini/config/skills/<cmd>/SKILL.md` (canonical global path read by AGY, AGY CLI, AGY IDE) — installed only when `~/.gemini/` is detected |
| All IDEs | `~/.agents/skills/<cmd>/SKILL.md` — unconditional (not read by AGY CLI) |

### What the block includes

- Self-contained commands: all `_base.md` files have inline content.
- `wf-init/_base.md` (C2): template that fetches phase files from GitHub via curl.
- Builder B7: generates for all IDEs including `.codex/commands/`.
- Unified naming: "AI Workflow Wizard" in all active files.
- Command `/wf-cleanup` to uninstall the wizard from a project without touching gentle-ai.
  Detection is manifest-driven: `build_plan.managed_paths` from `.wizard-state.json` is the
  authority (with special-handled exclusions: `AGENTS.md` → Phase 2 cleans its content,
  `.gitignore` → revert wizard lines only, MCP settings → remove the wizard entry only),
  and the heuristic
  patterns stay as a safety net for orphaned artifacts from installs older than the
  manifest. Heuristics cover satellites (including `.cursor/rules/`, `.windsurf/rules/`,
  `.devin/rules/project.md`, `.kiro/steering/`, `.opencode/AGENTS.md`,
  `.codex/AGENTS.md`), flat protocols (`.agents/protocols/`),
  commands, CI/CD workflows (`security-review*.yml`, including `deploy.yml`), MCP settings
  (Playwright MCP entries), test configs, the `post-commit` hook (`.git/hooks/`), `.husky/`,
  `.gga`, `.pr_agent.toml`, release-please configs, `.wizard-staging/`,
  `.wizard-managed-files.json`, and `.gitignore` entries. In Node projects with `.husky/`
  deleted, it offers package.json reconciliation (remove `"prepare": "husky"`,
  husky/commitlint devDependencies, and a stale `core.hooksPath`) so a later
  `npm install` cannot resurrect the wizard, and reports npm scripts left referencing
  deleted test configs.
  Confirmation is free-form: after the inventory, the user writes in their own words what to
  keep, and everything wizard-owned not mentioned is deleted after a per-group confirmation.

---

## Appendices

### A · Useful gentle-ai commands

| Command | Purpose |
|---|---|
| `gentle-ai install` | Initial configuration of detected agents |
| `gentle-ai install --agent <name> --preset full-gentleman` | Add a specific agent |
| `gentle-ai install --scope=workspace` | Install per-project instead of global |
| `gentle-ai status` | View configured agents and their status |
| `gentle-ai doctor` | Complete ecosystem health check |
| `gentle-ai upgrade` | Update internal components (post brew upgrade) |
| `gentle-ai --version` | View installed version |
| `engram search "<query>"` | Search persistent memory |
| `engram projects list` | List projects with memories |
| `engram tui` | Interactive UI to explore memory |
| `gga --help` | Guardian Angel help (Block 6) |

### B · Folder structure that gentle-ai writes

**Global (all in `~/`):**

| Path | Content |
|---|---|
| `~/.gentle-ai/state.json` | Installation state, agents, versions |
| `~/.engram/engram.db` | SQLite database with memories |
| `~/.engram/engram` | Engram binary |
| `~/.claude/` | Persona, skills, MCP wiring |
| `~/.windsurf/` | Persona, MCP, skills (Plan Mode integration) |
| `~/.kiro/steering/gentle-ai.md` | Kiro global steering |
| `~/.config/opencode/` | Plugins, MCP |
| `~/.codex/` | Model and effort configs |
| `~/.gemini/` | Global GEMINI.md, MCP, skills |
| `~/.pi/` | Pi agent harness (gentle-pi) |

### C · Troubleshooting

**`gentle-ai doctor` reports `degraded` due to duplicate warning**: cosmetic, non-blocking. Clean with `which -a <binary>` + uninstall the extra copy.

**Agent doesn't load skills**: verify skills are in the correct agent folder (`~/.claude/skills/` for Claude, `~/.cursor/skills/` for Cursor, etc.). gentle-ai does NOT copy skills between folders automatically — each agent reads from its own.

**OpenCode doesn't show sub-agents**: verify that `OPENCODE_EXPERIMENTAL=true` is in the shell and that you restarted OpenCode afterwards.

**AGENTS.md doesn't seem to be read**: verify the satellite for the IDE you are using exists (section 5.4). In Claude Code, `CLAUDE.md` must be at the project root with `@AGENTS.md`.

**Post-commit hook doesn't execute**: verify permissions with `ls -la .git/hooks/post-commit` — must have `x` (executable). If not, `chmod +x .git/hooks/post-commit`.

### D · Dependency risk on gentle-ai

This workflow is built on top of `gentle-ai` (`github.com/Gentleman-Programming/gentle-ai`) as a mandatory foundation. It is an open source project with good traction (4.2k+ stars, 500+ forks, 190+ releases at the time of writing), but it is still maintained by a small/individual team, not by an organization with long-term support guarantees. It's worth understanding the risk and plan if something changes.

**What already happened and what could happen again**: gentle-ai v4.0.0 retired the spec-driven workflow in favor of ODD, and with it the agents and skills that earlier releases installed. It is a real example of how a change inside gentle-ai can affect any part of this workflow that hardcodes command names, sub-agents, or gentle-ai paths, and this workflow does so in several places (`/wf-init`, `/wf-refresh`, `/wf-settings`).

**Current mitigation (no new tool required)**:
- **Periodic manual monitoring**: check `github.com/Gentleman-Programming/gentle-ai/releases` before recommending the wizard in a new project, or when the wizard fails unexpectedly. No cron or constant monitoring needed — the natural cadence is "I check when I'm going to use it or when something breaks".
- **Semi-automatic detection in the wizard**: Step 0.3.1 analyzes the text of gentle-ai release notes looking for risk signals near terms this workflow hardcodes, informs the developer on the spot, and leaves a draft ready to report it as an issue in this workflow's repo (see Block 4, section 8 and `/wf-init` Step 0.3.1 for full detail). This does not replace manual monitoring — it complements it by detecting in situ what a real developer encounters in production.

**What happens if gentle-ai stops being maintained or breaks compatibility severely**: Engram is a separate project from gentle-ai. gentle-ai orchestrates it but does not replace it. An abandonment of gentle-ai would mainly affect the multi-IDE configuration layer and native sub-agents, not Engram, which could continue to be used directly. There is no detailed migration plan yet because it hasn't been necessary; it will be documented if the situation arises.


---


