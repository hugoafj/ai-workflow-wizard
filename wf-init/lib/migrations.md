# State migrations — schema and version upgrades

This library defines migration rules for `.wizard-state.json` when upgrading between wizard versions or schema versions.

## Overview

Migrations are applied in `/wf-refresh` Phase R2 (State/schema migration). They are idempotent: applying the same migration twice produces the same result.

## Schema version migrations

### Schema v2 → v3

**Trigger**: `schema_version < 3`

**Changes**:
- Add `build_plan.generated_files[]` (empty array)
- Add `build_plan.managed_paths[]` (empty array)
- Add `build_plan.approval{}` (empty object)

**Implementation**:

```bash
# In Phase R2, after reading state:
if [[ $(jq -r '.schema_version' "$WF_STATE") -lt 3 ]]; then
  # Add new build_plan fields
  jq '.build_plan.generated_files //= [] |
      .build_plan.managed_paths //= [] |
      .build_plan.approval //= {} |
      .schema_version = 3' "$WF_STATE" > "$WF_STATE.tmp"
  mv "$WF_STATE.tmp" "$WF_STATE"
  
  echo "✓ Migrated schema v2 → v3"
fi
```

---

## Wizard version migrations

### Wizard v0.6.4-beta → v0.6.8-beta

**Trigger**: `wizard_version < "0.6.8-beta"`

**Changes**:

1. **New optional features** (ask user to enable):
   - `features.routing_abc` (default: false) — ABC routing pattern for SDD
   - `features.decision_ladder` (default: false) — decision ladder for architecture
   - `features.visual_regression` (default: false) — visual regression testing

2. **New testing options**:
   - `testing.visual_regression` (default: false) — enable visual regression tests

3. **New CI/CD options**:
   - `ci.e2e_in_ci` (default: false) — run E2E tests in CI
   - `ci.auto_improve` (default: true) — auto-improve via AI reviewer
   - `ci.inline_suggestions` (default: true) — inline code suggestions

4. **Deprecated fields** (remove if present):
   - `features.wf_cicd` (removed, replaced by `ci.*`)

**Implementation**:

```bash
# In Phase R2, after schema migration:
CURRENT_VERSION=$(jq -r '.wizard_version' "$WF_STATE")

# Compare versions (simple string comparison for beta versions)
if [[ "$CURRENT_VERSION" < "0.6.8-beta" ]]; then
  
  # Add new optional features (ask user)
  if ! jq -e '.features.routing_abc' "$WF_STATE" > /dev/null 2>&1; then
    read -p "Enable ABC routing pattern? [y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      jq '.features.routing_abc = true' "$WF_STATE" > "$WF_STATE.tmp"
      mv "$WF_STATE.tmp" "$WF_STATE"
    else
      jq '.features.routing_abc = false' "$WF_STATE" > "$WF_STATE.tmp"
      mv "$WF_STATE.tmp" "$WF_STATE"
    fi
  fi
  
  if ! jq -e '.features.decision_ladder' "$WF_STATE" > /dev/null 2>&1; then
    read -p "Enable decision ladder? [y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      jq '.features.decision_ladder = true' "$WF_STATE" > "$WF_STATE.tmp"
      mv "$WF_STATE.tmp" "$WF_STATE"
    else
      jq '.features.decision_ladder = false' "$WF_STATE" > "$WF_STATE.tmp"
      mv "$WF_STATE.tmp" "$WF_STATE"
    fi
  fi
  
  if ! jq -e '.features.visual_regression' "$WF_STATE" > /dev/null 2>&1; then
    read -p "Enable visual regression testing? [y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      jq '.features.visual_regression = true' "$WF_STATE" > "$WF_STATE.tmp"
      mv "$WF_STATE.tmp" "$WF_STATE"
    else
      jq '.features.visual_regression = false' "$WF_STATE" > "$WF_STATE.tmp"
      mv "$WF_STATE.tmp" "$WF_STATE"
    fi
  fi
  
  # Add new testing options (default values)
  jq '.testing.visual_regression //= false' "$WF_STATE" > "$WF_STATE.tmp"
  mv "$WF_STATE.tmp" "$WF_STATE"
  
  # Add new CI/CD options (default values)
  jq '.ci.e2e_in_ci //= false |
      .ci.auto_improve //= true |
      .ci.inline_suggestions //= true' "$WF_STATE" > "$WF_STATE.tmp"
  mv "$WF_STATE.tmp" "$WF_STATE"
  
  # Remove deprecated fields
  jq 'del(.features.wf_cicd)' "$WF_STATE" > "$WF_STATE.tmp"
  mv "$WF_STATE.tmp" "$WF_STATE"
  
  # Update wizard_version
  jq '.wizard_version = "0.6.8-beta"' "$WF_STATE" > "$WF_STATE.tmp"
  mv "$WF_STATE.tmp" "$WF_STATE"
  
  echo "✓ Migrated wizard v0.6.4-beta → v0.6.8-beta"
fi
```

