# Specification: Refactor `/wf-refresh` to builder-driven migration

**Change**: `refactor-wf-refresh-builder-driven`  
**Status**: Specification  
**Created**: 2026-08-13

## Overview

This specification details the eight phases of the new `/wf-refresh` workflow (R-1 through R6) and the supporting infrastructure (state schema, Builder updates, migrations).

## Phase R-1: Global command refresh

**Purpose**: Ensure the 3 global commands (`wf-init`, `wf-refresh`, `wf-cleanup`) and their 1:1 skills are up-to-date before proceeding with project refresh.

### Input
- Local `.wizard-state.json` (if exists)
- Remote `VERSION` file from wizard repo

### Process

```
1. Read local wizard version from:
   - AGENTS.md footer: grep "wf-version:" → extract version
   - If AGENTS.md missing: assume "0.1.0-beta.1"

2. Download remote VERSION from:
   - https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/VERSION

3. Compare versions:
   - If local == remote: skip, continue to Phase R0
   - If local < remote: propose running install.sh
     - Ask user: "Update global commands? [yes/no]"
     - If yes: run install.sh, verify success
     - If no: continue anyway (user may update later)
   - If local > remote: warn (local is ahead of remote)

4. Verify global skills are present:
   - Check .agents/skills/wf-init/SKILL.md
   - Check .agents/skills/wf-refresh/SKILL.md
   - Check .agents/skills/wf-cleanup/SKILL.md
   - If any missing: warn (will be regenerated in Phase R3)
```

### Output
- Updated global commands (if user approved)
- Continue to Phase R0

---

## Phase R0: Project validation

**Purpose**: Verify `.wizard-state.json` exists and has valid schema; detect active IDEs.

### Input
- Project root directory
- `.wizard-state.json` (if exists)

### Process

```
1. Check .wizard-state.json exists:
   - If missing: STOP, ask user to run /wf-init first
   - If exists: read and parse as JSON

2. Validate schema_version:
   - If schema_version < 2: STOP, state is too old
   - If schema_version == 2: continue (will migrate in Phase R2)
   - If schema_version == 3: continue (current)

3. Detect active IDEs from existing directories:
   - .claude/ → claude-code
   - .cursor/ → cursor
   - .windsurf/ or .devin/ → windsurf
   - .kiro/ → kiro
   - .opencode/ → opencode
   - .codex/ → codex
   - .github/copilot-instructions.md → vscode-copilot
   
   Store in memory for later phases

4. Verify wizard_version field:
   - If missing: set to "0.1.0-beta.1"
```

### Output
- Validated state and detected IDEs
- Continue to Phase R1

---

## Phase R1: Project content drift (Layer 1 replacement)

**Purpose**: Re-discover the project to detect changes in structure, dependencies, conventions.

### Input
- Project root directory
- Current `.wizard-state.json`

### Process

```
1. Run discovery commands (from subagent-discovery.md):
   - Stack detection: package.json, composer.json, pyproject.toml, Cargo.toml
   - Node engine: node -e "process.stdout.write(require('./package.json').engines?.node||'')"
   - npm major: npm --version | cut -d. -f1
   - Git commits: git log --oneline | wc -l
   - Committers: git shortlog -sne HEAD | wc -l
   - Code files: find src -name "*.ts" -o "*.js" -o "*.py" | wc -l
   - Default branch: git symbolic-ref --short refs/remotes/origin/HEAD | sed 's#origin/##'
   - CI present: ls .github/workflows/ | wc -l

2. Compare with existing discovery.* in state:
   - If stack changed: note it
   - If node_engine changed: note it
   - If conventions changed: note it

3. Present drift summary to user:
   - "Project content drift detected:"
   - List changed fields
   - Ask: "Use updated project info? [yes/no]"

4. If yes: update .wizard-state.json discovery.* fields
   If no: keep existing discovery fields
```

