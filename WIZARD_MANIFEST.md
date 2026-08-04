# WIZARD_MANIFEST.json — Auto-Generated File Registry

> This document explains how the Wizard Manifest works, how it's generated, and how `/wf-refresh` uses it to keep projects up-to-date.

## Overview

**WIZARD_MANIFEST.json** is an **auto-generated inventory** of:
- Every file in the wizard (templates, scripts, hooks, workflows)
- Whether it changed since the last version
- If it needs to be regenerated (and how)
- What state variables it requires from `.wizard-state.json`

**Who generates it?** CI/CD runs automatically on every commit to `main`
**Who uses it?** `/wf-refresh` reads it to know exactly what to download and regenerate

---

## File Structure

```json
{
  "version": "0.2.0-beta.1",
  "generated_at": "2026-08-04T00:00:00Z",
  "files": {
    "post-commit": {
      "version": "0.2.0-beta.1",
      "type": "hook",
      "path": "post-commit",
      "output": ".git/hooks/post-commit",
      "status": "changed",
      "regenerate": false,
      "template": null,
      "state_vars": []
    },
    "release-please": {
      "version": "0.2.0-beta.1",
      "type": "workflow",
      "path": ".github/workflows/release-please.yml",
      "output": ".github/workflows/release-please.yml",
      "status": "bugfix",
      "regenerate": true,
      "template": "templates/protocols/cicd/variants/release-please.yml",
      "state_vars": [
        "ci.release_please",
        "ci.conventional_commits",
        "discovery.stack_key",
        "answers.project_name"
      ]
    }
  }
}
```

---

## Field Meanings

| Field | Meaning |
|-------|---------|
| `version` | Wizard version this file belongs to |
| `type` | File category: `hook`, `workflow`, `command`, `protocol`, `infrastructure`, `metadata` |
| `path` | Where the file lives in the wizard repo |
| `output` | Where `/wf-refresh` writes it in user's project (null if not written) |
| `status` | `new`, `changed`, `unchanged`, or `bugfix` (detected by CI from `git diff`) |
| `regenerate` | `true` if file must be rebuilt from template with current user state |
| `template` | Path to template file (if file is generated from template) |
| `state_vars` | Variables from `.wizard-state.json` needed to render this file |

---

## How CI Generates It

**Trigger**: Push to `main` that changes `templates/`, `wf-init/`, or wizard files

**Steps**:
1. Get previous version tag: `v0.2.0-beta.1`
2. Run `git diff v0.2.0-beta.1..HEAD` to detect changes
3. For each changed file:
   - Determine file type (protocol, command, workflow, etc.)
   - Find its template (if generated from template)
   - Extract state variables it needs from `.wizard-state.json` schema
   - Mark `regenerate=true` if it changed and is generated
4. Build manifest JSON
5. Commit manifest to main

**Example: Bug fix in release-please.yml**

```bash
# Hugo commits
git commit -m "fix(cicd): add missing permissions"

# CI detects
git diff v0.2.0-beta.1..HEAD .github/workflows/release-please.yml

# CI marks in manifest
{
  "release-please": {
    "status": "bugfix",
    "regenerate": true,
    "template": "templates/protocols/cicd/variants/release-please.yml",
    "state_vars": ["ci.release_please", "ci.conventional_commits", "discovery.stack_key"]
  }
}

# Commits manifest
git commit -m "chore: update WIZARD_MANIFEST.json"
```

---

## How /wf-refresh Uses It

**Phase 2 (Layer 2 - Mandatory changes)**:

```bash
for file in manifest.files; do
  # Download file from GitHub
  download_file(file.path)
  
  # If regenerate=true, rebuild from template
  if [ file.regenerate == true ]; then
    # Get template
    template = file.template
    
    # Get state variables from user's .wizard-state.json
    state_vars = {}
    for var in file.state_vars:
      state_vars[var] = read_from_state(var)
    
    # Regenerate file with user's current config
    regenerate_file(template, state_vars) > file.output
    
    echo "✓ Regenerated: ${file.name}"
    echo "  Reason: ${file.status}"
  fi
done
```

**Example: User runs `/wf-refresh` on 0.1.0 → upgrades to 0.2.0**

```
manifest says: release-please has regenerate=true

/wf-refresh does:
1. Read template: templates/protocols/cicd/variants/release-please.yml
2. Get state from user: 
   - ci.release_please = true
   - ci.conventional_commits = true
   - discovery.stack_key = "node-react"
   - answers.project_name = "my-app"
3. Render template with those values
4. Write to: .github/workflows/release-please.yml

Result: User has 0.2.0 release-please.yml, bug-fixed and working
```

---

## When Does CI Generate the Manifest?

- **Every commit to main** that touches:
  - `templates/**` (any protocol, command, or template)
  - `wf-init/**` (phase changes)
  - `post-commit` (hook changes)
  - `.github/workflows/**` (workflow changes)
  - `VERSION` (version bump)

- **Output**: Updated `WIZARD_MANIFEST.json` committed to main

---

## Developer Workflow

**Hugo's perspective** (no manifest edits):

```bash
# Make a change
git commit -m "fix(cicd): add permissions to release-please"

# Push to main
git push origin main

# CI automatically:
# 1. Detects the change
# 2. Updates WIZARD_MANIFEST.json
# 3. Commits manifest to main

# Result: manifest is always up-to-date, zero manual work
```

**User's perspective** (`/wf-refresh` handles rest):

```
/wf-refresh 0.2.0:
├─ Downloads manifest
├─ Sees: release-please.yml changed, regenerate=true
├─ Reads template + user's .wizard-state.json
├─ Regenerates release-please.yml with current config
└─ User has fixed, up-to-date workflow
```

---

## Future: .wizard-state.json Migrations

If a `.wizard-state.json` schema change requires migration:

```json
{
  "wizard-state": {
    "version": "0.2.0",
    "type": "schema",
    "status": "bugfix",
    "migration": "add ci.security_scanning = false",
    "affected_users": "all"
  }
}
```

`/wf-refresh` applies migration automatically.

---

## Notes

- ✅ Manifest is auto-generated — **never edit manually**
- ✅ CI detects file changes automatically — **no manual marking**
- ✅ State variables come from `.wizard-state.json` schema — **no duplication**
- ✅ `/wf-refresh` knows exactly what to regenerate — **no guessing**
- ✅ Users always get complete, correct 0.2.0 installation
