# AI Workflow Wizard

Sets up a complete AI development workflow in any repo — context layers, testing, CI/CD, and spec-driven development. One command installs everything; the wizard adapts to your stack and IDE automatically.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/install.sh | bash
```

Detects your IDE and installs global slash commands. Supports: Claude Code, Cursor, Windsurf, Kiro, Codex, Copilot, Antigravity, OpenCode.

## Quick Start

```bash
/wf-init    # Run once per repo — sets up everything
```

That's it. The wizard discovers your stack, installs [gentle-ai](https://github.com/hugoafj/ai-workflow-wizard) (the foundation ecosystem), generates `AGENTS.md`, configures satellites per IDE, sets up git hooks, and prepares CI/CD templates.

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
- **CI/CD templates** — GitHub Actions with quality guard, AI review, and release-please ([learn more](AI_DEV_WORKFLOW.md#10-block-6--cicd-pipeline--gga))
- **Project-specific slash commands** — `/wf-onboard`, `/wf-settings`, `/wf-worktree`, `/wf-cicd`

## The Day-to-Day

Once set up, here's what working with the AI Workflow looks like:

1. **Request features in natural language** — no slash commands to learn. Just tell the agent what you want.
2. **SDD kicks in automatically** — for non-trivial tasks, the agent runs Spec-Driven Development: proposal → specs → design → tasks → implementation. You approve at each gate. ([learn more](AI_DEV_WORKFLOW.md#6-block-2--specification-layer-sdd))
3. **Test-first by default** — when TDD is enabled, the agent writes the test first, you approve it, then implements until it passes. Strict mode enforces this for every change. ([learn more](AI_DEV_WORKFLOW.md#9-block-5--tdd-pro--playwright-integrated))
4. **Sub-agents work in parallel** — each SDD phase runs on the optimal model with fresh context. ([learn more](AI_DEV_WORKFLOW.md#82-sub-agents-and-delegation-native-to-gentle-ai))
5. **Human review before every commit** — the agent shows you the full diff and waits for approval.
6. **AI code review on PRs** — GGA (Gentleman Guardian Angel) reviews diffs applying your project standards. Provider-agnostic: works with Claude, Gemini, Codex, Ollama. ([learn more](AI_DEV_WORKFLOW.md#10-block-6--cicd-pipeline--gga))
7. **Security scanning** — automated security review on every PR as part of the CI pipeline.
8. **Conventional commits + auto-release** — commits follow the `feat:`, `fix:`, `chore:` convention. release-please prepares changelogs and releases automatically.
9. **Drift detection** — the post-commit hook warns when `AGENTS.md` needs an update. Run `/wf-refresh` to fix it.

## Commands

| Command | Scope | Description |
|---------|-------|-------------|
| `/wf-init` | Global | Bootstrap wizard — initializes the workflow in a project |
| `/wf-refresh` | Global | Updates `AGENTS.md` when the project evolves ([learn more](AI_DEV_WORKFLOW.md#55-context-auto-update)) |
| `/wf-cleanup` | Global | Removes wizard artifacts from a project |
| `/wf-onboard` | Project | Onboarding guide for new developers |
| `/wf-settings` | Project | Toggle optional modules: TDD, testing extras, Decision Ladder ([learn more](AI_DEV_WORKFLOW.md#98-wf-settings--toggle-optional-modules-after-installation)) |
| `/wf-worktree` | Project | Git worktree management with automatic port assignment ([learn more](AI_DEV_WORKFLOW.md#84-worktrees--wf-worktree-built-in-this-block)) |
| `/wf-cicd` | Project | CI/CD pipeline configuration ([learn more](AI_DEV_WORKFLOW.md#10-block-6--cicd-pipeline--gga)) |

## Optional Modules

Enable via `/wf-settings` after initial setup:

- **TDD** — test-first development with strict or standard mode ([learn more](AI_DEV_WORKFLOW.md#9-block-5--tdd-pro--playwright-integrated))
- **Decision Ladder** — structured decision-making protocol for complex architectural choices ([learn more](AI_DEV_WORKFLOW.md#58-optional-behavior-improvements--decision-ladder))
- **CI/CD extras** — GGA review, security scanning, AI summary jobs ([learn more](AI_DEV_WORKFLOW.md#10-block-6--cicd-pipeline--gga))

## Architecture

Two layers that complement each other:

- **Foundation Layer** ([gentle-ai](https://github.com/hugoafj/ai-workflow-wizard)) — global ecosystem: Engram (persistent memory), SDD orchestrator, skills, MCPs, persona, permissions. Installed once, serves all projects.
- **Custom Layer** (this wizard) — project-specific: `AGENTS.md`, satellites, hooks, CI/CD. Lives in your repo.

They write to different locations and coexist without conflict. ([full architecture details](AI_DEV_WORKFLOW.md#2-the-architecture-two-layers))

## Documentation

This README is a quick reference. The full workflow documentation lives in [AI_DEV_WORKFLOW.md](AI_DEV_WORKFLOW.md) — start there if you want to understand the philosophy, architecture, and all 7 blocks in depth.

## License

MIT
