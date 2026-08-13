# Test Scenarios: Refactor `/wf-refresh` to builder-driven migration

**Change**: `refactor-wf-refresh-builder-driven`  
**Status**: Test Scenarios  
**Created**: 2026-08-13

## Overview

These test scenarios verify that the new `/wf-refresh` implementation works correctly across different project states and upgrade paths.

---

## Scenario 1: No-change refresh

**Purpose**: Verify that `/wf-refresh` correctly identifies unchanged files and skips them.

**Setup**:
- Project initialized with `/wf-init` on v0.6.8-beta
- No changes to project structure or dependencies
- No changes to wizard templates

**Execution**:
```bash
cd test-project-1
/wf-refresh
```

**Expected outcome**:
- Phase R-1: No update needed (versions match)
- Phase R0: Validation passes
- Phase R1: No drift detected
- Phase R2: No migrations needed
- Phase R3: Builder runs, generates staging
- Phase R4: All files classified as "unchanged"
- Phase R5: No diffs to show; user asked if they want to continue
- Phase R6: No changes applied; exit cleanly

**Acceptance criteria**:
- [ ] No files copied
- [ ] No git commit created
- [ ] `.wizard-staging/` cleaned
- [ ] Exit code 0

---

## Scenario 2: Enable new optional feature

**Purpose**: Verify that `/wf-refresh` correctly handles enabling new optional features.

**Setup**:
- Project initialized with `/wf-init` on v0.6.4-beta (old version)
- `.wizard-state.json` has `features.decision_ladder = false`
- New wizard version v0.6.8-beta has `features.decision_ladder` available

**Execution**:
```bash
cd test-project-2
/wf-refresh
# When asked "Enable decision ladder?", answer "yes"
```

**Expected outcome**:
- Phase R-1: Update available; user approves
- Phase R0: Validation passes
- Phase R1: Project drift detected (stack changed); user approves update
- Phase R2: Schema migrated (v2 → v3); asked about new features; user enables `decision_ladder`
- Phase R3: Builder runs with new state; generates wf-ladder files
- Phase R4: New files detected (wf-ladder SKILL.md, protocols, etc.)
- Phase R5: User approves additions
- Phase R6: Files copied, state updated, commit created

**Acceptance criteria**:
- [ ] `features.decision_ladder` set to `true` in state
- [ ] wf-ladder files added to project
- [ ] Commit message includes "Added N new files"
- [ ] Exit code 0

---

## Scenario 3: Custom AGENTS.md preservation

**Purpose**: Verify that custom AGENTS.md sections are preserved during refresh.

**Setup**:
- Project initialized with `/wf-init`
- User added custom section to AGENTS.md:
  ```markdown
  <!-- WF: DO NOT REGENERATE -->
  ## Custom Team Rules
  - Always use TypeScript strict mode
  - Code reviews required for main branch
  <!-- /WF: DO NOT REGENERATE -->
  ```
- Wizard templates changed (new version)

**Execution**:
```bash
cd test-project-3
/wf-refresh
# Approve all changes
```

**Expected outcome**:
- Phase R3: Builder generates new AGENTS.md
- Custom section is extracted and re-injected
- Phase R4: AGENTS.md shows as "updated" (hash differs due to version bump)
- Phase R5: User approves update
- Phase R6: AGENTS.md copied; custom section preserved

**Acceptance criteria**:
- [ ] Custom section still present in final AGENTS.md
- [ ] Custom section is in same relative location
- [ ] Markers are preserved
- [ ] Exit code 0

---

## Scenario 4: Deprecation and file deletion

**Purpose**: Verify that deprecated files are correctly identified and deleted with user approval.

**Setup**:
- Project initialized with v0.6.4-beta (which had `wf-cicd` command)
- New wizard v0.6.8-beta removed `wf-cicd` command
- `.wizard-managed-files.json` tracks old files

**Execution**:
```bash
cd test-project-4
/wf-refresh
# When asked "Delete removed files?", answer "yes"
```

**Expected outcome**:
- Phase R3: Builder runs; `wf-cicd` not generated
- Phase R4: Old `wf-cicd` files detected as "deleted" (safe to delete)
- Phase R5: User approves deletions
- Phase R6: Old files removed, commit created

**Acceptance criteria**:
- [ ] `wf-cicd` files removed from project
- [ ] Commit message includes "Removed N deprecated files"
- [ ] Exit code 0

---

## Scenario 5: Migration from v0.6.4-beta to v0.6.8-beta

**Purpose**: Verify that state migrations work correctly across versions.

**Setup**:
- Project initialized with v0.6.4-beta
- `.wizard-state.json` has schema_version 2
- Wizard version 0.6.8-beta has schema_version 3

