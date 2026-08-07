# AI Workflow Wizard

> Master document for the professional AI development workflow.
> Maintainer: hugoafj.

---

## ⚙ wf-init wizard architecture

> The `/wf-init` wizard is a **state machine with state persisted on disk**:
>
> - **State** (user responses + discovery) → `.wizard-state.json` at the project root
>   (contract: `wf-init/lib/state.md`). The process is resumable even if the
>   conversation is lost between phases.
> - **Permanent knowledge** (wf-ladder, wf-sdd-trigger, wf-tdd, SDD, CI/CD,
>   Testing, IDEs, Commands, Architecture) → `templates/protocols/<module/>` as **single
>   source of truth**, packaged as skills for each IDE (installed via `install.sh`).
> - **Assembly** → Deterministic Builder (`wf-init/lib/builder.md`) that assembles artifacts
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

**gentle-ai** — Ecosystem configurator. It is a binary installed once on your machine that configures ALL your agents (Claude Code, Cursor, etc.) with Engram, skills, MCPs, SDD, persona, and permissions. It is the foundation of this workflow.

**SDD (Spec-Driven Development)** — Methodology where before writing code you write artifacts: `proposal.md` (what), `specs/` (criteria), `design.md` (how), `tasks.md` (all). The agent does not implement until you approve each artifact. gentle-ai automates this in 10 phases.

**OpenSpec** — SDD framework that lives underneath gentle-ai. You do not invoke it directly; gentle-ai handles it for you. We only mention it because it is the internal machinery.

**GGA (Gentleman Guardian Angel)** — AI code review tool from the gentle-ai ecosystem. Reviews diffs and PRs applying defined standards. Provider-agnostic (works with Claude, Gemini, Codex, Ollama).

**TDD (Test-Driven Development)** — Methodology where you write the test BEFORE the code. In this workflow, the agent writes the test first, you approve it, then implements until the test passes.

**Conventional commits** — Commit message convention with prefixes (`feat:`, `fix:`, `chore:`, etc.) that enables automatic changelog generation and releases.

**Worktree** — Isolated git folder that shares the same repo. Useful for having multiple agents working in parallel without stepping on each other, each in their own worktree.

