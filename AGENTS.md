# AGENTS.md — workflow-wizard

## Commands

| Command | Path |
|---|---|
| `/wf-refresh` | `.claude/commands/wf-refresh.md` / `.github/prompts/wf-refresh.prompt.md` |
| `/wf-worktree` | `.claude/commands/wf-worktree.md` |
| `/wf-settings` | `.claude/commands/wf-settings.md` |
| `/wf-onboard` | `.claude/commands/wf-onboard.md` |
| `/wf-cleanup` | `.claude/commands/wf-cleanup.md` / `.github/prompts/wf-cleanup.prompt.md` |
| `/wf-cicd` | `.claude/commands/wf-cicd.md` / `.github/prompts/wf-cicd.prompt.md` |

## Code Style & Conventions

- **Language**: English (all wizard content)
- **Naming**: kebab-case for markdown files (wf-init, phase0, wf-refresh)
- **Format**: plain .md files, sequential numbering for phases

## Project Structure

```
.github/          — CI/CD workflows, copilot instructions
templates/        — single source of truth
  AGENTS.router.md
  commands/       — _base.md for each command
  protocols/      — packable protocols
  satellites/     — per-IDE context files
wf-init/          — wizard phases
  lib/            — builder.md, state.md (contracts)
  phase*.md       — phases 0 through 8
```

## Critical Constraints

- No production code (markdown/templates project of the workflow wizard)
- No push — the user decides when
- Mandatory human review gate before every commit

## Programmatic Checks

`lint + build`

## Project MCPs

| MCP | Active |
|---|---|
| Engram | automatic (gentle-ai) |
| Context7 | automatic (gentle-ai) |

## Behavior Preferences

- Review gate before commit: show me the full diff and wait for my approval before committing.
- No opportunistic refactoring: stick to the new pattern only in new code.
- If you detect that the code contradicts something in this AGENTS.md, report it at the end of
  your response with the tag `[AGENTS.md drift detected: <description>]`. Do NOT fix AGENTS.md yourself.

## SDD Workflow — Mandatory Hard Stops (BLOCKING)

**BEFORE any SDD request, gentle-ai skill invocation, or wf-* command:**

1. **READ `.agents/protocols/wf-orchestrator.md` FIRST** — this is not optional.
   - wf-orchestrator defines the authoritative gate sequence: Ladder → Preflight → Decision → TDD ritual
   - All SDD routing and skill delegation flow through wf-orchestrator
   
2. **IF you skip reading wf-orchestrator**: STOP immediately. Do not proceed with any SDD work.
   - No proposal drafting
   - No skill invocation
   - No code changes
   - Wait for explicit user confirmation that you have read it.

3. **IF wf-orchestrator says STOP at any gate**: honor it. Stop means stop.
   - No workarounds
   - No "I'll do the work anyway"
   - STOP and ask the user to clarify before proceeding

**Precedence**: wf-orchestrator is the source of truth for ALL SDD decisions. Project AGENTS.md, local protocols, and individual skills are subordinate to it.

## Critical: AI_DEV_WORKFLOW.md Synchronization

**BEFORE every commit**, if your changes affect ANY of these topics, verify and update AI_DEV_WORKFLOW.md:
- IDE paths, detection logic, routing tables, or satellite generation
- Builder phases (B1–B8), sub-agent roles, or staging workflow
- Phase numbering, phase logic, or resumption contracts
- State machine structure (`.wizard-state.json` shape)
- Commands (list, location per IDE, or behavior)
- Protocol packaging or delivery mechanism
- Testing, CI/CD, or release strategy
- Documentation structure, glossary, or major sections

**Rule**: If it's implemented in code/templates, it must be documented in AI_DEV_WORKFLOW.md. If you change the code, audit that section in the doc and update it if stale. Do not commit code changes without ensuring the doc reflects them accurately.

---

<!-- No agent protocols: the project does not use Ladder, Routes ABC, or TDD. -->

<!-- wf-version: 0.1.0-beta.1 | source: github.com/hugoafj/ai-workflow-wizard | stack: markdown-docs | features: ladder=no, tdd=no, routing=no, ci=no, cd=no, release=yes -->