---

## Default values for new fields

When a field is missing and no migration rule applies, use these defaults:

| Field | Default | Reason |
|-------|---------|--------|
| `features.routing_abc` | `false` | Optional feature; user decides |
| `features.decision_ladder` | `false` | Optional feature; user decides |
| `features.visual_regression` | `false` | Optional feature; user decides |
| `testing.visual_regression` | `false` | Optional; not enabled by default |
| `ci.e2e_in_ci` | `false` | Optional; not enabled by default |
| `ci.auto_improve` | `true` | Enabled by default (useful) |
| `ci.inline_suggestions` | `true` | Enabled by default (useful) |
| `build_plan.generated_files` | `[]` | Empty until Builder populates |
| `build_plan.managed_paths` | `[]` | Empty until Builder populates |
| `build_plan.approval` | `{}` | Empty until user approves changes |

---

## Migration order

Migrations are applied in this order:

1. **Schema migrations** (v2 → v3, etc.)
2. **Wizard version migrations** (0.6.4 → 0.6.8, etc.)
3. **Feature enablement** (ask user about new optional features)
4. **Defaults** (apply default values for missing fields)

---

## Testing migrations

To test a migration:

1. Create a `.wizard-state.json` with old schema/version
2. Run Phase R2 of `/wf-refresh`
3. Verify state is migrated correctly
4. Verify user was asked about new optional features
5. Verify no data loss

Example test state (v0.6.4-beta, schema v2):

```json
{
  "wizard_version": "0.6.4-beta",
  "schema_version": 2,
  "discovery": { "stack_key": "node-react" },
  "answers": { "ides": ["claude"] },
  "features": { "ci": true, "release_please": true },
  "testing": { "layers": 3, "tdd_mode": "standard" },
  "ci": { "ai_reviewer": true },
  "build_plan": {
    "agents_md": false,
    "satellites": [],
    "commands": [],
    "protocols_flat": [],
    "protocols_skills": [],
    "hook": false,
    "staging_dir": ".wizard-staging"
  }
}
```

After migration to v0.6.8-beta, schema v3:

```json
{
  "wizard_version": "0.6.8-beta",
  "schema_version": 3,
  "discovery": { "stack_key": "node-react" },
  "answers": { "ides": ["claude"] },
  "features": {
    "ci": true,
    "release_please": true,
    "routing_abc": false,
    "decision_ladder": false,
    "visual_regression": false
  },
  "testing": {
    "layers": 3,
    "tdd_mode": "standard",
    "visual_regression": false
  },
  "ci": {
    "ai_reviewer": true,
    "e2e_in_ci": false,
    "auto_improve": true,
    "inline_suggestions": true
  },
  "build_plan": {
    "agents_md": false,
    "satellites": [],
    "commands": [],
    "protocols_flat": [],
    "protocols_skills": [],
    "hook": false,
    "staging_dir": ".wizard-staging",
    "generated_files": [],
    "managed_paths": [],
    "approval": {}
  }
}
```

---

## Future migrations

When adding new features or schema changes:

1. Document the migration rule in this file
2. Add implementation code in Phase R2
3. Add test case with before/after state
4. Update default values table
5. Test with archived project states
