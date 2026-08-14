# AGENTS.md — workflow-wizard

## Commands

| Command | Source template |
|---|---|
| `/wf-refresh` | `templates/commands/wf-refresh/_base.md` |
| `/wf-worktree` | `templates/commands/wf-worktree/_base.md` |
| `/wf-settings` | `templates/commands/wf-settings/_base.md` |
| `/wf-onboard` | `templates/commands/wf-onboard/_base.md` |
| `/wf-cleanup` | `templates/commands/wf-cleanup/_base.md` |

`/wf-refresh` and `/wf-cleanup` are installed globally by `install.sh`; `/wf-worktree`, `/wf-settings`, and `/wf-onboard` are generated per project by `/wf-init`.

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

## Artifact Store

This project declares **OpenSpec** as the SDD artifact store; change artifacts live in `openspec/changes/<change-name>/`.

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

<!-- wf-version: 0.7.1-beta.1 | source: github.com/hugoafj/ai-workflow-wizard | stack: markdown-docs | features: ladder=no, tdd=no, routing=no, ci=no, cd=no, release=yes -->