### Output
- Updated or kept discovery fields in state
- Continue to Phase R2

---

## Phase R2: State/schema migration

**Purpose**: Migrate `.wizard-state.json` from old schema to current; ask about new optional features.

### Input
- Current `.wizard-state.json` (possibly schema_version 2)
- `wf-init/lib/migrations.md` (migration rules)

### Process

```
1. Detect current schema_version:
   - If schema_version < 3: run migrations
   - If schema_version == 3: skip migrations

2. For each migration rule in migrations.md:
   - Apply field additions with defaults
   - Rename deprecated fields
   - Migrate feature flags

3. After migrations, bump schema_version to 3

4. Detect new optional features not in state:
   - features.decision_ladder (if missing)
   - features.tdd_protocol (if missing)
   - features.routing_abc (if missing)
   - features.ci (if missing)
   - features.cd (if missing)
   - features.release_please (if missing)

5. For each new feature:
   - Ask user: "Enable <feature>? [yes/no]"
   - Only enable if user explicitly says yes
   - Never auto-enable

6. Update state with new features and schema_version
```

### Output
- Migrated and updated `.wizard-state.json` (schema_version 3)
- Continue to Phase R3

---

## Phase R3: Build new staging

**Purpose**: Re-run the Builder (B1-B9) to generate all artifacts into `.wizard-staging/`.

### Input
- Updated `.wizard-state.json`
- Wizard templates from GitHub (or local if available)

### Process

```
1. Clean staging:
   - rm -rf .wizard-staging/

2. Create fresh staging:
   - mkdir -p .wizard-staging/

3. Run Builder-Core (B1-B6):
   - Load state
   - Resolve selection keys (STACK, IDES, TDD_MODE, LAYERS, etc.)
   - Assemble protocol bodies
   - Pack protocols per IDE
   - Assemble AGENTS.md router
   - Generate satellites per IDE

4. Run Builder-Heavy (B7-B9):
   - Generate commands per IDE
   - Generate post-commit hook
   - Generate testing configs
   - Generate CI/CD artifacts
   - Register build_plan

5. Preserve custom AGENTS.md content:
   - If AGENTS.md exists in project:
     - Extract sections inside <!-- WF: DO NOT REGENERATE --> markers
     - After Builder generates AGENTS.md in staging:
       - Re-inject custom sections in same relative location
   - If no existing AGENTS.md: generate normally

6. Register all generated files in state.build_plan:
   - For each file in staging:
     - Calculate SHA256 hash
     - Add to build_plan.generated_files: { path, hash }
     - Add to build_plan.managed_paths: [list of paths]
```

### Output
- `.wizard-staging/` with all generated files
- Updated `state.build_plan.generated_files` and `state.build_plan.managed_paths`
- Continue to Phase R4

---

## Phase R4: Diff and plan

**Purpose**: Compare staging with project; classify each file as add/update/delete/unchanged.

### Input
- `.wizard-staging/` (newly generated)
- Project root directory
- Old `state.build_plan.managed_paths` (from previous run)
- `.wizard-managed-files.json` (if exists from previous run)

### Process

```
1. For each file in staging:
   - Calculate SHA256 hash
   - Check if file exists in project at same path
   
   If exists:
     - Calculate project file's SHA256
     - If hashes equal: classify as "unchanged"
     - If hashes differ: classify as "update"
   
   If not exists:
     - Classify as "add"

2. For each file in old managed_paths:
   - Check if file exists in new staging
   
   If not exists:
     - Check if file still exists in project
     - If exists in project:
       - Check if hash matches old managed hash
       - If matches: classify as "delete" (safe to delete)
       - If differs: classify as "delete_modified" (user edited, warn)
     - If not exists in project: already deleted, skip

3. Build refresh-plan.json:
   {
     "added": [ { path, hash } ],
     "updated": [ { path, old_hash, new_hash } ],
     "deleted": [ { path, hash, reason } ],
     "unchanged": [ { path, hash } ],
     "deleted_modified": [ { path, old_hash, current_hash } ]
   }

4. Calculate statistics:
   - Total files: added + updated + deleted + unchanged
   - Changes: added + updated + deleted
   - Skipped: unchanged
```

