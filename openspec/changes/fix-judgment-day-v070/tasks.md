# Tasks: Critical fixes for `v0.7.0-beta.1`

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 600–900 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | 4 work units |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

```text
Decision needed before apply: recorded (size:exception approved by user)
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High
```

> `Delivery strategy` is `single-pr` with an approved `size:exception`.

### Suggested Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|------|------|----------------------|-----------------|-------------------|
| 1 | State schema + semver migration logic | `bash -n wf-init/lib/refresher.md` + `jq` migration fixtures | Simulated `.wizard-state.json` from `0.6.4-beta` to `0.7.1-beta.1` and `0.8.0` | Revert `wf-init/lib/refresher.md` + `state.md` |
| 2 | `/wf-refresh` agent-instruction orchestration | `bash -n templates/commands/wf-refresh/_base.md` + extracted `refresher.md` blocks | Run `/wf-refresh` in a clean initialized project and verify it reaches Phase R5 | Revert `templates/commands/wf-refresh/_base.md` + `wf-init/lib/refresher.md` |
| 3 | Builder + `AGENTS.md` + `wf-cleanup` | `bash -n` on modified blocks + diff generated `AGENTS.md` | Run `/wf-init` and `/wf-refresh`; verify `AGENTS.md` footer/features match state | Revert `wf-init/lib/builder.md`, `AGENTS.router.md`, `AGENTS.md`, `wf-cleanup` |
| 4 | Docs + version bump + test scenarios | `bash -n` on any bash blocks + manual diff review | Verify `AI_DEV_WORKFLOW.md` and `WF_REFRESH_TROUBLESHOOTING.md` match implementation | Revert docs and `VERSION` |

## Phase 1: Foundation — state schema and migration logic

- [x] 1.1 Update `wf-init/lib/state.md`: set `schema_version` to `3` and ensure example includes `build_plan.generated_files`, `managed_paths`, `approval`.
- [x] 1.2 Implement `version_lte` helper in `wf-init/lib/refresher.md` (pure bash, handles `x.y.z[-prerelease]`).
- [x] 1.3 Implement `migrate_state(state, from, to)` in `wf-init/lib/refresher.md` using cumulative migration blocks and `jq //=` defaults.
- [x] 1.4 Move migration rules and explanatory prose from `wf-init/lib/migrations.md` into `refresher.md`; delete `migrations.md`.
- [x] 1.5 Add `TARGET_VERSION` resolution from `VERSION` file (or remote fallback) in Phase R2.
- [x] 1.6 Run `bash -n` on all modified bash blocks; test migrations with fixtures.

## Phase 2: Core — `/wf-refresh` orchestration

- [x] 2.1 Rewrite `templates/commands/wf-refresh/_base.md` to download `wf-init/lib/refresher.md` and helpers to a temp directory and present them as instructions.
- [x] 2.2 Remove all `source` calls to `.md` files from `wf-init/lib/refresher.md`.
- [x] 2.3 Update Phase R3 in `refresher.md` to delegate Builder to `subagent-builder-core.md` and `subagent-builder-heavy.md` as agent prompts.
- [x] 2.4 Complete custom `AGENTS.md` preservation in Phase R3: extract markers and re-inject into staged `AGENTS.md`.
- [x] 2.5 Complete Phase R4 diff classification: add `deleted_modified` for user-modified deprecated files.
- [x] 2.6 Update Phase R6 to write `.wizard-managed-files.json` from full `build_plan.generated_files`.
- [x] 2.7 Run `bash -n`; manually test `/wf-refresh` reaches Phase R5 in a clean project.

## Phase 3: Builder + `AGENTS.md` + cleanup

- [x] 3.1 Fix `wf-init/lib/builder.md` to generate `AGENTS.md` footer and features table matching actual state (`routing_abc`, `decision_ladder`, `tdd_protocol`, `ci`, `release_please`).
- [x] 3.2 Fix `templates/AGENTS.router.md` placeholders (`{{discovery.commands}}`, `{{features.*_yesno}}`) by either defining corresponding state fields or removing them.
- [x] 3.3 Regenerate root `AGENTS.md` from the Builder; ensure custom markers are preserved.
- [x] 3.4 Update `templates/commands/wf-cleanup/_base.md` to remove `.wizard-managed-files.json`.
- [x] 3.5 Bump `VERSION` to `0.7.1-beta.1`.
- [x] 3.6 Verify `bash -n` and diff generated `AGENTS.md` against state.

## Phase 4: Docs + verification

- [x] 4.1 Update `AI_DEV_WORKFLOW.md`: remove `.wizard-manifests/`, old Layer 1/2/3 refresh description, stale `wf-version: 0.1.0-beta.1` example.
- [x] 4.2 Update `WF_REFRESH_TROUBLESHOOTING.md` to match actual `refresher.md` behavior (`.wizard-managed-files.json` source, `deleted_modified`, custom section preservation).
- [x] 4.3 Update `openspec/changes/refactor-wf-refresh-builder-driven/test-scenarios.md` version assertions to `0.7.1-beta.1`.
- [x] 4.4 Run `bash -n` on all modified bash blocks.
- [x] 4.5 Manual end-to-end test: `/wf-init` in a clean repo, then `/wf-refresh`, then `/wf-cleanup`.
- [x] 4.6 Final diff review against `origin/main` and user approval before commit.
