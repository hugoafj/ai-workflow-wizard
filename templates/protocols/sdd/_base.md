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

Whether this project's own rules force an explicit SDD request is resolved by **`wf-sdd-trigger`**
(this wizard's own protocol), not this file. gentle-ai's own routing/delegation mechanics are its
exclusive authority once that explicit request is made. Reference rule: the "15-minute rule" and
the *delta* greenfield/legacy concept are documented in `AI_DEV_WORKFLOW.md` §6.4-6.5.

## config.yaml and Strict TDD

- `openspec/config.yaml` is the exclusive artifact of gentle-ai's `/sdd-init`. Per gentle-ai's own
  documentation (`docs/openspec-config.md`), there is no Go-side parser/validator enforcing a
  canonical schema for this file — it is prompt-driven, and its exact shape is **not fully uniform**
  even across gentle-ai's own skills (e.g. `strict_tdd`/`testing`/`layers` may live at the top level
  or nested under `context.*`, depending on how `/sdd-init` wrote it for this project).
- `strict_tdd: true|false` is the source of truth that `sdd-apply`/`sdd-verify` consult (see `wf-tdd`
  strict variant protocol). When migrating backends, preserve `strict_tdd`.
- `openspec/config.yaml` is **excluded** from the drift hook (it is the output of /sdd-init;
  including it would cause a loop).

### Wizard-Allowed Field Edits (Hard Rule)

The wizard (Phase 4.6b, `wf-settings`, Phase 8 step 8.1d) may ask the **current agent** to update a
small, fixed set of leaf fields inside the EXISTING `openspec/config.yaml` — never regenerate or
overwrite the file, and never do it via a script/template stamp (`config.yaml.tmpl.md` is
documentation of these fields, not a file to copy — see its header comment):

| Allowed field | When |
|---|---|
| `strict_tdd` | Toggling Strict TDD Mode (Phase 4.6 / `wf-settings`) |
| `testing.runner.{command,framework}` | Testing stack activated/changed (Phase 8, step 8.1d) |
| `testing.layers.<layer>.{available,tool}` | Testing layers activated/changed (Phase 8, step 8.1d) |
| `testing.coverage.{available,command}` | Coverage extra activated (Phase 8, step 8.1d) |
| `rules.verify.coverage_threshold` | Coverage extra activated (Phase 8, step 8.1d) |
| `rules.apply.test_command` / `rules.verify.{test_command,build_command}` | Testing/CI scripts added (Phase 8, step 8.1d) |
| the backend/artifact-store field (name may vary — read the real file first, never assume) | SDD backend migration (`wf-settings`, section 8) |

These map onto gentle-ai's canonical schema (`_shared/openspec-convention.md`,
`docs/openspec-config.md`, the `openspec/config.yaml` in the gentle-ai repo): `sdd-apply` reads the
`testing` section for runner detection and `rules.apply.test_command` as override; `sdd-verify`
reads `rules.verify.{test_command,build_command,coverage_threshold}`. Do NOT invent top-level keys
(`configured`, `planned`, `extras`, `conventions`, `checks_before_done`) — no gentle-ai consumer
reads them. Wizard concepts without a gentle-ai field (`visual_regression`, `page_object_model`)
stay in `.wizard-state.json`; they surface in the generated `playwright.config.ts` / `e2e/pages/`.

**Every edit MUST**: (1) read the real file first, (2) change only the listed leaf values, (3)
preserve everything else verbatim (`artifact_store`/`schema`, `project`, `context.*`, `sdd.*`,
`notes`, `rules.*` beyond the listed keys, and any other key present). The `testing.*`/`rules.*`
fields are written at the canonical gentle-ai nesting (`rules.verify.coverage_threshold`,
`testing.runner.{command,framework}`, `testing.layers.<layer>.{available,tool}`) even when
`/sdd-init` wrote the file at a different nesting — that is where gentle-ai's consumers read them
(`docs/openspec-config.md` documents the shape is not fully uniform across versions). If the real
file already carries the same value at a non-canonical nesting, leave the old key in place and
confirm the canonical one is set. If the correct location is ambiguous, ask the user before writing.
