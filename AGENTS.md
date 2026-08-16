# AGENTS.md — workflow-wizard

IMPORTANTE! Este wizard está diseñado como prosa instructiva + snippets bash como gatillos, no como scripts autocontenidos.

## Commands

This is a documentation/templates repository; there are no automated build, test, lint, or deploy commands. Run checks manually or via your IDE's Markdown tooling.

Wizard slash commands are documented in the README and generated from `templates/commands/`.

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
  lib/            — builder.md, state.md, state-helpers.sh, refresher.md (contracts/helpers)
  phase*.md       — phases 0-8 (plus 0b, 0c, 4.5, 4.6, 4.6b, 4.7, 6a, 6b)
  subagent-*.md   — sub-agent prompts (discovery, builder-core, builder-heavy)
```

<!-- WF: DO NOT REGENERATE -->
## Artifact Store

This project declares **OpenSpec** as the SDD artifact store; change artifacts live in `openspec/changes/<change-name>/`.
<!-- /WF: DO NOT REGENERATE -->

## Critical Constraints

- No production code (markdown/templates project of the workflow wizard)
- No push — the user decides when
- Mandatory human review gate before every commit

## Programmatic Checks

Manual review and validation; no automated lint/build for this markdown-only repository.

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


<!-- WF: DO NOT REGENERATE -->
## Critical: AI_DEV_WORKFLOW.md Synchronization

**BEFORE every commit**, if your changes affect ANY of these topics, verify and update AI_DEV_WORKFLOW.md:
- IDE paths, detection logic, routing tables, or satellite generation
- Builder phases (B1–B9), sub-agent roles, or staging workflow
- Phase numbering, phase logic, or resumption contracts
- State machine structure (`.wizard-state.json` shape)
- Commands (list, location per IDE, or behavior)
- Protocol packaging or delivery mechanism
- Testing, CI/CD, or release strategy
- Documentation structure, glossary, or major sections

**Rule**: If it's implemented in code/templates, it must be documented in AI_DEV_WORKFLOW.md. If you change the code, audit that section in the doc and update it if stale. Do not commit code changes without ensuring the doc reflects them accurately.
<!-- /WF: DO NOT REGENERATE -->

---

<!-- WF: DO NOT REGENERATE -->
<!-- No agent protocols: the project does not use wf-ladder, wf-sdd-trigger, or wf-tdd. -->
<!-- /WF: DO NOT REGENERATE -->

<!-- wf-version: 0.7.1-beta.1 | source: github.com/hugoafj/ai-workflow-wizard | stack: markdown-docs | features: ladder=no, tdd=no, routing=no, ci=no, cd=no, release=yes -->
