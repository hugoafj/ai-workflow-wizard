# Delta Spec: `state-migration`

## ADDED Requirements

### Requirement: Wizard version migrations MUST be cumulative and semver-aware

The migration logic in `wf-init/lib/refresher.md` SHALL compare versions using a proper semver ordering function, not lexicographic string comparison. It SHALL apply every migration whose target range includes the current project version up to the actual `TARGET_VERSION`. The final `.wizard-state.json` SHALL store the real `TARGET_VERSION`, not a hardcoded value.

#### Scenario: Project on `0.6.4-beta` refreshes to `0.7.1-beta.1`

- GIVEN a project whose `.wizard-state.json` has `wizard_version: "0.6.4-beta"`
- AND the wizard `VERSION` file is `0.7.1-beta.1`
- WHEN Phase R2 runs
- THEN the migration logic detects `0.6.4-beta` < `0.7.1-beta.1`
- AND applies the `0.6.4 → 0.6.8` migration block and any subsequent migration blocks up to `0.7.1-beta.1`
- AND writes `wizard_version: "0.7.1-beta.1"` to state

#### Scenario: Future release `0.8.0` is greater than `0.6.8-beta`

- GIVEN a project whose `wizard_version` is `0.7.1-beta.1`
- AND the new wizard version is `0.8.0`
- WHEN Phase R2 runs
- THEN the migration logic correctly identifies `0.7.1-beta.1` < `0.8.0`
- AND applies all migrations between those versions

### Requirement: Migration comparison MUST NOT use ASCII ordering

The version comparison function SHALL NOT rely on bash `[[ "$a" < "$b" ]]` because it treats `0.10.0` as less than `0.6.8` and `0.6.10` as less than `0.6.8`.

#### Scenario: Comparing `0.10.0` and `0.6.8-beta`

- GIVEN two versions `0.10.0` and `0.6.8-beta`
- WHEN the migration guard evaluates whether to migrate
- THEN it correctly reports `0.6.8-beta` < `0.10.0`
- AND does NOT re-apply the `0.6.4 → 0.6.8` migration

### Requirement: Schema version label MUST match the schema contents

`wf-init/lib/state.md` SHALL declare the `schema_version` that matches the example state it documents. If the example includes `build_plan.generated_files`, `build_plan.managed_paths`, and `build_plan.approval`, the schema version SHALL be `3`.

#### Scenario: New project initializes state

- GIVEN `/wf-init` creates `.wizard-state.json` from `state.md`
- WHEN the file is written
- THEN `schema_version` is `3`
- AND `build_plan` contains `generated_files`, `managed_paths`, and `approval` arrays/objects

## MODIFIED Requirements

None — there is no prior `openspec/specs/state-migration/spec.md` to modify.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
