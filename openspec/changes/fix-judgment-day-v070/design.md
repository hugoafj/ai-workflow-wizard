# Design: Critical fixes for `v0.7.0-beta.1`

## Technical Approach

1. Convert `/wf-refresh` into an agent-instruction workflow: the global command downloads `wf-init/lib/refresher.md` and supporting files to a temp directory, then the agent reads them as Markdown instructions and executes the fenced bash blocks one at a time.
2. Replace the hardcoded `0.6.8-beta` migration target with a portable semver comparison helper (`version_lte`) and a cumulative migration list that always migrates to the real `TARGET_VERSION`.
3. Absorb executable migration logic from `wf-init/lib/migrations.md` into pure bash inside `wf-init/lib/refresher.md`; keep `migrations.md` as a documentation-only artifact or remove it.
4. Delegate Builder execution in Phase R3 to the existing sub-agent prompts (`subagent-builder-core.md`, `subagent-builder-heavy.md`) instead of `source`-ing them.
5. Complete Phase R3 custom `AGENTS.md` preservation and Phase R4 `deleted_modified` classification.
6. Sync `AGENTS.md`, `AI_DEV_WORKFLOW.md`, and `WF_REFRESH_TROUBLESHOOTING.md` with the builder-driven refresh model.
7. Unify `.wizard-managed-files.json` generation and ensure `wf-cleanup` removes it.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|---|---|---|---|
| `/wf-refresh` execution model | Download + agent reads instructions | Keep `source` on `.md` | Markdown files are contracts/docs, not shell. Avoids bash parsing prose. |
| Version comparison | Pure bash `version_lte` with `IFS` and numeric compare | External `semver` tool; `sort -V` | No new dependency; works in any bash environment. |
| Migration source of truth | Cumulative migration list inside `refresher.md` | Keep `source migrations.md` | `migrations.md` can stay human-readable docs; executable code is shell-only. |
| Builder invocation | Sub-agent prompt delegation | Inline builder in `refresher.md` | Reuses existing `/wf-init` sub-agents; single source of truth. |
| `.wizard-managed-files.json` | Generated from full `build_plan.generated_files` | Generated only from `added + updated` | Allows correct deletion detection on next refresh. |
| `AGENTS.md` sync | Regenerate from `builder.md` truth table | Hand-edit | Prevents drift between footer/features and builder output. |

## Data Flow

```
User invokes /wf-refresh
  │
  ▼
templates/commands/wf-refresh/_base.md
  ├── downloads wf-init/lib/refresher.md → /tmp/wf-refresh-phases/
  └── agent reads refresher.md as instructions
  │
  ▼
Phase R-1: self-update check (curl VERSION, compare with version_lte)
Phase R0:  validate .wizard-state.json (schema_version >= 3)
Phase R1:  re-discover project
Phase R2:  migrate_state(from_version, TARGET_VERSION)
  │         ├── version_lte compares semver
  │         └── applies every migration block where from < block.to <= TARGET
  ▼
Phase R3:  run Builder via subagent-builder-core.md / -heavy.md
  │         ├── generate artifacts into .wizard-staging/
  │         └── preserve custom AGENTS.md markers
  ▼
Phase R4:  hash diff staging vs project
  │         ├── unchanged / added / updated / deleted / deleted_modified
  │         └── write refresh-plan.json
  ▼
Phase R5:  grouped diff → explicit user approvals
  ▼
Phase R6:  apply approved changes
  │         ├── copy added/updated files
  │         ├── delete approved deprecated files
  │         ├── write .wizard-managed-files.json from full generated_files
  │         ├── update .wizard-state.json
  │         └── git add -A + commit (after user approval)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `templates/commands/wf-refresh/_base.md` | Modify | Download `refresher.md` and friends; present them to agent; remove `source`. |
| `wf-init/lib/refresher.md` | Modify | Remove `source` calls; add `version_lte`; inline migrations; complete R3/R4 logic. |
| `wf-init/lib/migrations.md` | Modify or Delete | Convert to docs or remove; logic moves to `refresher.md`. |
| `wf-init/lib/state.md` | Modify | Fix `schema_version` to `3`; ensure example matches schema. |
| `wf-init/lib/builder.md` | Modify | Ensure generated `AGENTS.md` footer/features table is correct. |
| `templates/AGENTS.router.md` | Modify | Replace `{{discovery.commands}}` / `{{features.*_yesno}}` with real fields or remove. |
| `AGENTS.md` | Regenerate | Sync from builder output. |
| `AI_DEV_WORKFLOW.md` | Modify | Remove `.wizard-manifests/`, old refresh layers, stale `wf-version` example. |
| `WF_REFRESH_TROUBLESHOOTING.md` | Modify | Match actual `refresher.md` behavior. |
| `templates/commands/wf-cleanup/_base.md` | Modify | Remove `.wizard-managed-files.json`. |
| `VERSION` | Modify | `0.7.1-beta.1`. |
| `openspec/changes/refactor-wf-refresh-builder-driven/test-scenarios.md` | Modify | Update version assertions. |

## Interfaces / Contracts

```bash
# Returns 0 if $1 <= $2 (semver), 1 otherwise.
version_lte() {
  local v1="${1//-/~}"
  local v2="${2//-/~}"
  # Split into arrays, pad to 4 numeric components, compare lexicographically
  # after normalizing pre-release separator to '~' so ASCII puts -rc < empty.
}

