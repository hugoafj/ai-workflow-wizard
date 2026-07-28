# Protocol: SDD (Spec-Driven Development)

<!--
  SINGLE SOURCE of the wizard's permanent SDD rules. Consumed by phase45
  (backend selection + /sdd-init), phase46b (config.yaml), wf-refresh and wf-settings
  (backend migration). Source in inventory.md: phase45 (all), phase46b
  168-229, wf-refresh 85-137, wf-settings 352-418, AI_DEV_WORKFLOW 6.1-6.7.
  The config.yaml artifact is in config.yaml.tmpl.md (VERBATIM phase46b 199-229).
-->

## The three persistence backends

| Backend | What it persists | When to choose |
|---|---|---|
| `engram` | Local SQLite memory (~/.engram/); no files in the repo | Throwaway project or solo on the same machine. **Official warning: does not maintain versionable canonical specs.** |
| `openspec` | Versioned files in `openspec/` (config.yaml, specs/, changes/) | Team without Engram, or if you want SDD context auditable in git. |
| `hybrid` (recommended) | Versioned `openspec/` + Engram memory | Most cases. Versioned specs + fluid memory; no migration needed if the team grows. |

- The selection is made by the **user** (phase45); the wizard only recommends based on context
  (>1 committer → hybrid). The full text of the 3 options lives in phase45 as a
  user question and its result is stored in `state.sdd.backend`.
- If choosing `engram`: explicit confirmation of implications before continuing.

## ⛔ BLOCK RULE (hard rule) — never create SDD artifacts by hand

> This rule is INVOLABLE and applies in ALL cases (phase45 of wf-init, wf-refresh,
> wf-settings, or any flow that touches SDD). It corrects a recurring
> behavior: the agent, unable to invoke `/sdd-init`, "helps" by creating the files
> itself — and creates them incorrectly, corrupting the SDD initialization.

**If you CANNOT invoke `/sdd-init` correctly and confirm it completed**, then:

1. **PROHIBITED to manually create** `openspec/config.yaml`, `openspec/specs/`, `openspec/changes/`,
   `.atl/skill-registry.md`, or any other artifact that `/sdd-init` produces. Prohibited to
   read the sdd-init `SKILL.md` to replicate its steps. Prohibited to run
   `gentle-ai sdd-init` (that subcommand does NOT exist in the CLI).
2. **Why**: `/sdd-init` has internal logic (validations, prompts, exact format,
   orchestrator→sub-agent, context-dependent defaults) that a manual
   reimplementation CANNOT guarantee to replicate. A malformed `openspec/` is not noticed until
   `sdd-apply`/`sdd-verify` fail later — a silent failure hard to trace.
3. **What to do instead**: STOP the flow and tell the user to **open a NEW session/
   chat** in an IDE/CLI with gentle-ai skill support (Claude Code, Cursor,
   Windsurf, Kiro, OpenCode, Gemini CLI, Antigravity CLI, Codex CLI), run `/sdd-init` there choosing the
   selected backend, and when it finishes **come back to this conversation and write "done"**.
   ⚠️ **Explicitly warn them**: `/sdd-init` upon completion shows a message suggesting
   `/sdd-explore` or `/sdd-new` as next steps — **ignore that message**, do not follow
   those instructions. The task is only `/sdd-init`, then come back here.
   Do not take any alternative action in the meantime (no creating files, no verifying, no
   "advancing work").

**"Unable to invoke correctly" includes ALL these cases** (not just "the IDE does not have
slash commands"): the IDE does not support slash commands; you typed `/sdd-init` but nothing
visible happened; the skill is not registered (`gentle-ai doctor` shows it); the skill failed;
or you cannot verify that `openspec/config.yaml`, `openspec/specs/` and `openspec/changes/`
were properly created. At the SLIGHTEST doubt → apply this rule (new session), never create.

## `/sdd-init` execution

- `/sdd-init` is a **gentle-ai skill**, NOT a terminal command. `gentle-ai sdd-init`
  does not exist.
- With slash commands: type `/sdd-init` and choose the backend from `state.sdd.backend`.
- Without slash commands (e.g., Devin): exact message to the user (see phase45 183-196).
  **Prohibited to simulate the skill manually** or run nonexistent subcommands.
- `/sdd-init` does not rewrite if `openspec/` already exists (skill's Hard Rule): it reports and
  asks before touching.

## When SDD applies (routing)

The direct/Lite/full decision is resolved by **Local Orchestration** (see `decision-ladder`
protocol), not this file. Reference rule: the "15-minute rule" and
the *delta* greenfield/legacy concept are documented in `AI_DEV_WORKFLOW.md` §6.4-6.5.

## config.yaml and Strict TDD

- The complete `openspec/config.yaml` template is in `config.yaml.tmpl.md`.
- `testing.strict_tdd: true|false` is the source of truth that `sdd-apply` consults
  (see `tdd` strict variant protocol). When migrating backends, preserve `strict_tdd`.
- `openspec/config.yaml` is **excluded** from the drift hook (it is the output of /sdd-init;
  including it would cause a loop).
