# Delta Spec: `wf-refresh`

## ADDED Requirements

### Requirement: Refresh orchestration MUST be agent-instruction based

The `/wf-refresh` command SHALL download `wf-init/lib/refresher.md` and any required phase or library files to a temporary directory before execution. The orchestrator SHALL present `refresher.md` to the agent as Markdown instructions, and the agent SHALL execute the bash blocks inside it selectively, exactly as `/wf-init` presents `phase*.md` files.

#### Scenario: `/wf-refresh` runs in a project initialized by `/wf-init`

- GIVEN a project with a valid `.wizard-state.json`
- WHEN the user invokes `/wf-refresh`
- THEN `templates/commands/wf-refresh/_base.md` downloads `wf-init/lib/refresher.md` and optional helpers to a temporary directory
- AND the agent reads `refresher.md` as instructions, not as a bash script via `source`
- AND Phase R-1 through R6 execute in order

### Requirement: `/wf-refresh` MUST NOT `source` Markdown instruction files

Neither `templates/commands/wf-refresh/_base.md` nor `wf-init/lib/refresher.md` SHALL use the bash `source` builtin on any `.md` file. All helper logic used during refresh MUST either be inline bash inside code fences or invoked through existing, documented sub-agent prompt files.

#### Scenario: `refresher.md` invokes the Builder

- GIVEN Phase R3 needs to regenerate staging
- WHEN the refresh reaches the Builder step
- THEN `refresher.md` delegates to `subagent-builder-core.md` and `subagent-builder-heavy.md` as agent prompts
- AND it does NOT call `source wf-init/subagent-builder-core.md`

### Requirement: Review gate MUST require explicit user approval

Before applying any additions, updates, or deletions, `/wf-refresh` SHALL present a grouped diff and collect explicit user approval for each category (`added`, `updated`, `deleted`, `deleted_modified`). It SHALL NOT apply changes without approval.

#### Scenario: Refresh proposes deletions of user-modified files

- GIVEN a file is in the old `build_plan.managed_paths`
- AND it still exists in the project
- AND its current hash differs from the hash recorded in `build_plan.generated_files`
- WHEN Phase R4 computes the diff
- THEN the file is classified as `deleted_modified`
- AND Phase R5 asks for explicit approval before deletion

### Requirement: Custom `AGENTS.md` sections MUST be preserved

When `refresher.md` regenerates `AGENTS.md`, it SHALL extract content between `<!-- WF: DO NOT REGENERATE -->` and `<!-- /WF: DO NOT REGENERATE -->` markers in the existing `AGENTS.md` and re-inject that content into the newly generated `AGENTS.md` at an equivalent location.

#### Scenario: User has a custom section in `AGENTS.md`

- GIVEN `AGENTS.md` contains a custom section inside the preservation markers
- WHEN Phase R3 generates a new `AGENTS.md` into `.wizard-staging/`
- THEN the custom section appears in the staged `AGENTS.md`
- AND the final promoted `AGENTS.md` retains the custom section

## MODIFIED Requirements

None — there is no prior `openspec/specs/wf-refresh/spec.md` to modify.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