# Migrates state from $1 to $2 idempotently using jq.
migrate_state() {
  local STATE="$1"
  local FROM="$2"
  local TO="$3"
  # Apply each migration block whose range includes FROM..TO
}
```

`build_plan` schema (v3):
- `generated_files[]`: `{path, hash, managed}`
- `managed_paths[]`: `path`
- `approval{}`: `{added, updated, deleted, deleted_modified}` booleans

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Static | All modified bash blocks | `bash -n <file>` on extracted code |
| Migration | Old `.wizard-state.json` fixtures | Simulate `migrate_state` from `0.6.4-beta` to `0.7.1-beta.1` and `0.8.0` |
| `/wf-refresh` | Clean initialized project | Run `/wf-refresh` end-to-end and verify it reaches Phase R5 |
| Safety | User-modified deprecated file | Verify classification as `deleted_modified` and approval gate |
| Docs | `AGENTS.md` / troubleshooting | Diff review against builder output and actual `refresher.md` behavior |

## Threat Matrix

| Boundary | Minimum adversarial cases | Applicability | Design response | Planned RED tests |
|---|---|---|---|---|
| Documentation-like paths | `wf-init/lib/refresher.md`, `migrations.md`, `subagent-builder-*.md` executed as shell | Applicable | Markdown files are agent instructions; bash blocks extracted and validated with `bash -n` before execution; `source` on `.md` is removed | 1) Try `source refresher.md` → must fail; 2) Extract each bash block and run `bash -n` → must pass |
| Git repository selection | N/A | N/A: no new repo selection logic | — | — |
| Commit state | `git add -A` in Phase R6 adds unrelated user changes | Applicable | Document that user must stage only intended changes before `/wf-refresh`; Phase R6 uses `git add -A` as before, but review gate precedes it | Test that uncommitted user files appear in diff and are only committed if approved (they remain unstaged if not in plan) |
| Push state | N/A | N/A: no push in `/wf-refresh` | — | — |
| PR commands | N/A | N/A: no PR automation in this change | — | — |

## Migration / Rollout

- New `VERSION`: `0.7.1-beta.1`.
- Phase R2 reads the `VERSION` file (or remote `VERSION` if reachable) as `TARGET_VERSION`.
- `version_lte` determines which migration blocks to apply.
- Existing projects on `0.6.4-beta` through `0.7.0-beta.1` migrate forward to `0.7.1-beta.1`.
- If migration fails, `refresher.md` stops and suggests `wf-cleanup` + `wf-init`.

## Open Questions

- [x] Should `migrations.md` be deleted entirely or kept as a human-readable migration log while `refresher.md` owns the executable rules?
  **Decision**: Delete `migrations.md`; migrate its executable rules and explanatory prose into `refresher.md` so there is a single source of truth.
- [x] Should `AGENTS.md` be fully regenerated by `/wf-refresh` (treating it as a managed artifact) or partially patched?
  **Decision**: Regenerate `AGENTS.md` fully from the Builder during `/wf-refresh`; preserve custom sections inside `<!-- WF: DO NOT REGENERATE -->` markers and honor custom rules markers.