### Output
- `refresh-plan.json` with classified files
- Continue to Phase R5

---

## Phase R5: Review gate

**Purpose**: Present grouped diff to user; require explicit approval for deletions.

### Input
- `refresh-plan.json`
- Staging and project files

### Process

```
1. Group and present diff:

   === ADDED FILES ===
   - .claude/skills/wf-onboard/SKILL.md
   - .agents/protocols/wf-tdd.md
   [total: N files]
   
   === UPDATED FILES ===
   - AGENTS.md (changed: features, wf-version)
   - .github/workflows/release-please.yml (changed: permissions)
   [total: N files]
   
   === DELETED FILES ===
   - .claude/skills/wf-cicd/SKILL.md (deprecated)
   - .github/workflows/old-ci.yml (removed in new version)
   [total: N files]
   
   === UNCHANGED FILES ===
   [total: N files, skipped]

2. For each group, ask approval:
   - "Apply added files? [yes/no]"
   - "Apply updated files? [yes/no]"
   - "Delete removed files? [yes/no]"
   
   For "delete_modified" files:
   - "File <path> was edited by you. Delete anyway? [yes/no]"

3. Collect approvals into state.build_plan.approval

4. If any "no": ask if user wants to continue anyway or abort
```

### Output
- User approvals recorded in state
- Continue to Phase R6 (if approved) or abort

---

## Phase R6: Apply and close

**Purpose**: Copy approved changes, update state, commit, clean staging.

### Input
- `refresh-plan.json`
- User approvals
- `.wizard-staging/`

### Process

```
1. Apply approved adds/updates:
   - For each file in added + updated:
     - If approved: copy from staging to project
     - Create parent directories as needed
     - chmod +x for hooks

2. Apply approved deletions:
   - For each file in deleted:
     - If approved: rm -f <path>

3. Update .wizard-state.json:
   - Set wizard_version to remote VERSION
   - Update build_plan.generated_files with new hashes
   - Update build_plan.managed_paths with new paths
   - Set migrated_features: true

4. Write .wizard-managed-files.json:
   {
     "wizard_version": "0.6.8-beta.1",
     "generated_at": "ISO-8601",
     "files": [
       { path, hash, managed: true },
       ...
     ]
   }

5. Add .wizard-managed-files.json to .gitignore

6. Runtime setup (idempotent):
   - If .husky/ missing but conventional_commits == true:
     - Ask: "Initialize Husky? [yes/no]"
     - If yes: npx husky init
   - If testing deps missing:
     - Ask: "Install testing dependencies? [yes/no]"
     - If yes: npm install --save-dev <deps>
   - If gga local mode:
     - Ask: "Install GGA hook? [yes/no]"
     - If yes: gga install

7. Git operations:
   - git add <changed files>
   - git add .wizard-state.json
   - git add .wizard-managed-files.json
   - git commit -m "chore: refresh workflow to v<VERSION>
   
     - Updated AGENTS.md with new project info
     - Added <N> new files
     - Updated <N> files
     - Removed <N> deprecated files
     
     Generated with /wf-refresh"

8. Clean staging:
   - rm -rf .wizard-staging/

9. Report success:
   - "✓ Refresh complete"
   - "Files: <N> added, <N> updated, <N> deleted"
   - "Commit: <hash>"
   - "Next: git push (when ready)"
```

### Output
- Applied changes to project
- Updated state and managed files
- Committed changes (no push)
- Cleaned staging

---

## Supporting infrastructure

### State schema extension (wf-init/lib/state.md)

