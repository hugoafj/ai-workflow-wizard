# AI Workflow Wizard

Sets up a complete AI development workflow in any repo: context layers, testing, CI/CD, and feature tracking with Organic Driven Development (ODD). One command installs everything; the wizard adapts to your stack and IDE automatically.

> **Note:** SDD (spec-driven development, OpenSpec) was removed in favor of ODD, which gentle-ai v4 runs natively. ODD sizes its work by evidence instead of file counts, keeps one feature document per change in `odd/tasks/`, and runs test-first by default. Projects set up by an older version migrate on their next `/wf-refresh`.

## Install

**One time in your terminal:**

```bash
curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/install.sh | bash
```

This installs global slash commands (`/wf-init`, `/wf-refresh`, `/wf-cleanup`) that work in any IDE. Supports: Claude Code, Cursor, Windsurf, Kiro, Codex, Copilot, Antigravity, OpenCode.

## Quick Start

**Inside your project (legacy or greenfield with git + stack initialized):**

In your IDE or CLI agent, run:

```bash
/wf-init    # Or just say "run wf-init" to your agent
```

> **IMPORTANT**: This wizard requires [gentle-ai](https://github.com/Gentleman-Programming/gentle-ai), the foundation ecosystem that powers ODD, Engram (persistent memory), skills, and multi-IDE routing. If gentle-ai is not installed, the wizard will guide you through installation automatically. **Before running `/wf-init`, take 5 minutes to read the [gentle-ai documentation](https://github.com/Gentleman-Programming/gentle-ai#readme)**. Understanding how gentle-ai works is essential to getting the most out of this workflow. Skipping this step means missing critical features like the ODD workflow and persistent memory between sessions.

> **⚠️ WARNING: Use capable models**: The wizard is instruction-driven: agents must follow multi-step procedures exactly. **Fast or small models (Haiku-class or equivalent) are, by nature, prone to skipping instructions and steps**. They do not follow procedural prompts reliably. This is worse on **VS Code / GitHub Copilot**, where the harness hides context and the model cuts corners. Use a **Sonnet-class or better** model to run `/wf-init` (wizard initialization). **This warning applies to the wizard bootstrap only. For day-to-day development, feature work, and anything else in the initialized repo, any model works fine.** See [Known Issues & Workarounds](#copilot--vs-code-use-capable-models) below.

The wizard discovers your stack, installs [gentle-ai](https://github.com/Gentleman-Programming/gentle-ai) (the foundation ecosystem), generates `AGENTS.md`, configures satellites per IDE, sets up git hooks, and prepares CI/CD templates.

## Protecting Custom Content

If you add team-specific rules, policies, or custom configurations to `AGENTS.md`, wrap them with markers so the wizard never overwrites them:

```markdown
<!-- WF: DO NOT REGENERATE -->
## Our Team Rules

- Code review: 2 approvals minimum
- Release window: Tuesdays only
- Documentation: Always in English
<!-- /WF: DO NOT REGENERATE -->
```

When you run `/wf-refresh`, the wizard will update everything EXCEPT these marked sections. Your customizations are preserved forever.

**Why this matters**: Your team's policies, constraints, and decisions are yours to maintain. The wizard adapts around them, never replaces them.

## Known Issues & Workarounds

### Copilot / VS Code: Use Capable Models

The wizard's phases are procedural instructions: each one expects the agent to execute every step in order and persist state exactly. **Fast or small models (Haiku-class or equivalent) skip instructions by nature** — they cut steps, invent state fields, and do not reliably follow long procedure chains. This is amplified on GitHub Copilot / VS Code, whose progressive skill disclosure only loads instructions when the model decides they are relevant.

- **The issue**: fast/small models do not follow multi-step instructions reliably; the problem compounds on Copilot / VS Code harnesses that hide context.
- **The fix**: use a **Sonnet-class or better** model only to run `/wf-init` (wizard initialization). If a capable model is unavailable, expect to review every phase step manually — the wizard cannot compensate for a model that ignores its instructions.
- **Scope**: this applies to the wizard bootstrap **only**, once the repo is initialized, day-to-day development, feature work, and anything else work with any model, including fast/small ones.
- **What works**: OpenCode and Claude Code expose full context and respect tool/agent boundaries; Copilot's harness is the least reliable for instruction-driven workflows, regardless of model.

### Windsurf / Devin: Legacy Path Bridge

If you use **Windsurf** or **Devin**, the wizard adds a compatibility rule to `AGENTS.md`:

- **The issue**: gentle-ai installs its skills into Windsurf's legacy paths (`~/.codeium/windsurf/skills/`), but Windsurf doesn't scan them natively. Without a bridge rule in `AGENTS.md`, the agent can't find those skills.
- **The fix**: the bridge rule tells your agent where to look.
- **When it applies**: during `/wf-init`, automatically, if Windsurf is detected as an active IDE. The wizard re-applies it in Phase 8.
- **If it needs reapplying**: run `/wf-refresh`. It reinserts the rule, which `gentle-ai sync` may remove.

No user action needed; the wizard handles it.

## Updating Global Commands

If you install new IDEs or want to update to a newer wizard version:

```bash
curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/install.sh | bash
```

This updates `/wf-init`, `/wf-refresh`, and `/wf-cleanup` globally, and installs them in any new IDEs detected on your machine.

## What You Get

After `/wf-init`, your repo has:

- **`AGENTS.md`** — project-specific context that tells AI agents how this repo works ([learn more](AI_DEV_WORKFLOW.md#51-understanding-agentsmd))
- **IDE satellites** — auto-generated files in `.cursor/rules/`, `.windsurf/rules/`, `.kiro/steering/`, `CLAUDE.md`, etc. that point to `AGENTS.md` ([learn more](AI_DEV_WORKFLOW.md#54-project-specific-satellites-what-they-are-and-why-we-need-them))
- **Post-commit hook** — detects when `AGENTS.md` drifts out of sync with the codebase
- **Wizard state** — `.wizard-state.json` and `.wizard-managed-files.json`, committed so your teammates never need to re-run `/wf-init`
- **CI/CD templates** — GitHub Actions with quality guard, AI review, and release-please ([learn more](AI_DEV_WORKFLOW.md#10-block-6--cicd-pipeline--gga))
- **Project-specific slash commands**: `/wf-onboard`, `/wf-settings`, `/wf-worktree` (plus `/wf-ladder` when the Decision Ladder is enabled). Every command is also packaged as a skill (1:1), so it can be invoked by natural language too.

## The Day-to-Day

Once set up, here's what working with the AI Workflow looks like:

1. **Request features in natural language** — no slash commands to learn. Just tell the agent what you want.
2. **ODD tracks substantial work**: for substantial, authorized changes the agent creates one feature document (`odd/tasks/<feature>.md`) with specs, tasks, and a log, and mirrors it to Engram. Small changes stay lightweight. ([learn more](AI_DEV_WORKFLOW.md#6-block-2--feature-tracking-odd))
3. **Test-first by default**: when a relevant runnable test exists, the agent writes it first, watches it fail, then implements until it passes. ([learn more](AI_DEV_WORKFLOW.md#9-block-5--testing-test-first-and-playwright))
4. **Sub-agents work in parallel**: when a task is large enough to delegate, each sub-agent runs with fresh context. ([learn more](AI_DEV_WORKFLOW.md#82-sub-agents-and-delegation-native-to-gentle-ai))
5. **Human review before every commit** — the agent shows you the full diff and waits for approval.
6. **AI code review on PRs** — GGA (Gentleman Guardian Angel) reviews diffs applying your project standards. Provider-agnostic: works with Claude, Gemini, Codex, Ollama. ([learn more](AI_DEV_WORKFLOW.md#10-block-6--cicd-pipeline--gga))
7. **Security scanning** — automated security review on every PR as part of the CI pipeline.
8. **Conventional commits + auto-release** — commits follow the `feat:`, `fix:`, `chore:` convention. release-please prepares changelogs and releases automatically.
9. **Drift detection** — the post-commit hook warns when `AGENTS.md` needs an update. Run `/wf-refresh` to fix it.

## Working in a Team

Only one person runs `/wf-init`. Everything it generates, including the wizard state, is committed, so nobody else spends tokens re-initializing the project.

1. **The maintainer** runs `/wf-init`, reviews the diff, and pushes the commit.
2. **Every teammate** clones the repo and runs `/wf-onboard` once. It prepares *their* machine and never touches the repo: it installs the global commands (`/wf-init`, `/wf-refresh`, `/wf-cleanup`) and gentle-ai if missing, installs dependencies (which also activates Husky), recreates the post-commit hook when the project doesn't use Husky, and walks through the project's MCPs.
3. **Anyone** can then run `/wf-refresh` or `/wf-cleanup`, because the state travels with the repo. If someone runs `/wf-init` in an already initialized repo, it says so and points to `/wf-onboard` or `/wf-refresh`.

Repos initialized by an older wizard kept the state local. Ask the maintainer to run `/wf-refresh` once and commit; it asks before removing the old `.gitignore` entries and then versions the state.

## Commands

| Command | Scope | Description |
|---------|-------|-------------|
| `/wf-init` | Global | Bootstrap wizard — initializes the workflow in a project |
| `/wf-refresh` | Global | Re-runs the Builder (B1–B9) to regenerate all managed artifacts when the project evolves ([learn more](AI_DEV_WORKFLOW.md#55-context-auto-update)) |
| `/wf-cleanup` | Global | Removes wizard artifacts from a project |
| `/wf-onboard` | Project | Sets up a teammate's machine after cloning: global commands, gentle-ai, dependencies, git hooks, MCPs |
| `/wf-settings` | Project | Toggle optional modules: testing, testing extras, Decision Ladder, CI/CD ([learn more](AI_DEV_WORKFLOW.md#96-wf-settings-toggle-optional-modules-after-installation)) |
| `/wf-worktree` | Project | Git worktree management with automatic port assignment ([learn more](AI_DEV_WORKFLOW.md#84-worktrees--wf-worktree-built-in-this-block)) |
| `/wf-ladder` | Project (optional) | Decision Ladder: avoids over-engineering before implementing ([learn more](AI_DEV_WORKFLOW.md#58-optional-behavior-improvements--wf-ladder)) |

> Every command is also packaged as a SKILL.md (1:1): project ones by the Builder (native
> per IDE + `.agents/skills/` universal + flat fallback), global ones by `install.sh`.

> CI/CD re-configuration lives in `/wf-settings` (options 6–13: CI/CD and release strategy), sourced from the `cicd`
> protocol (`templates/protocols/cicd/_base.md`).

## When to Use /wf-cleanup + /wf-init Instead of /wf-refresh

In most cases, `/wf-refresh` handles updates gracefully. But if any of these apply, a clean reinstall is safer:

- **Disruptive release** — Many files changed simultaneously (5+ regenerations)
- **Deleted files** — `.wizard-managed-files.json` shows files were removed and you're unsure which
- **Corrupted state** — File integrity check fails (content hash mismatch)
- **Multiple releases behind** — Jumping 3+ versions risks orphaned files
- **Broken .wizard-state.json** — State is missing or incomplete

**Recovery path:**
```bash
/wf-cleanup    # Removes wizard artifacts (safe — preserves your code)
/wf-init       # Fresh install with current stack and state
```

`/wf-cleanup` is designed to be completely safe: it removes only wizard-generated files and asks for confirmation before each deletion. Your project code, team policies (marked with `<!-- WF: DO NOT REGENERATE -->`), and gentle-ai installations are always preserved.

See [WF_REFRESH_TROUBLESHOOTING.md](WF_REFRESH_TROUBLESHOOTING.md) for detailed decision tree and troubleshooting.

## Optional Modules

Enable via `/wf-settings` after initial setup:

- **Testing**: unit, integration, and E2E layers, with test-first development by default ([learn more](AI_DEV_WORKFLOW.md#9-block-5--testing-test-first-and-playwright))
- **wf-ladder (Decision Ladder)** — structured decision-making protocol for complex architectural choices ([learn more](AI_DEV_WORKFLOW.md#58-optional-behavior-improvements--wf-ladder))
- **CI/CD extras** — GGA review, security scanning, AI summary jobs ([learn more](AI_DEV_WORKFLOW.md#10-block-6--cicd-pipeline--gga))

## Architecture

Two layers that complement each other:

- **Foundation Layer** ([gentle-ai](https://github.com/Gentleman-Programming/gentle-ai)) is the global ecosystem: Engram (persistent memory), the ODD workflow, skills, MCPs, persona, permissions. Installed once, serves all projects.
- **Custom Layer** (this wizard) — project-specific: `AGENTS.md`, satellites, hooks, CI/CD. Lives in your repo.

They write to different locations and coexist without conflict. ([full architecture details](AI_DEV_WORKFLOW.md#2-the-architecture-two-layers))

## Documentation

This README is a quick reference. The full workflow documentation lives in [AI_DEV_WORKFLOW.md](AI_DEV_WORKFLOW.md) — start there if you want to understand the philosophy, architecture, and all 7 blocks in depth.

## License

MIT