**Execution**:
```bash
cd test-project-5
/wf-refresh
# Approve all changes
```

**Expected outcome**:
- Phase R2: Schema migrated (v2 → v3)
  - `build_plan.generated_files` added
  - `build_plan.managed_paths` added
  - `build_plan.approval` added
- Phase R2: Wizard version migrated (0.6.4 → 0.6.8)
  - New features asked (routing_abc, decision_ladder, visual_regression)
  - New CI/CD options set to defaults
- Phase R3: Builder runs with migrated state
- Phase R6: State updated with new schema_version and wizard_version

**Acceptance criteria**:
- [ ] `schema_version` set to 3
- [ ] `wizard_version` set to "0.6.8-beta"
- [ ] `build_plan` has all three new fields
- [ ] Exit code 0

---

## Scenario 6: User rejects changes

**Purpose**: Verify that `/wf-refresh` respects user rejections and doesn't apply changes.

**Setup**:
- Project with changes detected
- User will reject all approvals

**Execution**:
```bash
cd test-project-6
/wf-refresh
# When asked for approvals, answer "no" to all
```

**Expected outcome**:
- Phases R-1 to R5 execute normally
- Phase R5: User rejects all changes
- Phase R6: Skipped (no approvals)
- No files copied
- No git commit created
- Exit code 0

**Acceptance criteria**:
- [ ] No changes applied
- [ ] No git commit created
- [ ] `.wizard-staging/` cleaned
- [ ] Exit code 0

---

## Scenario 7: User skills are never deleted

**Purpose**: Verify that user-created skills are protected from deletion.

**Setup**:
- Project with user-created skill: `.claude/skills/react-19/SKILL.md`
- Wizard has no `react-19` skill
- Old managed_paths includes `react-19` (false positive)

**Execution**:
```bash
cd test-project-7
/wf-refresh
# Approve all changes
```

**Expected outcome**:
- Phase R4: `react-19` detected as potential deletion
- But hash check shows it's different from old managed hash (user edited it)
- Classified as "delete_modified" (not safe to delete)
- Phase R5: User asked explicitly for each "delete_modified" file
- User rejects deletion of `react-19`
- Phase R6: `react-19` preserved

**Acceptance criteria**:
- [ ] `react-19` skill preserved
- [ ] User was asked explicitly about deletion
- [ ] Exit code 0

---

## Scenario 8: Hash-based change detection

**Purpose**: Verify that hash-based comparison correctly identifies changed files.

**Setup**:
- Project with existing AGENTS.md
- Wizard version bumped (VERSION file changed)
- AGENTS.md will have different hash due to version footer

**Execution**:
```bash
cd test-project-8
/wf-refresh
# Approve all changes
```

**Expected outcome**:
- Phase R3: Builder generates new AGENTS.md with new version in footer
- Phase R4: Hash comparison shows AGENTS.md hash differs
- Classified as "update"
- Phase R5: User approves update
- Phase R6: AGENTS.md copied

**Acceptance criteria**:
- [ ] AGENTS.md correctly identified as "update"
- [ ] File copied with new version
- [ ] Exit code 0

---

## Manual verification checklist

After all automated tests pass, manually verify:

- [ ] **No user skills deleted**: Check that all `.claude/skills/`, `.agents/skills/`, etc. user skills are preserved
- [ ] **Custom AGENTS.md preserved**: Check that custom sections with markers are intact
- [ ] **Commit messages conventional**: Check that commits follow conventional commit format
- [ ] **No push**: Verify that no automatic push occurred
- [ ] **Diffs reviewed**: Review all diffs before approving
- [ ] **State consistency**: Verify `.wizard-state.json` is valid after refresh
- [ ] **Managed files tracked**: Verify `.wizard-managed-files.json` is created and accurate

---

## Test execution

Run all scenarios:

```bash
#!/bin/bash
set -e

for scenario in 1 2 3 4 5 6 7 8; do
  echo "Running Scenario $scenario..."
  cd test-project-$scenario
  /wf-refresh || echo "Scenario $scenario failed"
  cd ..
done

echo "✓ All scenarios completed"
```

---

## Success criteria (overall)

- [ ] All 8 scenarios pass
- [ ] No user skills deleted in any scenario
- [ ] Custom AGENTS.md preserved in scenario 3
- [ ] Deprecated files deleted in scenario 4
- [ ] State migrations work in scenario 5
- [ ] User rejections respected in scenario 6
- [ ] Hash-based detection works in scenario 8
- [ ] Manual verification checklist completed
- [ ] No commits until user approval