```json
{
  "build_plan": {
    "agents_md": false,
    "satellites": [],
    "commands": [],
    "protocols_flat": [],
    "protocols_skills": [],
    "hook": false,
    "staging_dir": ".wizard-staging",
    "generated_files": [
      { "path": "AGENTS.md", "hash": "sha256:...", "managed": true },
      { "path": ".claude/skills/wf-ladder/SKILL.md", "hash": "sha256:...", "managed": true }
    ],
    "managed_paths": [
      "AGENTS.md",
      ".claude/skills/wf-ladder/SKILL.md",
      ".agents/protocols/wf-ladder.md",
      ...
    ],
    "approval": {
      "added": true,
      "updated": true,
      "deleted": true
    }
  }
}
```

### Migrations (wf-init/lib/migrations.md)

```
Migration rules keyed by schema_version and wizard_version:

schema_version 2 → 3:
  - Add build_plan.generated_files = []
  - Add build_plan.managed_paths = []
  - Add build_plan.approval = {}
  - Rename discovery.prior_artifacts → discovery.prior_artifacts (no change)

wizard_version 0.6.4 → 0.6.8:
  - Add features.routing_abc if missing (default: false)
  - Add features.decision_ladder if missing (default: false)
  - Add testing.visual_regression if missing (default: false)
  - Add ci.e2e_in_ci if missing (default: false)
  - Add ci.auto_improve if missing (default: true)
  - Add ci.inline_suggestions if missing (default: true)
```

### Builder updates (lib/builder.md, subagent-*.md, phase8.md)

**Step B9 (Register plan and advance)**:
```
Populate state.build_plan with exact list of files in staging:
  - For each file in staging:
    - Calculate SHA256 hash
    - Add to build_plan.generated_files: { path, hash, managed: true }
    - Add to build_plan.managed_paths: [path]
  
  Mark phases.phase6.status = done, phase_pointer = phase7
```

**Phase 8 (Promote staging and commit)**:
```
After copying files to project:
  - Write .wizard-managed-files.json:
    {
      "wizard_version": <from state>,
      "generated_at": <ISO-8601>,
      "files": [
        { path, hash, managed: true },
        ...
      ]
    }
  - Add .wizard-managed-files.json to .gitignore
```

### Custom AGENTS.md preservation (Builder)

**Before regenerating AGENTS.md**:
```
1. If AGENTS.md exists in project:
   - Read AGENTS.md
   - Extract all sections inside <!-- WF: DO NOT REGENERATE --> markers
   - Store in memory

2. Generate AGENTS.md from AGENTS.router.md (normal Builder flow)

3. After generation:
   - If custom sections exist:
     - Find relative location in generated AGENTS.md
     - Re-inject custom sections at same location
   - If no custom sections: use generated AGENTS.md as-is
```

---

## Error handling

### Phase R-1
- If `install.sh` fails: warn, continue anyway
- If remote VERSION unreachable: warn, use local version

### Phase R0
- If `.wizard-state.json` missing: STOP, ask user to run `/wf-init`
- If schema_version < 2: STOP, state too old

### Phase R1
- If discovery commands fail: warn, keep existing discovery

### Phase R2
- If migration fails: STOP, ask user to run `/wf-cleanup` + `/wf-init`

### Phase R3
- If Builder fails: STOP, show error, ask user to check state

### Phase R4
- If staging is empty: STOP, Builder failed

### Phase R5
- If user rejects all changes: abort, no changes applied

### Phase R6
- If git operations fail: STOP, preserve state for manual recovery
- If runtime setup fails: warn, continue (user can run manually)

---

## Success criteria

- [ ] All 8 phases execute in order
- [ ] Hash-based diff correctly identifies add/update/delete/unchanged
- [ ] User skills are never deleted (protected by pattern + hash)
- [ ] Custom AGENTS.md rules are preserved
- [ ] State migrations work for 0.6.4-beta → 0.6.8-beta
- [ ] No commits until all approvals given
- [ ] Staging cleaned after completion