**Wizard `/wf-init`** — Global slash command for this workflow that initializes a project: installs and verifies gentle-ai automatically (Phase 0), discovers the project (Phases 1-4), runs `/sdd-init` with backend choice showing all three modes (Phase 4.5), generates `AGENTS.md` with "📋 wf-sdd-trigger" section (Phase 6), configures post-commit hook that detects AGENTS.md and SDD drift. Installed with `install.sh` as a global slash command. Architecture: orchestrator (`wf-init.md`) + phase files in `wf-init/` (read on-demand from disk).

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
6. [Block 2 · Specification Layer (SDD)](#6-block-2--specification-layer-sdd)
   - 6.1 [SDD Philosophy](#61-sdd-philosophy)
   - 6.2 [How gentle-ai handles SDD for you](#62-how-gentle-ai-handles-sdd-for-you)
   - 6.3 [How you invoke SDD without learning slash commands](#63-how-you-invoke-sdd-without-learning-slash-commands)
   - 6.4 [Greenfield vs Legacy](#64-greenfield-vs-legacy)
   - 6.5 [When SDD yes, when NO](#65-when-sdd-yes-when-no)
   - 6.6 [SDD persistence backends](#66-sdd-persistence-backends)
   - 6.7 [SDD integration with AGENTS.md](#67-sdd-integration-with-agentsmd)
   - 6.8 [Judgment Day — Automatic dual-judge review](#68-judgment-day--automatic-dual-judge-review)
7. [Block 3 · MCPs, Testing Stack and Commands](#7-block-3--mcps-testing-stack-and-commands)
8. [Block 4 · Orchestration and worktrees](#8-block-4--orchestration-and-worktrees)
    - 8.1 [What gentle-ai automates vs. what the wizard provides](#81-what-gentle-ai-automates-vs-what-the-wizard-provides)
   - 8.2 [Sub-agents and delegation](#82-sub-agents-and-delegation-native-to-gentle-ai)
   - 8.3 [Model routing per SDD phase](#83-model-routing-per-sdd-phase)
   - 8.4 [Worktrees — `/wf-worktree`](#84-worktrees--wf-worktree-built-in-this-block)
9. [Block 5 · TDD pro + Playwright integrated](#9-block-5--tdd-pro--playwright-integrated)
    - 9.1 [Strict TDD Mode](#91-strict-tdd-mode--what-it-is-and-how-it-works)
    - 9.2 [Architecture of three independent pieces](#92-architecture-of-three-independent-pieces)
    - 9.3 [TDD Mode](#93-tdd-mode--how-it-is-asked-and-what-changes)
    - 9.4 [Playwright dual-loop](#94-playwright-dual-loop--when-to-explore-before-versioning)
    - 9.5 [data-testid convention](#95-data-testid-convention--mandatory-when-e2e-is-present)
    - 9.6 [Optional extras](#96-optional-extras--coverage-targets-visual-regression-page-object-model)
    - 9.7 [Strategy for legacy projects without tests](#97-strategy-for-legacy-projects-without-tests)
    - 9.8 [/wf-settings — toggle optional modules](#98-wf-settings--toggle-optional-modules-after-installation)
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
- **SDD orchestrator**: 10 phases of Spec-Driven Development that the agent invokes automatically when the task warrants it. You don't have to learn slash commands.
- **Skills**: curated library (embedded foundation + community in `Gentleman-Skills`).
- **Preconfigured MCPs**: Context7 (live framework docs), Engram.
- **Automatic multi-IDE config**: configures Claude Code, OpenCode, Cursor, Windsurf, Codex CLI, Kiro, VS Code Copilot, Gemini CLI, Antigravity CLI, Pi, OpenClaw, Trae.
- **Persona**: senior architect teaching-oriented (or neutral if you prefer).
- **Permissions**: blocks destructive commands and sensitive paths (`.env`, `.ssh`, etc.) by default.
- **Model routing per phase**: each SDD phase can run on a different model (Opus for design, Sonnet for implementation, Haiku for exploration).
- **GGA (Gentleman Guardian Angel)**: AI code review (activated in Block 6).
- **Auto-updates**: via Homebrew/Scoop.

### 2.2 Custom Layer · Your project-specific workflow

On top of gentle-ai, in each repo. This is what you maintain. What it provides:

- **AGENTS.md**: project-specific context (stack, conventions, constraints, exact commands). gentle-ai's skills + persona still apply, but AGENTS.md tells the agent HOW THIS specific repo is.
- **Wizard `/wf-init`**: slash command that installs gentle-ai if not present, runs `/sdd-init` to initialize SDD in the repo, verifies system state, and bootstraps the project (generates AGENTS.md, configures hooks, adjusts .gitignore).
- **Post-commit hook**: detects structural drift and warns when AGENTS.md may need an update.
- **Project-specific satellites**: files in `.cursor/rules/`, `.windsurf/rules/`, `.kiro/steering/`, `CLAUDE.md`, etc. that point to the repo's AGENTS.md. **gentle-ai does NOT generate these satellites**, because gentle-ai is global and knows nothing about your individual repo. All satellites are always from the custom workflow (section 5.4 explains them in detail).
- **CI/CD pipeline**: GitHub Actions with quality guard + AI review (Claude Code Action or GGA).
- **Conventional commits + release-please**: traceable releases and automatic changelog.
- **`/wf-config`**: local setup command for devs who clone the repo (project-specific MCPs, etc.).

### 2.3 How they complement each other without clashing

gentle-ai writes to **global** folders (`~/.claude/`, etc.). Our custom satellites write to **project** folders (`.claude/`, `.cursor/`, etc.). Different files, different locations, **coexist without conflict**.

When you open an IDE in a project:

1. The IDE first reads the global config (from gentle-ai) → persona, skills, MCPs, SDD agents.
2. Then reads the project config (your AGENTS.md + satellites) → repo-specific context.
3. The agent combines both. The two layers complement each other.

---

## 3. The Day-to-Day Cycle

When everything is set up, a typical feature looks like this:

1. **New or existing repo** → you start in any state.
2. **`/wf-init`** once per repo → installs gentle-ai if missing, generates AGENTS.md + satellites + hooks.
3. **You open your AI IDE** → skills, MCPs, Engram, SDD orchestrator already active (courtesy of gentle-ai).
4. **You request a feature in natural language**. You don't learn slash commands.
5. **SDD orchestrator decides**: if the task warrants SDD, it starts the 10 phases automatically.
6. **Sub-agents work per phase**, each with their own model and fresh context.
7. **You approve at each gate** (after proposal, after specs, after design, before implementing).
8. **Human review gate** before commit: the agent shows you the full diff, waits for your approval.
9. **Commit with conventional commits** + the post-commit hook detects if AGENTS.md may need an update.
10. **PR + CI/CD pipeline**: Quality Guard (lint, types, tests, build) + AI review (GGA or Claude Code Action) + security scan.
11. **Merge + release-please** prepares the automatic release PR with changelog.
12. **Engram saves what was learned** for the next session.

**To visualize**: see the two diagrams in Appendix E.

---

## 4. gentle-ai · The Foundation

gentle-ai is the foundation of this workflow: it configures the complete AI agent ecosystem on your machine (persona, skills, SDD orchestrator, Engram, MCPs, permissions). **You don't need to install it manually before starting.** The `/wf-init` wizard detects it, installs it if missing, and configures it — all in its Phase 0.

This section exists as **reference**: what it is, what it installs, and advanced options you might need later.

### 4.1 What is gentle-ai in practical terms

It is a binary written in Go. It lives on your machine (`/opt/homebrew/bin/gentle-ai` on macOS, similar on Linux/Windows). When you run it, it **configures all the AI agents you have installed** to work better: connects Engram (persistent memory), installs skills, registers MCPs, injects persona, etc.

**It is model-agnostic**: works with Claude, GPT/Codex, Gemini, etc. **It is IDE-agnostic**: configures all the ones it detects.

What it installs on your machine (once, globally):

- **Engram**: persistent memory via MCP. Local SQLite, full-text search, shared across all IDEs.
- **SDD orchestrator + 10 sub-agents**: the agents that drive the Spec-Driven Development cycle. Live in `~/.claude/agents/`, `~/.cursor/agents/`, `~/.kiro/agents/`, etc.
- **Foundation skills**: SDD, workflow, testing. Embedded in gentle-ai.
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

> `--preset full-gentleman` activates everything: persona, skills, SDD, MCPs, permissions. It is the preset the wizard uses by default.

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
brew upgrade gentle-ai      # actualiza el binario
gentle-ai upgrade           # actualiza componentes internos (skills, sub-agents, configs)
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
- **Configure Models**: assign different models to each SDD pipeline phase and to Judgment Day (jd-judge-a, jd-judge-b, jd-fix-agent). For example, Claude Opus for `sdd-design`, a cheap model for `sdd-explore`. Also configures Codex lanes (strong/mid/cheap).
- **OpenCode SDD Profiles**: create and manage SDD profiles for OpenCode. After creating one, in OpenCode press `Tab` to switch between `gentle-orchestrator` (default) and your custom profiles.
- **Backup & Rollback**: lists automatic configuration snapshots (gentle-ai backs up before each install/sync/upgrade). You can pin a backup with `p` to protect it from auto-pruning (by default it keeps the 5 most recent). Useful if an update broke something.
- **Uninstall**: removes specific components from specific agents without deleting everything. Example: remove only `sdd` and `persona` from Cursor without affecting Claude Code.
- **Doctor**: equivalent to `gentle-ai doctor` in terminal, but with visual formatting.

**Useful shortcuts that are not obvious**:

- `p` in Backup & Rollback: pins the selected backup (not deleted by auto-pruning).
- In Configure Models: you can assign models per-phase without needing the CLI — the TUI writes the same files as `gentle-ai sync --profile-phase`.
- Upgrade from the TUI: if an update is available, the TUI shows the prompt "Apply now? [Y/n]". When updating gentle-ai from the TUI, the app restarts automatically after you confirm the result.

> **For dummies**: the TUI is useful for exploring what gentle-ai has installed and changing models per phase. For daily use, you don't need to open it — the workflow runs in the background. Open it when you want to adjust which model each SDD phase uses or review/restore a configuration backup.

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
- To verify that the agent correctly saved a decision after an SDD session.
- To diagnose why the agent proposed something unexpected ("what did it remember about the project?").

**What it does NOT show**: Engram TUI only shows explicit persistent memories (those the agent saved with `mem_save`). It does not show in-memory session context or the contents of `openspec/`. They are different layers.

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

**What changes between stacks** (mental map):

| Stack | Emphasis on Code Style | Emphasis on Critical Constraints |
| --- | --- | --- |
| React + Vite + TS | Component patterns, hooks rules, Tailwind syntax | React and Tailwind versions |
| Next.js fullstack | App Router vs Pages, server vs client components, fetching | Server/client boundaries, env vars, caching |
| Laravel + PHP | Eloquent patterns, queue handling, FormRequest, middleware | Artisan commands, namespaces, migrations |
| Backend Node/Express | Error handling, API contracts, auth, validation | Transactions, idempotency, rate limiting |
| Python FastAPI / Django | Type hints, Pydantic schemas, async patterns | DB sessions, dependency injection |

#### Concrete example: AGENTS.md for `crud-tasks-sdd-demo`

Stack: Vite 8 + React 19.2 + TS 6 + Tailwind 4 + ESLint 9 flat config. Size: ~82 lines. Covers the 6 mandatory sections + Behavior preferences + Trigger 3 of drift detection + version footer.

> **For dummies**: the AGENTS.md lives in the `AGENTS.md` file at the root of your repo. The agent reads it on its own. To validate it works, ask the agent for something and verify it respects the written rules.

### 5.3 Wizard `/wf-init` (greenfield + legacy)

Slash command that orchestrates the complete workflow bootstrap in a project. Split architecture — the orchestrator (`wf-init.md`) is the only thing attached to the chat; phases live in `wf-init/` (10 files) and the agent reads them from disk on-demand. This solves the "lost in the middle" problem a monolithic file would have: the agent only keeps the orchestrator + the active phase in context at any time.

The wizard phases:

- **Phase 0** — Self-contained prerequisite. Installs/verifies gentle-ai, runs `gentle-ai doctor`, confirms active agents for this project.
- **Phase 1** — Discovery (lists files, manifests, previous satellites, commits).
- **Phase 2** — Migration of previous artifacts (if any with their own content).
- **Phase 3** — Mode: greenfield vs legacy (auto-detect + confirmation).
- **Phase 4** — Reverse engineering (legacy only).
- **Phase 4.5** — SDD initialization. With the context already discovered (committers, stack, greenfield vs legacy), the wizard explains the three backends (engram / openspec / hybrid), makes a grounded recommendation, and runs `/sdd-init` with the user's choice. The wizard always shows all three modes — the user decides.
- **Phase 5** — Minimum questions (4-5 depending on path).
- **Phase 6** — File generation in memory (does not write yet). The AGENTS.md includes the "📋 wf-sdd-trigger" section as part of the base template.
- **Phase 7** — Human review gate (preview, approval).
- **Phase 8** — Write, handle `.gitignore`, install post-commit hook (detects AGENTS.md and SDD drift in the same hook), commit.

**How it is invoked**: with `install.sh` it is installed as a global slash command on all detected IDEs. You invoke it with `/wf-init` from any repo. The agent detects and reads the phase files from the repo as it progresses.

### 5.4 Project-specific satellites: what they are and why we need them

**Important clarification**: gentle-ai does NOT generate project-specific satellites. gentle-ai is **global**: it only knows about your machine (persona, skills, MCPs, SDD sub-agents). It has no way to know your individual repo or how to "point" to your project's specific `AGENTS.md`. **All project satellites are generated by the `/wf-init` wizard**.

#### What gentle-ai installs globally (NOT project satellites)

These files live in `~/`, are common to all your projects, and do NOT know your repo:

- `~/.claude/` — persona, SDD sub-agents, skills, MCP wiring.
- `~/.cursor/agents/sdd-*.md` — 10 sub-agents for Cursor.
- `~/.windsurf/` — persona, MCP, skills (Plan Mode).
- `~/.kiro/steering/gentle-ai.md` — global steering.
- `~/.kiro/agents/sdd-*.md` — 10 Kiro sub-agents.
- `~/.config/opencode/`, `~/.codex/`, `~/.gemini/`, etc.

#### What your `/wf-init` wizard generates (these ARE project satellites)

These live in the repo. Each one connects its specific IDE to THIS project's `AGENTS.md`:

- `AGENTS.md` — the content (source of truth).
- `CLAUDE.md` with `@AGENTS.md` (Claude Code does not read AGENTS.md natively).
- `.github/copilot-instructions.md` (Copilot does not read AGENTS.md).
- `.cursor/rules/project.mdc` (optional in 2026; Cursor already reads AGENTS.md natively).
- `.windsurf/rules/project.md` with `trigger: always_on` (Windsurf does not read AGENTS.md).
- `.kiro/steering/project-context.md` (Kiro partial).
- `GEMINI.md` (Gemini CLI partial) — `ANTIGRAVITY.md` (Antigravity CLI).
- `post-commit` hook for drift detection.
- Exceptions in `.gitignore` so satellites are versioned.

#### How both layers coexist without clashing

When you open an IDE in a project, the agent loads both:

1. **gentle-ai global config** → persona, skills, MCPs, SDD agents.
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

**`.github/copilot-instructions.md`**:

```markdown
# GitHub Copilot Instructions
Apply the conventions defined in `AGENTS.md` in all your responses.
[See AGENTS.md](../AGENTS.md)

<!-- MIGRATION NOTE: Copilot does not read AGENTS.md natively. Delete when adopted. -->
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
     Project-level SDD skills are written to both .windsurf/skills/ and .devin/skills/ for dual IDE support. -->
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

**Trigger 2 · Slash command `/wf-refresh`**. When invoked, the agent runs two layers:

- **Layer 1**: re-runs Phase 4 of the wizard (reverse engineering), compares with AGENTS.md, proposes diffs.
- **Layer 2**: reads the AGENTS.md footer (`wf-version` + `source`), fetches from GitHub, compares local vs remote version. If there is a new version, shows the changelog and proposes template updates.

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
<!-- wf-version: 0.1.0-beta.1 | source: github.com/hugoafj/ai-workflow-wizard | stack: vite-react-ts | optional-features: decision-ladder=yes -->
```

The `optional-features` field is new and critical. It tracks which optional features of the wizard the user accepted or rejected. Without it, every time the wizard ships a new feature, the system wouldn't know if the user already considered it or if it's new to them.

**Three wizard distribution options**:

1. **GitHub as source of truth** (recommended). Wizard lives in repo `github.com/hugoafj/ai-workflow-wizard` with tagged versions. Agent fetches + compares when running `/wf-refresh`.
2. **Package manager** (npm/composer/pip). For large teams.
3. **Manual convention with changelog**. No additional infrastructure.

**Recommendation**: Option 1 to start.

#### Intelligent refresh mechanism · Three layers

`/wf-refresh` does not just apply changes. It is a command with **three analysis layers** that run sequentially. This solves the core problem: when new wizard versions ship with new features, the user does NOT have to clean up and re-run the wizard. Refresh integrates them incrementally.

**Layer 1 · Project content drift**

Re-runs Phase 4 of the wizard (reverse engineering) on the current repo state. Compares with the existing `AGENTS.md`. Detects new scripts, reorganized folders, added dependencies, conventions that evolved. Proposes specific diffs. You approve each one.

**Layer 2 · Wizard template drift (mandatory changes)**

Reads the AGENTS.md footer: current `wf-version`. Fetches the wizard repo and compares versions. Reads the changelog and separates changes into two categories:

- **Mandatory changes** (bug fixes, obsolete template fixes). These changes are proposed for automatic application (with human review before writing).
- **Optional changes** (see layer 3).

**Layer 3 · New optional features**

This is the key piece for the workflow to evolve without forcing the user to re-run the wizard. The wizard maintains a registry of optional features.

When running `/wf-refresh`, layer 3 does the following:

1. Reads `optional-features` from the local AGENTS.md footer. Example: `decision-ladder=yes`.
2. Fetches the remote wizard and reads its `OPTIONAL_FEATURES.md` file that lists all optional features.
3. **For each feature the wizard has but is NOT in `optional-features` of the local AGENTS.md**: asks you. Example:

```
Two optional features are available that your AGENTS.md does not include:

1. Test pyramid documentation
   Adds a subsection to Testing with the suggested test pyramid for your stack.
   Include? [yes / no / explain more]

2. Performance budgets
   Adds performance constraints (Lighthouse scores, bundle size limits) to Critical Constraints.
   Include? [yes / no / explain more]
```

4. For each user response, updates `optional-features` in the AGENTS.md footer. Example after: `decision-ladder=yes,test-pyramid=no,performance-budgets=yes`.
5. Features marked with `=no` are not asked again in future refreshes, unless the user explicitly requests re-review with a flag (`/wf-refresh --reconsider-skipped`).

#### When refresh is NOT enough and you need to re-run the wizard

Rare cases where refresh cannot resolve the change:

- **Complete restructuring of the AGENTS.md schema** (e.g., if in v3.0 we change from 7 sections to 4 renamed sections). In that case the footer marks `major-version-bump-required: true` and refresh recommends re-running `/wf-init` in migration mode (preserves custom content marked with `<!-- WF: DO NOT REGENERATE -->`).
- **Fundamental change in workflow architecture** (e.g., if we decided to switch from gentle-ai to Superpowers as foundation). In that case refresh does not apply; it is a manual migration with explicit guidance.

These cases are rare (1-2 times per year max) and are announced in the wizard changelog with a "Breaking changes" section. **Design goal: 99% of workflow evolutions are handled via refresh, not by re-running the wizard**.


### 5.6 Step-by-step tutorial · Test the wizard on a clean project

> The wizard (`/wf-init`) verifies and installs gentle-ai automatically in its Phase 0 — you don't need to do it beforehand. You can run the wizard in any project state: clean, with previous artifacts, or legacy with existing code.

#### Step 1 · Open the project from its root

This is the only thing that matters before running the wizard: **open the IDE exactly from the repo root folder**, not from a parent folder. If you open from the parent, the agent won't find `AGENTS.md` or `openspec/` because its working directory is not the repo's.

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

The wizard lives in the `workflow-wizard` repo: the orchestrator is `wf-init.md` (85 lines) and the phase files are in `wf-init/`. Make sure you have the repo cloned on your machine. The agent detects the location automatically.

#### Step 4 · Open a new Claude Code session (or your preferred IDE/CLI)

> Important: **new session**, do not continue one you had open. The wizard needs to start from scratch.

```bash
cd ~/path/to/your-project
claude
```

(or `cursor`, `opencode`, etc., depending on your IDE)

#### Step 5 · Paste the orchestrator as the first prompt

Open `wf-init.md` in another editor (it's only 85 lines). Select all (Cmd+A / Ctrl+A). Copy it. Paste it into the new AI IDE session as the first message.

> Don't add anything before or after. The agent will locate the phase files on your machine and read each one as it progresses. You don't need to attach anything else.

#### Step 6 · Follow the interactive phases

The agent will process the wizard phase by phase. **Each phase ends with a PAUSE and a question**. Answer, wait for the next phase, repeat.

What you will see, in order:

**Phase 0 — Self-contained prerequisite**. The agent checks if gentle-ai is installed. If not, it installs it automatically (asks for confirmation and explains why it is mandatory). If already installed, it compares local vs remote version and recommends whether the update is mandatory or suggested. Then runs `gentle-ai doctor` and shows you the health summary. At the end it asks which configured agents you will use in this project — that determines the satellites generated in Phase 6.

**Phase 1 — Discovery report**. The agent lists the files it found, the detected stack, etc. Approve to continue.

**Phase 2 — Migration**. If it found satellites with their own content (shouldn't happen on a clean project), it asks what to do. On a clean project it jumps directly to Phase 3.

**Phase 3 — Mode**. Tells you if it classified as greenfield or legacy. Confirm.

**Phase 4 — Reverse engineering**. Legacy only. Reports detected conventions. Confirm or correct.

**Phase 5 — Minimum questions**. 4-5 questions depending on path. Answer short and specific. The key question is **which IDEs/CLIs you will use** — that determines the custom satellites generated.

**Phase 6 — In-memory generation**. The agent assembles all files but does NOT write them yet. The generated AGENTS.md includes the abbreviated SDD flow in Behavior Preferences by default.

**Phase 7 — Review gate**. Shows you the complete AGENTS.md and the list of files to be created. **Read them carefully**. If something doesn't fit, say "let me edit X first" and describe the change. The agent adjusts and shows again.

**Phase 8 — Write and commit**. Only if you said "yes" in Phase 7. The agent writes files, handles `.gitignore`, installs the hook, does `git add -f` and `git commit`. **Does NOT push** — that's your decision.

#### Step 7 · Validate the result

After the wizard finishes, in another terminal:

```bash
# View the commit
git log -1 --stat

# Verify created files
ls -la AGENTS.md CLAUDE.md
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
- **When you're ready**, advance to Block 2 (SDD) to start using the spec flow before implementing non-trivial features.


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

This section documents an optional but highly recommended improvement: integrating the **Decision Ladder** pattern into the project's AGENTS.md, or as a global gentle-ai skill.

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

#### Where to integrate it

Two options, not mutually exclusive:

**Option A · In the project's AGENTS.md** (recommended to start). Add the decision ladder as a subsection of "Behavior preferences":

```markdown
## Behavior preferences

[...rest of behavior preferences...]

### Decision Ladder (before writing any code)

Before proposing any implementation, go through this ladder in order and
**declare out loud each rung and its answer**. Do not apply the ladder in
silence — the analysis output must be visible so the user can
audit it. Stop at the first rung where the answer is "yes" and use it.

**When it applies:**

The Ladder applies **always before Preflight**, in all paths. This is
intentional: the Ladder can simplify a task before classifying it — if
it detects that "it already exists in the code" (rung 2), the task can go from `wf-force-sdd`
to `wf-no-sdd`. `wf-preflight` uses the Ladder result as input for classification.

Universal order: 🪜 **Ladder → 🔍 Preflight → flow by path**.

In Paths B and C, the Ladder applies **a second time** inside `sdd-apply`,
before implementing each individual task — the SDD pipeline already approved the what and
the how, and the Ladder confirms that each implementation follows the minimum path.

Mandatory output format:

```
🪜 DECISION LADDER
  1. Does this need to exist? → <answer and brief reason>
  2. Does it already exist in the code? → <answer and brief reason>
  ...
  ✓ Rung N — <what is used or done and why>
```

1. Does this really need to exist? If not, skip it.
2. Does it already exist in this codebase? If yes, reuse instead of rewriting.
3. Does the language's standard library already do it? If yes, use the standard library.
4. Is it a native platform feature? If yes, use the native approach (e.g.: native `<input type="date">` instead of installing a heavy lib).
5. Is there already a dependency installed in the project that serves? If yes, use it.
6. Can it be done in a single line? If yes, do it in one line.
7. Only if none of the above apply: write the minimum necessary code that works.

Only the rungs evaluated up to the ✓ are declared.
Under `wf-force-sdd`, the Ladder applies once per task — not to the full pipeline.
```

**Option B · As a project-specific command** (generated in Block 3, section 7.5). The `/wf-ladder` command allows the user to force it explicitly and see the agent's reasoning rung by rung. The ladder rules stay in `AGENTS.md`; the command is the shortcut to invoke it consciously.

Recommendation: use Option A (AGENTS.md) as the base — the agent always follows it. The Block 3 command adds the ability to force and audit it explicitly.

#### Related frameworks (future reference, don't integrate now)

If in the future you evaluate replacing the gentle-ai foundation with another, the serious candidates are:

- **Superpowers** (`github.com/obra/superpowers`) — 93k-150k stars. Agentic skills framework with SDD methodology, brainstorming, automatic worktrees, subagent-driven dev, strict TDD, code review. Works with Claude Code, Cursor, Codex, Gemini CLI, Copilot CLI, OpenCode, Pi, Antigravity, Kimi Code, Factory Droid. Created by obra (Jesse Vincent, ex-Anthropic). Technical difference with gentle-ai is small; community/maturity difference favors Superpowers. **Reason not to migrate now**: gentle-ai is already installed and validated in your setup, and Engram (persistent memory) is a real differentiator of gentle-ai that Superpowers has no equivalent for. The day you decide to migrate, the only thing that changes is section 4 of the master document (the foundation); the rest of the workflow stays the same because the foundation is replaceable by design.

- **Decision Ladder** — Anti-over-engineering prioritization pattern (origin: Ponytail project, `github.com/DietrichGebert/ponytail`). Integrated as a practice in this workflow (see section 5.8).

- **EDD (Evaluation-Driven Development)** — Pending evaluation. EDD means different things depending on context: prioritizing eval datasets in AI-internal systems (chatbots, agents, RAG), a variant of TDD for performance-critical code, or a generalist "pre-evaluation" approach. Useful if you build products that use AI internally; overkill for typical CRUD apps. Will be covered in Block 5 if the project warrants it.

---

## 6. Block 2 · Specification Layer (SDD)

### 6.1 SDD Philosophy

#### The problem SDD solves

Working with AI without structure produces a predictable pattern: vague prompt → code that seems to work → you ask for adjustments → model "fixes" things → you lose context between sessions → after 3-5 iterations the code diverges. The industry called it **vibe coding**: trusting that a good prompt and the smartest model are enough. They are not.

**SDD (Spec-Driven Development)** is the structural correction: before the agent touches code, there are markdown artifacts that describe **what to build** and **how to build it**. Those artifacts are versioned, approved, and are the contract against which the agent implements.

#### The mental shift

The hardest part of adopting SDD is not technical, it's psychological. The instinct is: "let me start writing and figure it out as I go". SDD inverts that: "let me solve it first, then write". With AI this is the right approach because AI implements fast — the slow phase is understanding what is wanted. If you understand what you want before asking for implementation, the AI goes to the goal at maximum speed. If not, the AI goes fast in the wrong direction.

The sentence that captures the principle: _"Vibe coding optimizes for the first iteration. SDD optimizes for the tenth — the one you have six months later when you've already forgotten what you built."_

#### Two layers of context

- **AGENTS.md** = persistent **project** context. How to work in this repo.
- **Specs (SDD)** = context per **change**. What to build in this specific feature.

The agent reads both. The two separate layers keep the context window clean.

### 6.2 How gentle-ai handles SDD for you

gentle-ai comes with an **SDD orchestrator** that drives the entire Spec-Driven Development flow. Underneath it uses OpenSpec, but you **don't interact with OpenSpec directly** — the orchestrator makes all the calls and decisions. Your interface is **natural language** with the agent.

#### The 10 orchestrator phases

The orchestrator defines a 10-phase cycle for a change (feature, refactor, non-trivial fix). Each phase is a **specialized sub-agent** with its own fresh context, assigned model, and specific permissions:

1. **`sdd-onboard`** — Only the first time in a project. Reads existing code, identifies patterns, generates initial context for gentle-ai (saves it in Engram).
2. **`sdd-explore`** — Research when the problem is not clear. Reads related code, searches Engram for previous decisions, proposes alternatives. Ends with a concrete understanding of the problem.
3. **`sdd-propose`** — Generates `proposal.md`: what will change, why, user-visible impact, rollback strategy. Waits for your approval.
4. **`sdd-spec`** — Generates `specs/` with requirements in Given/When/Then format (BDD style). These are the **acceptance criteria** that will feed into Block 5 tests. Waits for your approval.
5. **`sdd-design`** — Generates `design.md`: technical approach, decisions, trade-offs, new APIs. If there's a significant architectural decision, proposes adding it as an ADR (Architectural Decision Record). Waits for your approval.
6. **`sdd-tasks`** — Generates `tasks.md`: implementation checklist with executable TODOs. Each with a clear "done" criterion.
7. **`sdd-apply`** — Implementation. Takes each task, writes tests first (if the project has a TDD framework), implements until green. Marks tasks completed as it progresses.
8. **`sdd-verify`** — Final validation. Runs the AGENTS.md programmatic checks (lint, typecheck, tests, build). Validates acceptance criteria against implementation.
9. **`sdd-archive`** — When all tasks are complete and verify passes, moves the change to `openspec/changes/archive/` and merges the deltas to the source of truth in `openspec/specs/`.
10. **`sdd-finalize`** — Generates summary, saves decisions in Engram for future sessions, prepares commit/PR context.

#### Execution modes by agent

gentle-ai adapts how phases run depending on the IDE:

- **Claude Code and Cursor**: each phase is delegated to a **native sub-agent** of the IDE, with fresh context window. Benefit: no context contamination between phases, different model per phase if you configured model routing.
- **OpenCode**: uses the native task subagent system (post v0.13).
- **Pi**: global agents in `~/.pi/agents/sdd-*.md`.
- **Windsurf Cascade**: gentle-ai's own installed content classifies it as solo-agent — *"there are no sub-agents. Every SDD phase runs inline in the same conversation"*. Native Plan Mode is used to save/persist artifacts across sessions.
- **Devin (fork of Windsurf, shares its file paths)**: gentle-ai has **no dedicated adapter for Devin** — it isn't in gentle-ai's capability manifest at all, so gentle-ai's "Windsurf" content (including the "no sub-agents" claim above) gets applied to Devin by accident, not by design. In practice Devin does support real subagent delegation (a working `run_subagent`-style tool). Don't trust the IDE-name label alone — check whether a real subagent tool is actually available in the current session before assuming either capability.
- **Kiro**: 10 native files in `~/.kiro/agents/sdd-*.md`, auto-delegate by YAML description.
- **Others**: SDD runs **inline** in the same session. The orchestrator is the executor. Engram provides persistence between phases.

#### Where artifacts live

Independent of the agent:

```
openspec/
├── specs/                          ← source of truth (current state)
│   └── (active product specs)
├── changes/                        ← proposed modifications
│   └── <change-id>/
│       ├── proposal.md
│       ├── specs/                  ← delta specs (ADDED/MODIFIED/REMOVED)
│       ├── design.md
│       └── tasks.md
└── changes/archive/                ← cambios completados
    └── YYYY-MM-DD-<change-id>/
        └── (frozen artifacts as historical reference)
```

When a change is archived, the **deltas** (what the change added/modified) are merged into `openspec/specs/` which grows organically. **You never rewrite the full spec**; you only describe the delta of the current change.

#### Engram in each phase

Each sub-agent can:

- **Search** Engram for relevant past decisions (`mem_search`).
- **Save** what was learned when finishing the phase (`mem_save`).

This means when you start a new change six months later, the sub-agents find what your team decided in past changes without you having to remember. It's the difference between vibe coding (single-turn memory) and professional SDD (persistent project memory).

#### Cross-IDE portability: can I start in one IDE and continue in another?

Yes, with an important distinction between **what is directly portable** and **what requires the new IDE to reorient**.

**What IS portable without friction**: the artifacts in `openspec/changes/<change-id>/` (`proposal.md`, `specs/`, `design.md`, `tasks.md`) are **plain markdown versioned in git**. They have nothing specific to Claude Code, Cursor, or any IDE. If you generated `proposal.md` in Claude Code, approved it, and then open the same repo in Windsurf, Windsurf can read that `proposal.md` exactly the same. The change state (which phase, what's approved) lives in the repo filesystem, not in the IDE session that generated it.

**What DOES require reorientation**: the *orchestration mechanism* varies by IDE (see "Execution Modes" table above). If you were in Claude Code using native sub-agents and switch to Windsurf (which runs everything inline, without sub-agents), the new IDE doesn't "resume the session" from the previous one — **it reads the existing artifacts from scratch** and continues the flow from there. It's like a colleague taking over your work: they don't inherit your session, but they do read your document.

**How to resume an SDD change in another IDE**: when opening the new IDE, explicitly tell it to continue an existing change:

```
There's an SDD change in progress in openspec/changes/filter-by-status/. The proposal.md
and specs/ are already approved. Continue from design.md.
```

The agent reads the existing artifacts, confirms their content with you (for safety, it doesn't assume what was approved in another session is still valid without your confirmation), and continues with the corresponding phase.

**What is NOT portable**: Engram context (persistent memory) IS shared between IDEs because Engram is a single local service on your machine (not per-IDE) — any agent with the Engram MCP connected sees the same memories, regardless of which IDE you saved them in. The only real exception is if you configured gentle-ai with `--scope=workspace` instead of global; in that case each repo has its own config and you need to verify the new IDE is also configured for that project.

**Quick summary**:

| Element | Portable cross-IDE |
|---|---|
| `openspec/changes/*/proposal.md`, `specs/`, `design.md`, `tasks.md` | Yes — plain markdown in the repo |
| Approval state of each phase | Yes, but the new agent must confirm with you when resuming |
| Engram (persistent memory) | Yes — shared local service, unless different scope=workspace per project |
| Orchestration mechanism (sub-agents vs inline vs Plan Mode) | No — each IDE uses its own mode, but all read the same artifacts |
| Active session / conversational context of previous IDE | No — the new IDE does not inherit the conversation, only the files |

### 6.3 How you invoke SDD without learning slash commands

The goal of gentle-ai's orchestrator is that you don't need to know which phase you're in or which sub-agent to run. You speak in natural language and the system decides. Here's the actual mechanics.

#### Two independent axes operate in parallel

gentle-ai has its own **global Delegation Stop Rules** (4+ file rule to understand a flow, 2+ non-trivial file rule to modify, etc.). These always apply — they belong to the orchestrator and are not overridden.

What this workflow adds on top is **`wf-sdd-trigger`**, a two-outcome decision (`wf-no-sdd` / `wf-force-sdd`, with `wf-sdd-lite` as a lighter severity) that the agent applies to each local change before touching the workspace. It's a different axis: gentle-ai's own native routing decides Direct inline vs Delegated direct and owns all delegation mechanics; `wf-sdd-trigger` decides only WHEN this project's own rules require explicitly requesting gentle-ai's SDD. They don't conflict; they are complementary axes, and `wf-sdd-trigger` never re-specifies HOW gentle-ai then routes or delegates.

#### wf-sdd-trigger: the two outcomes

The AGENTS.md generated by the wizard includes a "📋 wf-sdd-trigger" section that defines the complete decision tree in detail. It decides ONE thing: does this change meet this project's own rules for explicitly requesting gentle-ai's SDD? It never decides HOW gentle-ai then routes or delegates — that remains gentle-ai's own native authority, already installed for the active adapter(s). Summary:

- **🟢 `wf-no-sdd`**: deterministic changes where there is an obvious implementation and design risk is minimal. Direct implementation; gentle-ai's own native routing (Direct inline / Delegated direct) decides the rest.
- **🔴 `wf-force-sdd`**: the change meets this project's own SDD-forcing rules. Two severities:
  - **`wf-sdd-lite` severity**: the change requires validating a design decision with the user because there are several reasonable approaches that produce different functional behaviors. It must meet five constraints (max 3 files, no new abstractions, no altering public contracts, fully reversible, single approach after analysis). If any fails, it automatically escalates to full severity.
  - **Full severity**: the change modifies architecture, public contracts, data model, or breaches any `wf-sdd-lite` constraint. The agent explicitly requests gentle-ai's full indexed SDD pipeline. No options to skip the harness.

#### The mandatory wf-preflight

Before writing code, planning, or requesting SDD, the agent issues a **single definitive diagnosis** called `wf-preflight` with: determined outcome (`wf-no-sdd`/`wf-force-sdd`), severity if forcing, impact analysis, and for `wf-sdd-lite` severity a 5-item checklist marked ✓/✗ without semantic interpretation. A single ✗ escalates to full severity. This closes the gap where the agent might "forget" to declare its outcome — the declaration is auditable, and if it later contradicts itself (says `wf-no-sdd` but modifies public contracts), you catch it on the spot.

#### The blocking protocol at wf-sdd-lite severity

When `wf-preflight` determines `wf-force-sdd` at `wf-sdd-lite` severity, the agent stops and shows a menu of three options:

1. **Execute wf-sdd-lite** → explicitly requests gentle-ai's `sdd-propose` → `sdd-tasks` → `sdd-apply` (this wizard's own name for the request, never a gentle-ai command). In standard mode, after `sdd-tasks` **the orchestrator issues the 🧪 TDD PROPOSAL and waits for the user's choice BEFORE requesting** `sdd-apply` (which is headless), then makes the request with the *baked* decision + a reference to `wf-tdd` (see "How TDD enters `sdd-apply`" in the SDD integration section). How gentle-ai delegates/executes these phases is its own native decision per adapter — never specified here. When finished with tests/checks green, suggests `sdd-archive` as cleanup (does not run it alone).
2. **Escalate to full severity** → ignores the `wf-sdd-lite` shortcut and explicitly requests gentle-ai's full indexed SDD pipeline instead.
3. **Ignore SDD (Direct)** → skips harnesses, jumps to code under the user's risk.

The agent cannot write code or detail technical tasks until it receives the option number.

#### How to correct the flow manually

If the agent determined `wf-no-sdd` and you prefer SDD:

```
Before implementing, I want the full SDD flow: exploration, proposal, specs, design, tasks. Do not implement until I approve each artifact.
```

If the agent determined `wf-force-sdd` and you confirm it's trivial:

```
This task is simpler than what you classified in the wf-preflight. Reclassify as wf-no-sdd and implement directly. The AGENTS.md constraints still apply.
```

> The exact text of the "📋 wf-sdd-trigger" section lives in each project's AGENTS.md (the wizard injects it in Phase 6, and `wf-refresh` syncs it in Layer 2). This section 6.3 is only the conceptual summary.

#### The human gate in each phase

After each artifact (proposal, specs, design, tasks), the orchestrator **stops and waits**. It does not continue until you say something. The responses that make it advance:

- **Approval**: "Approved", "LGTM", "continue", "ok, continue with specs".
- **Approval with comments**: "Approved, but before specs: add a constraint that the filter must work without JS too." → The agent incorporates the feedback and regenerates if needed before advancing.
- **Rejection**: "Rejected. The design approach assumes react-router but we don't have it. Propose an alternative with native URL API." → The agent goes back to the previous phase.

> **For dummies**: the gate is not a rhetorical question. If the agent asks "does the proposal look good to you?" and you keep not responding, it doesn't advance. If you say "yes" without reading, the contract is yours. Read the artifact. The value of SDD is in those approvals.

#### Visual flow of a typical SDD session

```
You: "Add task filter by status with URL persistence"
                    │
                    ▼
         [Orchestrator evaluates]
         Does it warrant SDD? → Yes
                    │
                    ▼
         sdd-explore: reads code, searches Engram
                    │
                    ▼
         sdd-propose → generates proposal.md
                    │
                    ▼
         ┌─── GATE: waits for approval ─────────────────────┐
         │  You review proposal.md. Approve or reject.      │
         └──────────────────────────────────────────────────┘
                    │ (approved)
                    ▼
         sdd-spec → generates specs/ (Given/When/Then)
                    │
                    ▼
         ┌─── GATE: waits for approval ─────────────────────┐
         └──────────────────────────────────────────────────┘
                    │ (approved)
                    ▼
         sdd-design → generates design.md
                    │
                    ▼
         ┌─── GATE: waits for approval ─────────────────────┐
         └──────────────────────────────────────────────────┘
                    │ (approved)
                    ▼
         sdd-tasks → generates tasks.md
                    │
                    ▼
         ┌─── GATE: waits for approval ─────────────────────┐
         └──────────────────────────────────────────────────┘
                    │ (approved)
                    ▼
         sdd-apply → implements (TDD if configured)
                    │
                    ▼
         sdd-verify → lint, types, tests, build
                    │
                    ▼
         ┌─── GATE: human diff review ──────────────────────┐
         │  You review the full diff before committing.      │
         └──────────────────────────────────────────────────┘
                     │ (approved)
                    ▼
         sdd-archive + sdd-finalize → commit, Engram
```

#### What to do when the agent "skips" a gate

This can happen with more impatient models (or if your initial prompt already sounded like approval). If you notice the agent went from proposal to specs without asking for approval:

```
Stop. Show me the full proposal.md again. Do not continue until I explicitly approve it.
```

The magic phrase is always **"stop"** or **"don't continue"**. Well-configured agents respect this.

### 6.4 Greenfield vs Legacy

The orchestrator has two start modes (`sdd-explore` phase works differently in each). The `/wf-init` wizard already did the diagnosis when you configured the repo (Phase 3 of the wizard), and left that context in AGENTS.md. The orchestrator reads it and adjusts.

#### Greenfield (new project, empty or minimal codebase)

`sdd-explore` in greenfield is short: no existing code to read, no Engram project memories. It does three things:

1. Reads `AGENTS.md` to understand the stack and conventions.
2. Searches Engram for past decisions from similar projects (rare in greenfield).
3. Proposes the file structure it will create before doing so.

The `proposal.md` in greenfield is more detailed in the "what is created from scratch" section because there is no reference code the agent can assume.

**Typical greenfield pattern**: the first SDD change (the project's main feature) starts with `sdd-onboard` → `sdd-propose` → specs → design → tasks → apply. Subsequent changes skip `sdd-onboard` because Engram already has the initial context.

#### Legacy (existing project with working code)

`sdd-explore` in legacy is where the orchestrator earns its real value. Before proposing anything:

1. Reads files directly related to the feature.
2. Searches Engram: are there past decisions about this module? was something similar attempted before?
3. Identifies implicit constraints: naming conventions, component patterns, existing hooks that could be reused (Decision Ladder applied to real code).
4. Detects relevant technical debt: if the module to be touched has known problems, it mentions them in `sdd-explore` before the proposal ignores them.

Only after that context does it write the `proposal.md`. The proposal in legacy always includes a "Relevant Existing Code" section with the files/functions it found, so you can validate the agent understood the context before designing.

#### The delta concept

In SDD, **you never rewrite the full product spec**. Each change is a delta: it describes only what changes from the current state.

Structure of a delta in `openspec/changes/<change-id>/`:

```
specs/
  filter-by-status.md        ← change spec (ADDED)
  task-list.md               ← existing spec modification (MODIFIED)
                             ← (existing spec that didn't change, not included)
```

The file in `specs/` that is `MODIFIED` describes only the delta: "Add `filter: TaskFilter` prop to `TaskList` component". It doesn't rewrite the entire `TaskList` spec. When the change is archived, that delta is merged into `openspec/specs/task-list.md` which grows incrementally.

Advantage of the delta approach: **the history is readable**. You can see in `openspec/changes/archive/` exactly what was changed in each feature, on what date, with what justification. It's the design changelog, not just the code changelog.

#### Summary table

| Aspect | Greenfield | Legacy |
|---|---|---|
| `sdd-explore` | Short. Reads AGENTS.md + global Engram. | Long. Reads real code + project Engram. |
| First change | Starts with `sdd-onboard` too. | Starts with `sdd-explore` (onboard already ran). |
| `proposal.md` | Details "what is created from scratch". | Includes "relevant existing code". |
| Main risk | Over-engineering without real reference code. | Breaking something existing the agent didn't see. |
| Risk mitigation | design.md approval is critical. | proposal.md approval is critical (verify the agent understood existing code). |

### 6.5 When SDD yes, when NO

The "📋 wf-sdd-trigger" section in each AGENTS.md (see 6.3) is the source of truth for classifying any change. This section 6.5 is the reference heuristic for understanding when to expect each outcome and why.

#### The 15-minute rule (quick calibration)

If an experienced human can implement the complete change, including tests, in less than 15 minutes without facing design decisions, it likely falls under `wf-no-sdd`. If it would take longer due to volume but the approach is clear, likely `wf-no-sdd` as well (mechanical refactors across many files still don't need forced SDD). If there are functional or UX decisions the user didn't specify but the change is bounded, `wf-force-sdd` at `wf-sdd-lite` severity. If it touches architecture, public contracts, data model, or any element that violates the five `wf-sdd-lite` constraints, automatic `wf-force-sdd` at full severity.

#### Reference table (when to expect each outcome)

| Type of change | Expected outcome | Why |
|---|---|---|---|
| Typo, label, copy fix | wf-no-sdd | Deterministic, no design |
| Dependency bump (patch/minor) | wf-no-sdd | No design decision |
| Color, size, spacing change | wf-no-sdd | Obvious implementation |
| Adding `console.log` for debug | wf-no-sdd | Temporary, no impact |
| Mechanical name refactor (few or many files) | wf-no-sdd | Mechanical even if touching many files |
| Documentation, comments, READMEs | wf-no-sdd | No production code |
| Isolated tests, fixtures | wf-no-sdd | No system behavior change |
| Extend existing flow with unspecified UX decision | wf-force-sdd (wf-sdd-lite) | Multiple valid behaviors, within wf-sdd-lite limits |
| New validation with decidible business rule | wf-force-sdd (wf-sdd-lite) | Needs to validate the what with the user |
| Non-trivial bug with two reasonable architectures after analysis | wf-force-sdd (wf-sdd-lite, escalates to full if a constraint fails) | Design decision albeit bounded |
| Feature with new global state or new shared hook | wf-force-sdd (full) | Modifies contracts / adds reusable abstractions |
| Feature with new API or endpoint | wf-force-sdd (full) | Public contract |
| Feature with new user-visible routing | wf-force-sdd (full) | Modifies system navigation model |
| Significant refactor (complete module) | wf-force-sdd (full) | Touches architecture |
| Dependency migration (major) | wf-force-sdd (full) | Breaking changes, real tradeoffs |
| Data model / schema change | wf-force-sdd (full) | Fundamental contract |
| Replace main library | wf-force-sdd (full) | Architecture |
| Convert synchronous APIs to async | wf-force-sdd (full) | Deep tradeoffs |

#### When the wf-preflight seems wrong

`wf-preflight` is auditable by design. If it declared `wf-force-sdd` at `wf-sdd-lite` severity but the checklist marks all 5 items ✓ without visible justification, or if it declared `wf-no-sdd` and started creating new files that contradict that classification, you have immediate evidence to request reclassification:

```
The wf-preflight declared wf-no-sdd but you are creating a new file (TaskFilter.tsx) that is a reusable abstraction. Reclassify.
```

The agent should not defend itself — it should re-emit a corrected `wf-preflight` and proceed according to the new outcome.

### 6.6 SDD persistence backends

When you run `/sdd-init` in a repo, gentle-ai asks which persistence backend to use. The choice is not trivial — it affects what is versioned in git, whether the team can share SDD context, and whether you will be able to evolve canonical specs. The official gentle-ai documentation is explicit about this.

#### The three backends

**engram** (persistent memory without versioned files). All decisions, specs, and SDD context live in the developer's local Engram. No canonical `openspec/specs/` is generated in the repo. The advantage is automatic cross-session persistent memory, without file noise in the repo. The main disadvantage, quoting the official documentation: "Engram-only mode is different by design: Engram is working memory and does not maintain a canonical spec merge layer." Without that layer, you cannot evolve versionable specs or share context with other developers via git.

**openspec** (versioned files in the repo). All SDD context lives in files: `openspec/config.yaml`, `openspec/specs/`, `openspec/changes/`. It is committed to the repo and shared with the team. The advantage is that specs are first-class artifacts with git history. The disadvantage is that you lose the cross-session persistent memory that Engram provides — each session starts by reading files, not remembering context from past sessions.

**hybrid** (both). Combines the best of both: versioned files in `openspec/` + persistent memory in Engram. The official documentation recommends it: "Use openspec or both (hybrid file + memory persistence) when you need canonical spec evolution". The cost is that there are two sources of truth that need to be kept consistent, but gentle-ai does this automatically via `sdd-sync` (merges file-backed deltas into the canonical spec) and `sdd-archive` (moves the archived change to history).

#### Which to choose based on your context

| Context | Recommended backend | Why |
|---|---|---|
| Solo project indefinitely, no plan to share | engram | Simple, no file noise |
| Solo project but could grow to a team | hybrid | Frictionless migration when devs join |
| Established team, professional use | hybrid | Official recommendation |
| Company with audit or compliance requirements | openspec or hybrid | Specs must be versionable artifacts |
| Learning project, throwaway | engram | No overhead |

**Default wizard recommendation**: hybrid, unless the user explicitly states they will work solo indefinitely.

#### Migration between backends

If you started with engram and now developers are joining, you can migrate to hybrid by re-running `/sdd-init`. But there is an important limitation: **decisions already saved in Engram are not retroactively transferred to the repo when you migrate**. Only new post-migration decisions will live in `openspec/`.

This means if you started engram-only and accumulated 6 months of context, migrating to hybrid leaves that historical context only in your local Engram — new developers joining will not have access to it without you manually extracting it. That's why the wizard recommends hybrid from the start, even if you start alone.

The reverse direction (hybrid → engram) is valid but rare — you lose the versioned specs layer, which is almost never desirable.

#### How the wizard handles the choice

#### Analysis of the real `openspec/config.yaml` (crud-tasks-sdd-demo)

This is the `config.yaml` generated by `/sdd-init` in the `crud-tasks-sdd-demo` test project:

```yaml
artifact_store: openspec
project: crud-tasks-sdd-demo
initialized: "2026-06-30"
refreshed: "2026-06-30"
version: "1.1"
context:
  stack: "Vite 8 + React 19 + TypeScript 6 + Tailwind CSS 4 + ESLint 9 (flat config)"
  type: SPA
  backend: none
  entry: src/App.tsx
  pattern: container-hook (useTasks owns state; presentational components receive props)
  state: useState + localStorage (no external state lib)
  styling: Tailwind 4 via @tailwindcss/vite; clsx + tailwind-merge for class merging
  testing:
    strict_tdd: false
    configured: false
    runner: null
    planned: "Vitest + Testing Library"
  layers:
    unit: false
    integration: false
    e2e: false
    coverage: false
  quality:
    linter: "eslint . (ESLint 9 flat config)"
    type_checker: "tsc -b (TypeScript 6 strict)"
    formatter: null
  checks_before_done:
    - npm run lint
    - npm run build
sdd:
  phases:
    - explore
    - propose
    - spec
    - design
    - tasks
    - apply
    - verify
    - archive
  changes_dir: openspec/changes
  specs_dir: openspec/specs
notes: |
  Migrated from engram-only mode to openspec on 2026-06-30.
  Prior SDD history (crud-tasks pipeline) lives in Engram under project crud-tasks-sdd-demo.
  New changes from this point forward will generate files under openspec/changes/.
  No test runner detected — strict_tdd disabled. Install Vitest before adding tests.
```

**What to do with this information**:

The `config.yaml` is not something you normally edit by hand — `/sdd-init` generates and updates it. What is useful to know:

- `artifact_store: openspec` confirms the chosen backend. It migrated from engram-only to openspec, as indicated in the `notes` field.
- `context.pattern: container-hook` is the most valuable for SDD sub-agents: they know `useTasks` owns the state and components are presentational. This prevents them from proposing to put state in components.
- `testing.configured: false` and `runner: null` tell the orchestrator not to generate tests yet — it respects `testing.strict_tdd: false`.
- `checks_before_done` is the equivalent of AGENTS.md "Programmatic Checks" for SDD phases: before archiving any change, the sub-agent must pass `npm run lint` and `npm run build`.
- `sdd.phases` lists the 8 pipeline phases in order — this is what the orchestrator follows. No invented phases.

**When to re-run `/sdd-init`**: when `testing.configured` changes from `false` to `true` (when you install Vitest), when the architectural pattern changes, or when the stack changes. The post-commit hook notifies when `package.json` changes (which is when most of those changes occur).

### 6.7 SDD integration with AGENTS.md

gentle-ai's SDD sub-agents read the project's `AGENTS.md` in every phase — it's not an optional integration, it's part of the pipeline. This means the conventions, Critical Constraints, and Behavior Preferences you defined in `AGENTS.md` are respected during `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, and `sdd-apply`.

The "📋 wf-sdd-trigger" section that the wizard injects into `AGENTS.md` is especially relevant here because gentle-ai's SDD phases use it to classify sub-tasks within a large change. Example: if in the `sdd-tasks` phase a task is generated that technically falls under `wf-no-sdd` (mechanical change), it can be executed directly without declaring a formal `wf-preflight` — but if it generates a task that falls under `wf-force-sdd` at `wf-sdd-lite` severity, it applies the blocking protocol before touching code.

The native `sdd-apply` skill resolves TDD mode by reading `openspec/config.yaml → strict_tdd`. With `strict_tdd: true` it loads `strict-tdd.md` and requires RED→GREEN evidence per task (headless, no interaction). With `strict_tdd: false` it falls into native standard mode. Since `sdd-apply` is a headless sub-agent (`user-invocable: false`) — it executes and returns, cannot ask the user anything — the `🧪 TDD PROPOSAL` happens **before** delegation: the orchestrator issues the proposal (task coverage, in batch), waits for the user's choice, and **only then** delegates to `sdd-apply` with the decision baked into the prompt.

If you detect that sub-agents ignore `AGENTS.md` in some phase, there are two possible causes: (1) `AGENTS.md` is too far from the repo root where the sub-agent started — verify the location; (2) the sub-agent started from a parent folder — same diagnosis documented in 5.7. The solution in both cases is the same as for direct IDEs.

### 6.8 Judgment Day — Automatic dual-judge review

gentle-ai includes a skill called `judgment-day` (visible in `internal/assets/skills/judgment-day/` of the repo) that implements a dual code review pattern with two independent agents in parallel. This skill activates automatically at SDD pipeline gates and requires no manual invocation.

#### How it works

The orchestrator launches two "judges" in parallel — `judge-a` and `judge-b` — each with its own session, no communication between them. Both review the same change looking for issues (bugs, vulnerabilities, contradictions with specs, convention violations). When both complete, the orchestrator synthesizes a verdict classifying each issue into four categories:

- **Confirmed** (both judges detected it) → high confidence, immediate fix.
- **Suspect A** (only judge A detected it) → requires triage.
- **Suspect B** (only judge B detected it) → requires triage.
- **Contradiction** (judges disagree on the same point) → flag for manual decision.

Confirmed issues go to a `fix-agent` (a third delegation, not one of the judges) that applies fixes. After fix, both judges re-launch in Round 2. The cycle continues until APPROVED or until the user decides to escalate.

#### When it activates

Judgment Day has a specific trigger: **dual adversarial review when there is real risk or high uncertainty** about whether the implementation is correct. It is not an automatic verifier for every `sdd-verify` phase — it applies when context warrants it.

**Activates automatically when**:

- Before commits/pushes with substantial changes per trigger-rules v1.33+.
- In OpenCode with profiles v1.34+, it is profile-scoped by default.
- When there is high uncertainty about the implementation (ambiguity in spec, complex code without strict type coverage, changes to shared contracts).

**Does NOT activate in `sdd-verify` when** the SDD pipeline already provided sufficient guarantees:

- The change followed a detailed spec (spec + design phases defined exactly what to produce).
- TypeScript strict already validated all contracts — if something was broken, `tsc -b` would have caught it in `checks_before_done`.
- No ambiguity in the implementation.

In those cases, `sdd-verify` runs the `checks_before_done` from `openspec/config.yaml` (`npm run lint` + `npm run build`) and that is sufficient. Judgment Day is not redundant — it simply doesn't apply when mechanical checks already guarantee correctness.

**Manually** — when you do want to force it:

- With `/judgment-day` in agents with slash commands enabled.
- When you want adversarial review of a PR before merging.
- When the agent implemented something without a prior spec and you want a structured second opinion.

#### Critical rules you should know

Directly from the skill:

- The judges never execute git commit / git push / code during review — they only detect.
- After a fix, the orchestrator MUST re-launch both judges before allowing commit/push.
- A single judge finishing does NOT allow skipping rounds of the other — each judgment day is independent.
- Warnings are classified as "real" (bug reproducible with normal use) vs "theoretical" (requires contrived scenario). Theoretical warnings are reported as INFO but do not block.

#### Interaction with the workflow flow

When applicable, Judgment Day runs after implementation but before human review. The order is: implementation → `checks_before_done` → Judgment Day (if applicable) → human review → commit. Human review cannot be skipped just because Judgment Day passed — they are complementary layers.

When not applicable (SDD pipeline with detailed spec + TypeScript strict), the order is simply: implementation → `checks_before_done` → human review → commit.

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

The wizard's goal is that the agent automatically runs tests as part of the SDD pipeline, without the user having to remember commands. For that, the wizard needs to configure the complete stack and update `openspec/config.yaml`.

**When it is configured**: in Phase 4.5 (or Phase 4.6 dedicated to the testing stack) of the wizard, when the user confirms they want testing. It can also be configured later when the post-commit hook detects changes in `package.json` relevant to testing.

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
3. Adds scripts to `package.json` (`test`, `test:ui`, `test:e2e`, `test:coverage`).
4. Updates `openspec/config.yaml` with `testing.configured: true`, active layers, and the runner.
5. Updates `AGENTS.md` "Testing" section with the real commands.
6. If the user activated Playwright: configures the Playwright MCP in the agent's folder.
7. Everything with human review gate before writing any files.

This makes `checks_before_done` in the SDD pipeline go from just `lint + build` to `lint + build + test` (or `lint + build + test + e2e` depending on layers). The agent runs it all automatically before archiving a change.

**TDD Protocol** (automatic when testing is configured — no opt-in, no question asked): in addition to running tests in `checks_before_done`, the agent **automatically writes them** before implementing each change. It evaluates which layers apply based on the type of change using the coverage matrix (unit for pure logic, integration for components, e2e for complete user flows), and issues a `🧪 TDD PROPOSAL` with its suggestion.

The proposal menu is dynamic: if the suggestion already covers unit + integration + e2e, it only shows Apply / Skip. If partial, it shows Apply / TDD Full / Skip. The agent follows the red-green-refactor cycle per task and when generating E2E specs always shows the exact command with `--headed` to see them run in the browser.

E2E naming conventions: one file per user flow named by the flow, not by the component (`persistence.spec.ts`, `task-creation.spec.ts`). The same convention is stored in `openspec/config.yaml` under `testing.conventions.e2e`.

Complete output order before implementing: 🪜 Ladder → 🔍 Preflight → 🧪 TDD Proposal → implementation.

### 7.5 Project-specific commands

Commands the wizard generates in Phase 6 and writes in Phase 8. They are project-specific markdown files — live in the repo, not globally. They are used as slash commands in the IDE (correct format per IDE).

**`/wf-ladder`** — forces explicit wf-ladder with visible `🪜` output per rung.
**`/wf-sdd-lite`** — explicitly requests gentle-ai's SDD at wf-sdd-lite severity (sdd-propose → sdd-tasks → sdd-apply). In standard mode, the orchestrator emits the 🧪 TDD PROPOSAL before requesting apply (headless) then makes the request with baked decision + a reference to `wf-tdd`. No spec or design; suggests sdd-archive at the end. `wf-sdd-lite` is this wizard's own name — never a gentle-ai command.
**`/wf-onboard`** — stub that points to `wf-onboard.md` for new developer onboarding.
**`/wf-refresh`** — stub that invokes the AGENTS.md refresh wizard.

**Global vs project-specific commands**: `wf-init`, `wf-refresh`, and `wf-cleanup` are installed globally with `install.sh`. `wf-onboard`, `wf-settings`, `wf-worktree`, and `wf-cicd` are generated per project in Phase 6. `wf-ladder` and `wf-sdd-lite` are project-specific — they have project context in their content.

**Correct paths and formats per IDE** (verified against official documentation):

| IDE | Directory | Format |
|---|---|---|
| Claude Code | `.claude/commands/` | Plain markdown, no frontmatter |
| Cursor | `.cursor/commands/` | Plain markdown, no frontmatter |
| Windsurf/Devin | `.windsurf/workflows/` | Frontmatter with `description:` required |
| Kiro | `.kiro/steering/` | Frontmatter with `inclusion: manual` |
| OpenCode | `.opencode/commands/` | Plain markdown, no frontmatter |
| Copilot | `.github/prompts/` | Suffix `.prompt.md` + `mode: agent` |

**Important**: `.cursor/rules/` and `.windsurf/rules/` are for context rules (always-on) — a different concept from slash commands. In Kiro, `inclusion: manual` turns a file into a slash command; `inclusion: always` makes it always-on (already covered by satellites).

The wizard detects active IDEs: on new projects it uses the Phase 5 list; on upgrades it reads existing satellites in the repo.

### 7.6 How to test that wf-ladder works

Three concrete tests. The Ladder must always appear **before `wf-preflight`** — that is the correct and validated order: 🪜 wf-ladder → 🔍 wf-preflight → flow.

**Test 1 — wf-no-sdd, Ladder should propose reusing existing:**

```
I need to show the number of completed tasks in the app header.
```

Expected: `🪜 WF-LADDER` appears before `🔍 WF-PREFLIGHT`. Stops at rung 2 because `useTasks` already exposes `tasks.filter(t => t.completed).length`. Success signal: `✓ Rung 2 — use tasks.filter(t => t.completed).length from useTasks`. No new hooks or state.

**Test 2 — wf-no-sdd, Ladder should reach rung 7:**

```
I need to validate that a task title doesn't have special characters like <, >, &.
```

Expected: `🪜` evaluates rungs 1-6 and none apply. `✓ Rung 7 — minimum validation function`. If it proposes installing a validation library, it did not apply rung 5 correctly.

**Test 3 — wf-force-sdd (full), Ladder in two moments (validated in production):**

```
Add a priority system to tasks (high, medium, low) with visual badge and ability to sort by priority.
```

Success signals:

- `🪜 WF-LADDER` appears first, before `🔍 WF-PREFLIGHT`. The Ladder informs `wf-preflight` — detecting rung 7 with 5+ coordinated files directly feeds full `wf-force-sdd` classification.
- Two `🔍 WF-PREFLIGHT` may appear if the agent tried `wf-sdd-lite` severity and escalated to full after the checklist — that's correct, shows the full reasoning.
- SDD pipeline runs with gates at each phase, once explicitly requested from gentle-ai.
- Inside `sdd-apply` (gentle-ai's own phase), the Ladder appears again per task confirming minimum implementation.

### 7.7 `/wf-onboard` — new developer cloning the repo

`wf-onboard.md` is the onboarding wizard for developers who clone a repo that already has the workflow configured. It does not modify the repo — only configures the local environment.

**Wizard phases**:

- **Phase 0**: reads the repo's AGENTS.md, especially the `## Project MCPs` section — source of truth for which MCPs each developer needs to configure.
- **Phase 1**: verifies and installs gentle-ai if missing. Detects which agents the team uses (by reading the repo's satellites) and compares them with the agents configured on the developer's machine. Configures missing ones.
- **Phase 2**: verifies SDD and Engram. Reads the backend from `openspec/config.yaml` and warns if the project uses engram-only (decision history is not shared).
- **Phase 3**: verifies and guides configuration of each project MCP. Automatic ones (Engram, Context7): no action. Playwright: verifies browsers. GitHub: `gh auth login` if missing. API key MCPs (Supabase, Stripe, Postgres): guides creation of local `.env.local`.
- **Phase 4**: final verification with status summary and project commands.
- **Phase 5**: suggests adding a mention to `/wf-onboard` in the README if it doesn't exist.

**How to use**: generated as a project-specific slash command in Phase 6 of `/wf-init`. Invoked with `/wf-onboard` from the cloned repo root.

**The project README should include**: "If you are new to this repo, run `/wf-onboard` to configure your local environment."

---

## 8. Block 4 · Orchestration and worktrees

### 8.1 What gentle-ai automates vs. what the wizard provides

| Capability | Does gentle-ai provide it? | Detail |
|---|---|---|
| Delegation to sub-agents | Yes, native | Via Agent tool in Claude Code, native system in OpenCode, inline (without spawning a separate process) in others |
| Rules for when to delegate | Yes, native | "Delegation Stop Rules" — see 8.2 |
| Model routing per SDD phase | Only in OpenCode | Via "SDD Profiles". In all other agents, SDD runs in single-mode with one model |
| Worktrees | No | gentle-ai does not create, list, or clean worktrees. It only has a reactive rule: if it detects a worktree/git accident, it requires a fresh audit before continuing |

### 8.2 Sub-agents and delegation (native to gentle-ai)

When the orchestrator agent (the one in your main session) delegates work to a sub-agent — for example, an `sdd-explore` to investigate code before proposing a change — that sub-agent is not a dumb script. It is a full agent with its own session, its own tools, and its own context.

**How this runs depending on which agent you use**:

| Agent | How it delegates |
|---|---|---|
| Claude Code | Via the Agent tool (Task tool) — the orchestrator launches focused sub-agents and injects already resolved project rules |
| OpenCode | Native sub-agent system — each phase is a dedicated agent with its own model, tools and permissions defined in `opencode.json` |
| Cursor | Native sub-agents, 10 SDD agents in `~/.cursor/agents/` |
| Kiro | Native sub-agents in `~/.kiro/agents/` with orchestration via steering |
| Windsurf Cascade | No sub-agents (solo-agent, per gentle-ai's own installed content) — inline for every phase |
| Devin (fork of Windsurf) | gentle-ai has no dedicated adapter for Devin, so it inherits Windsurf's "no sub-agents" content by accident. In practice Devin does support real subagent delegation (`run_subagent()`-style tool) — check your actual session toolset rather than trusting the inherited label |
| Codex | Native sub-agents in `~/.codex/agents/` with phase routing |
| Copilot | SDD runs inline in a single session — without spawning separate processes |
| Gemini CLI | SDD runs inline in a single session — without spawning separate processes |
| Antigravity CLI | SDD runs inline in a single session (known bug: gentle-ai doesn't install SDD skills in the correct path, see Known Issues) |

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

### 8.3 Model routing per SDD phase

SDD (Block 2) has phases: explore, propose, spec, design, implement, verify. Each phase has a different nature — exploring code doesn't need the most expensive model, but designing architecture does benefit from a more capable one. gentle-ai supports assigning different models per phase, but **only in OpenCode**.

#### 8.3.1 OpenCode SDD Profiles (real automatic routing)

This is the only thing gentle-ai truly automates. If your team uses OpenCode:

```bash
# Create a "cheap" profile for experimentation: economical model in general,
# but a more capable model specifically for the design phase
gentle-ai sync --profile cheap:openrouter/qwen/qwen3-30b-a3b:free
gentle-ai sync --profile-phase cheap:sdd-design:anthropic/claude-sonnet-4-20250514
```

You can also create via TUI: `gentle-ai` → "OpenCode SDD Profiles" → Create.

**How it works once created**:
- The base SDD conductor is `gentle-orchestrator` (correct name since the migration from `sdd-orchestrator`, applied automatically if you come from an old version).
- Each named profile generates `sdd-orchestrator-{name}` plus sub-agents with the corresponding suffix, each pointing to the model you chose.
- In OpenCode, press **Tab** to switch between `gentle-orchestrator` (default) and your custom profiles.
- You can have multiple profiles at once (e.g., "cheap" for exploring, "premium" for production) and switch freely.

Full official guide: `github.com/Gentleman-Programming/gentle-ai/blob/main/docs/opencode-profiles.md`.

#### 8.3.2 Manual recommendation per phase (for all other agents)

For Claude Code, Cursor, Windsurf, Kiro, Copilot, Gemini CLI, Antigravity CLI, Codex, and any other agent supported by the wizard: SDD runs in single-mode, one model handles all phases automatically. If you want to vary the model per phase, you do it **manually**, changing the model in your IDE/CLI before invoking each phase. Here is the guide on what to choose:

| SDD Phase | What it requires | Recommended model | Why |
|---|---|---|---|---|
| Explore | Read and understand existing code, without generating much new output | Fast/economical model (e.g., Haiku) | It's reading and synthesis work, not deep reasoning. Saves cost without perceptible quality loss |
| Propose | Draft the "what" of the change, scope decisions | Intermediate model (e.g., Sonnet) | Needs good judgment but not maximum reasoning — it's a proposal, not final architecture |
| Spec | Detailed acceptance criteria | Intermediate model (e.g., Sonnet) | Precision and thoroughness matter more than creativity |
| Design | Architecture, technical decisions on how to solve it | Most capable model available (e.g., Opus, if your organization has it approved) | This is the phase where a design error is most expensive to fix later. Worth the strongest model here |
| Implement | Write code following the already approved design | Intermediate model (e.g., Sonnet) | Design already solved the hard decisions; implementing is disciplined execution, not exploration |
| Verify | Review that code meets the spec, run tests | Intermediate model (e.g., Sonnet) | Rigorous review, doesn't require top capability if the spec is already clear |

> **Note for Improving**: the organization-approved models are Claude Sonnet and Claude Haiku — Opus, Fable, and Mythos are not approved for use in this stack. Applying the table above within that limit: use Haiku for Explore, and Sonnet for everything else (Propose, Spec, Design, Implement, Verify). If any project needs additional capacity for Design, the correct path is to request an exception from Global IT Services, not to change the model on your own.

**How to apply this in practice** (no automation, it's manual):
1. Before running `sdd-propose`, `sdd-explore`, etc., change the active model in your IDE/CLI to the one recommended for that phase.
2. Run the phase.
3. Switch back before the next phase if applicable.

This is real friction compared to OpenCode, but it's the current reality of gentle-ai outside that agent. If your team adopts OpenCode in the future, 8.3.1 applies directly.

> **Codex CLI**: treats skills as passive reference context — it can ignore Decision Ladder gates, Preflight, TDD Proposal even after reading them. Workaround: add the protocol instructions at the end of the prompt (`--prompt "..."` or paste in UI) instead of relying on it reading from `AGENTS.md` or `.agents/`. The wizard documents this but doesn't automate it because the limitation is on the client side, not the config.

### 8.4 Worktrees — `/wf-worktree` (built in this block)

gentle-ai does not manage worktrees. The only thing it does is the "Incident rule" from 8.2: if it detects something went wrong with a worktree, it requires an audit before continuing — but it doesn't create, list, or clean worktrees for you. That's why the worktree wizard exists: `/wf-worktree` is a project-specific slash command generated in Phase 6.

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

The mapping of natural language phrases to the four operations (`new`, `list`, `clean`, `parallel`) lives **inside `wf-worktree.md`**, as internal instructions of the file itself — it is not added to `AGENTS.md`. This maintains the convention already established in Block 3 with `wf-ladder` and `wf-sdd-lite`: those commands also live as standalone files briefly referenced from `AGENTS.md`, not duplicated there. Putting the full mapping in `AGENTS.md` inflates its target size (150-200 lines, see Appendix D) unnecessarily — `AGENTS.md` is a lightweight index, not the source of truth for every feature.

The command stub in `AGENTS.md` (or in the IDE's commands directory) simply indicates: "if the user asks for something equivalent to create/list/clean/merge worktrees in parallel in natural language, follow the instructions in `wf-worktree.md`". The file itself contains the example phrases and decision logic.

#### 8.4.8 Installation as command (same pattern as Block 3)

Same as `wf-ladder`, `wf-sdd-lite`, `wf-onboard`, and `wf-refresh`, `/wf-worktree` is generated in Phase 6 of `wf-init` (or added via `/wf-refresh` if the project is already initialized) for each active IDE, with the same path table and formats from section 7.5:

| IDE | Path | Format |
|---|---|---|
| Claude Code | `.claude/commands/wf-worktree.md` | Plain markdown, no frontmatter |
| Cursor | `.cursor/commands/wf-worktree.md` | Plain markdown, no frontmatter |
| Windsurf | `.windsurf/workflows/wf-worktree.md` | Frontmatter with `description:` required |
| Kiro | `.kiro/steering/wf-worktree.md` | Frontmatter with `inclusion: manual` |
| OpenCode | `.opencode/commands/wf-worktree.md` | Plain markdown, no frontmatter |
| Copilot | `.github/prompts/wf-worktree.prompt.md` | Suffix `.prompt.md` + frontmatter `mode: agent` |

It is a **project-specific** command (like `wf-ladder` and `wf-sdd-lite`), not global — depends on the repo you're in, although its internal logic is generic.

The complete `wf-worktree.md` file is already built as a standalone file (same format as `wf-onboard.md`): three operations (`new`, `list`, `clean`), free port detection per worktree, internal natural language mapping, and inviolable rules to never push or delete without explicit confirmation. It is included in the `EXPECTED_COMMANDS` and in the per-IDE command generation — a project running `/wf-init` from scratch receives it right away, and one already initialized receives it via `/wf-refresh` (Phase 3.5, check for missing commands).

---

## 9. Block 5 · TDD pro + Playwright integrated

### 9.1 Strict TDD Mode — what it is and how it works

Strict TDD Mode is a working mode (managed by gentle-ai) where the agent CANNOT skip TDD — no skip option, with mandatory raw output evidence. Unlike the standard TDD Protocol (where the agent proposes and you decide whether to apply, apply partial, or skip), Strict TDD has no "escape".

The actual Strict TDD behavior is resolved by this precedence (confirmed against the gentle-ai source SKILL.md):
1. Engram: `mem_search("sdd/{project}/testing-capabilities")`
2. `openspec/config.yaml → strict_tdd`
3. Fallback: project file detection

`wf-init` writes `strict_tdd` directly to Engram ALWAYS, and additionally to `openspec/config.yaml` if the backend includes it. In Claude Code or Windsurf it also runs `gentle-ai sync --strict-tdd` as a complementary signal for the orchestrator. There is no `--no-strict-tdd` — the field is reverted by simply changing `true` to `false`, which is what `/wf-settings` automates.

### 9.2 Architecture of three independent pieces

The final design separates three decisions that are orthogonal to each other — activating one does not affect the others:

```
┌─────────────────────────────┐   ┌──────────────────────────────┐   ┌─────────────────────────┐
│ 1. TDD Mode                  │   │ 2. Playwright Dual-loop       │   │ 3. Optional Extras       │
│    (exclusive choice)        │   │    (independent of mode)     │   │    (each separate)       │
│                               │   │                                │   │                          │
│  • Standard TDD Protocol      │   │  Applies equally with         │   │  • Coverage targets      │
│    (own content, already      │   │  standard TDD or Strict —     │   │  • Visual regression     │
│    tested)                    │   │  answers a different          │   │  • Page Object Model     │
│  • Strict TDD Mode            │   │  question: "how do I build    │   │                          │
│    (real field in openspec/    │   │  the E2E spec?", not "can    │   │  None activate without   │
│    config.yaml, confirmed     │   │  I skip the test?"            │   │  being asked             │
│    against source skill)      │   │                                │   │                          │
└─────────────────────────────┘   └──────────────────────────────┘   └─────────────────────────┘
```

### 9.3 TDD Mode — how it is asked and what changes

In Phase 4.6 of `wf-init.md`, immediately after choosing testing layers (unit/integration/e2e), the wizard asks:

```
What TDD mode do you want for this project?

1. Standard TDD Protocol (recommended)
   Own content of this workflow, already tested in real use. The agent
   proposes which layers apply and LETS YOU CHOOSE: apply, apply partial,
   or skip TDD if you decide it's not warranted.

2. Strict TDD Mode (managed by gentle-ai, not by this wizard)
   No skip option, with mandatory raw output evidence. This
   wizard does NOT write the content — runs `gentle-ai install --strict-tdd`
   and gentle-ai writes its own section in your AGENTS.md/CLAUDE.md. The
   exact content of that section is neither controlled nor verified by this
   workflow line by line.

Which do you prefer? [1 / 2]
```

**If option 1 is chosen**: `wf-init` writes the TDD Protocol documented in the file itself — 100% our content, unchanged from what was already tested.

**If option 2 is chosen**: `wf-init` writes no TDD Protocol text. Runs `gentle-ai install --strict-tdd` and informs the user to review the section gentle-ai added to their `AGENTS.md`/`CLAUDE.md` as the real source of truth, instead of assuming it matches this workflow's documentation.

The response is saved in `openspec/config.yaml` (`testing.strict_tdd: true/false`) only as an informational record of which mode was activated — that field does not control behavior, because in the Strict TDD case the real behavior lives in what gentle-ai wrote, not in this config file.

Neither mode forces tests where the coverage matrix already says they don't apply (for example, "UI/pure styles") — but that guarantee is verifiable in standard mode (it's our text) and not verified by this workflow in Strict TDD (depends on how gentle-ai implemented it in its current version).

### 9.4 Playwright dual-loop — when to explore before versioning

The pattern consists of two different loops for the same tool:

- **Loop 1 — exploration (Playwright MCP, no new files)**: the agent controls a real browser interactively — navigates, clicks, captures screenshots — to visually confirm that a flow behaves as expected, before committing to write a spec.
- **Loop 2 — versioning (`@playwright/test`, real spec in `e2e/`)**: once confirmed, the agent writes the spec that gets committed and runs in any future pipeline, without needing the interactive browser.

**It is not a mandatory step in all cases** — forcing visual exploration before every spec, even in trivial and well-known flows, would be unnecessary ceremony, contrary to gentle-ai's own principle of "small request, no ceremony". The agent evaluates:

- **Explore first if**: the flow has multiple visual states, transitions or animations; it's the first time that interaction is tested; or the user explicitly asks for it.
- **Go direct to spec if**: it's a simple known CRUD (create → appears in list, edit → updates) without complex visual states, or a similar template spec already exists.

This criterion lives as its own subsection within the TDD Protocol in `AGENTS.md` (see `wf-init.md`, "Playwright Dual-loop" section), applying equally regardless of whether the project uses Standard TDD Protocol or Strict TDD Mode.

### 9.5 `data-testid` convention — mandatory when E2E is present

When the project activates the E2E layer in Phase 4.6, `wf-init.md` adds to the Testing Approach section of `AGENTS.md` the requirement that every interactive element (buttons, inputs, links) receives its own `data-testid` **at component creation time**, not later when a test needs it. Format: `data-testid="<context>-<element>"` in kebab-case. The practical reason: without this, E2E specs depend on visible text or Tailwind classes, both fragile against copy or style changes that have nothing to do with the behavior the test is trying to verify.

### 9.6 Optional extras — coverage targets, visual regression, Page Object Model

All three are always asked in Phase 4.6, after TDD mode, and **none activate without the user explicitly requesting it** — each has a real cost that isn't justified in every project:

| Extra | What it does | Real cost | When it's worth it |
|---|---|---|---|---|
| Coverage targets | Minimum coverage threshold; fails `npm run test -- --coverage` if not met | Nearly zero — one config line in `vitest.config.ts` | Almost always — cheap and provides an objective quality signal |
| Visual regression (snapshots) | Compares screenshots against a saved reference | Real and ongoing — each run is slower, and references need manual re-generation when design intentionally changes | Projects with stable UI where an accidental visual change would be costly |
| Page Object Model | Organizes Playwright selectors into reusable classes | None at runtime, but it's an abstraction layer | Projects with multiple E2E specs — for 2-3 flows it's over-engineering, same logic the workflow's Decision Ladder already applies |

Integration with CI/CD (so the coverage threshold also blocks the pipeline, not just the local run) is pending until Block 6 exists — today the gate can only apply locally.

### 9.7 Strategy for legacy projects without tests

Unchanged from the original criteria: no mass retrofitting of tests onto legacy code without coverage. Testing entry is organic — new feature comes with its new tests, bug fix comes with a regression test that first reproduces the bug and then confirms the fix, and the suite grows with the team's real work instead of a dedicated "let's cover all the legacy this sprint" effort.

### 9.8 `/wf-settings` — toggle optional modules after installation

Once `/wf-init` has run, several decisions the developer made (TDD mode, testing extras, Decision Ladder, SDD backend) are fixed in the project — but they are not immutable, and it shouldn't require editing files by hand or re-running full `wf-init` to change them. `/wf-settings` (new standalone file, same format as `wf-onboard.md` and `wf-worktree.md`) closes that gap.

**The four things it manages**:

| Module | What it toggles | Risk when changing |
|---|---|---|
| TDD Mode | Standard ↔ Strict TDD Mode | None — both coexist in `openspec/config.yaml`, changing is instant |
| Testing extras | Coverage targets / Visual regression / Page Object Model, each independent | Low — only config, although deactivating visual regression or POM doesn't automatically rewrite existing specs |
| Decision Ladder | Included or not in `AGENTS.md` | Real — it's an anti-over-engineering safeguard, removing it requires additional explicit confirmation |
| SDD persistence backend | engram ↔ openspec ↔ hybrid | Variable — migrating *to* hybrid is safe (only adds), migrating *from* hybrid implies real functionality loss and requires double confirmation |

**Interaction pattern**: the command always shows the real state first (reading `openspec/config.yaml` and `AGENTS.md` directly, never assuming what the developer remembers choosing), lets you choose one or several changes, applies and confirms each individually, and asks "anything else?" before closing with a consolidated commit — without `git push`, like the rest of this workflow.

**Why it's project-specific and not global**: just like `/wf-worktree`, its behavior depends entirely on the real state of the active repo (which backend, which extras are on) — it doesn't make sense as a global command installed once for all projects.

`wf-init.md` and `wf-refresh.md` already include `wf-settings` in their `EXPECTED_COMMANDS`, so it is auto-generated in new projects and offered to add in existing projects that don't have it.

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

The **AI Review** has three possible providers:
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
the artifacts in Phase 6e. If you already initialized the project and want to change something,
use `/wf-settings` (CI options, AI Reviewer, Security Review, CD, etc.) or
`/wf-cicd` for complete block re-configuration.

---

## 11. Block 7 · Bootstrap automation (slash commands)

> The workflow is distributed as a product via `install.sh` — one line to install global slash commands on all detected IDEs.

### install.sh

```bash
curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/install.sh | bash
```

- Detects IDEs by directories in `~/` (Claude, Cursor, Windsurf, Kiro, Codex, Copilot, Antigravity)
- Installs `/wf-init` and `/wf-refresh` as self-contained slash commands
- Applies correct format per IDE (frontmatter for Windsurf/Kiro/Copilot, SKILL.md for Antigravity)
- Supports `--uninstall` to remove only the installed commands

### Global vs project-specific commands

| Type | Commands | Installation |
|---|---|---|
| **Global** | `/wf-init`, `/wf-refresh` | `install.sh` → `~/.<ide>/commands/` |
| **Project-specific** | `/wf-onboard`, `/wf-settings`, `/wf-worktree`, `/wf-cicd` | `/wf-init` Phase 6 → repo |
| **Global** | `/wf-cleanup` | `install.sh` → `~/.<ide>/commands/` |
| **Project-specific** | `/wf-ladder`, `/wf-sdd-lite` | `/wf-init` Phase 6 → repo |

### What the block includes

- Self-contained commands: all `_base.md` files have inline content.
- `wf-init/_base.md` (C2): template that fetches phase files from GitHub via curl.
- Builder B7: generates for all IDEs including `.codex/commands/`.
- Unified naming: "AI Workflow Wizard" in all active files.
- Command `/wf-cleanup` to uninstall the wizard from a project without touching gentle-ai.

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
| `~/.claude/` | Persona, SDD sub-agents, skills, MCP wiring |
| `~/.cursor/agents/sdd-*.md` | 10 sub-agents for Cursor |
| `~/.windsurf/` | Persona, MCP, skills (Plan Mode integration) |
| `~/.kiro/steering/gentle-ai.md` | Kiro global steering |
| `~/.kiro/agents/sdd-*.md` | 10 sub-agents for Kiro |
| `~/.config/opencode/` | Plugins, SDD profiles, MCP |
| `~/.codex/` | Per-phase model+effort configs |
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

**What already happened and what could happen again**: the base SDD conductor was renamed from `sdd-orchestrator` to `gentle-orchestrator` between versions (with automatic migration on `sync`). It is a real example of how an internal naming change can affect any part of this workflow that hardcodes command names, sub-agents, or gentle-ai paths — and this workflow does so in several places (`wf-init.md`, `wf-refresh.md`, section 8.3 of this document).

**Current mitigation (no new tool required)**:
- **Periodic manual monitoring**: check `github.com/Gentleman-Programming/gentle-ai/releases` before recommending the wizard in a new project, or when the wizard fails unexpectedly. No cron or constant monitoring needed — the natural cadence is "I check when I'm going to use it or when something breaks".
- **Semi-automatic detection in the wizard**: Step 0.3.1 analyzes the text of gentle-ai release notes looking for risk signals near terms this workflow hardcodes, informs the developer on the spot, and leaves a draft ready to report it as an issue in this workflow's repo (see Block 4, section 8 and wf-init.md Step 0.3.1 for full detail). This does not replace manual monitoring — it complements it by detecting in situ what a real developer encounters in production.

**What happens if gentle-ai stops being maintained or breaks compatibility severely**: Engram and OpenSpec (the actual backends behind persistent memory and SDD) are separate projects from gentle-ai — gentle-ai orchestrates them but does not replace them. An abandonment of gentle-ai would mainly affect the multi-IDE configuration layer and native sub-agents, not necessarily the memory or SDD themselves, which could continue to be used more manually. There is no detailed migration plan yet because it hasn't been necessary — it will be documented if the situation arises.

---

## Known Issues

### Antigravity IDE — gentle-ai does not install SDD skills in the correct path

gentle-ai writes SDD skills to `~/.gemini/antigravity-cli/skills/` (correct path for the **CLI**), but **IDE 2.0** expects global skills at `~/.gemini/config/skills/`. As a result, the agent reads the SDD orchestrator from `GEMINI.md` and tries to run phases, but without actual skill files, it simulates phases inline without persisting artifacts to Engram/openspec.

**Bug reference**: [gentle-ai issue #746](https://github.com/Gentleman-Programming/gentle-ai/issues/746) — "Feat: Add support for Antigravity 2.0 target directory"

**Manual workaround** (until gentle-ai fixes it):

```bash
cp -r ~/.gemini/antigravity-cli/skills ~/.gemini/config/skills
```

This copies the 22 SDD skills (`sdd-apply`, `sdd-propose`, etc.) to the path the IDE recognizes. It does not affect the CLI installation.

**Valid for**: gentle-ai v1.43.3 and earlier. When issue #746 is resolved, this workaround will no longer be necessary.

---


