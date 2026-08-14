# /wf-refresh Troubleshooting & Recovery

> When `/wf-refresh` encounters problems or your wizard installation is corrupted, sometimes a clean reinstall is safer than trying to patch.

## When to Use /wf-cleanup + /wf-init

If any of these apply, **STOP /wf-refresh and use `/wf-cleanup` + `/wf-init` instead:**

### 1. **Disruptive Release** (multiple breaking changes)

User is 2+ releases behind AND:
- Many files changed simultaneously
- Regeneration would touch 5+ files
- High risk of conflicts or corrupted state

**Action:**
```bash
/wf-cleanup    # Remove all wizard artifacts safely
/wf-init       # Fresh install with current state
```

### 2. **Deleted Files in Release**

If the new wizard version removed files AND:
- User has modified those files locally
- Not sure if deletion is intentional
- Better to ask user than auto-delete

**Action:**
```bash
# Show user what /wf-cleanup will remove
# Let them decide what to keep
/wf-cleanup
# Then manually restore needed files
# Finally run /wf-init
```

### 3. **Content Hash Mismatch**

If a file's content hash doesn't match what's expected:
- Corruption detected
- File may have been manually edited in conflicting ways
- Regeneration might fail or lose data

**Action:**
```bash
/wf-cleanup
/wf-init
```

### 4. **State Variable Errors**

If `/wf-refresh` fails because:
- `.wizard-state.json` is missing or corrupt
- State variables are incomplete
- Can't render templates properly

**Action:**
```bash
# Option A: Fresh install
/wf-cleanup
/wf-init

# Option B: Try to repair state (risky)
# Only if you know what you're doing
```

### 5. **Multi-Version Jump** (3+ releases behind)

User is trying to jump from 0.1.0 → 0.2.5 AND:
- Multiple intermediate releases changed critical files
- Complex file deletions/renames happened
- Safer to start fresh

**Recommendation:**
```bash
Your wizard is 3+ versions behind.
For safety, we recommend a fresh install:

/wf-cleanup   # Remove old artifacts
/wf-init      # Install latest version

This ensures no orphaned or conflicting files.
```

---

## How /wf-refresh Detects These Cases

### Hash-Based Diff

`/wf-refresh` uses SHA256 hashes to compare the Builder's staging output with the project:

```bash
# For each file in .wizard-staging/ (use wf_sha256 for macOS/BSD compatibility)
STAGING_HASH=$(wf_sha256 ".wizard-staging/$file")

if [[ -f "$file" ]]; then
  PROJECT_HASH=$(wf_sha256 "$file")
  if [[ "$STAGING_HASH" == "$PROJECT_HASH" ]]; then
    echo "unchanged: $file"
  else
    echo "update: $file"
  fi
else
  echo "add: $file"
fi
```

| Classification | Meaning |
|---------------|---------|
| `added` | File only in staging |
| `updated` | File in project and staging, but hash differs |
| `deleted` | Old managed file, no longer in staging, and project hash matches the recorded hash |
| `deleted_modified` | Old managed file, no longer in staging, but project hash differs (user edited it) |
| `unchanged` | File in project and staging with the same hash (skipped) |

### Deprecated Files Detection

`/wf-refresh` compares the previous `.wizard-managed-files.json` (derived from `.wizard-state.json` `build_plan.managed_paths`) with the newly generated staging:

- Files in old `managed_paths` but not in new staging → proposed for `deleted` or `deleted_modified`
- Files with unchanged hash → classified as `deleted` (safe to delete)
- Files with modified hash → classified as `deleted_modified` (user is warned and must approve explicitly)

### Multi-Version Detection

In `/wf-refresh` Phase R-1, versions are compared with a proper semver helper, not lexicographically:

```bash
LOCAL_VERSION=$(sed -n 's/.*wf-version: \([^ |]*\).*/\1/p' AGENTS.md | tail -1)
REMOTE_VERSION=$(curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/VERSION)

if version_lt "$LOCAL_VERSION" "$REMOTE_VERSION"; then
  echo "⚠ Wizard is outdated (local: $LOCAL_VERSION, remote: $REMOTE_VERSION)"
  read -p "Update global commands? [y/n] " -r
fi
```

`version_lt` handles `x.y.z[-prerelease[.N]]` correctly, so `0.10.0` is detected as greater than `0.6.8-beta` and `0.6.10` is greater than `0.6.8`.

---

## What /wf-cleanup Does (Safe)

**Removes:**
- ✅ Wizard skills (but NOT gentle-ai skills like sdd-*)
- ✅ Wizard commands (/wf-refresh, /wf-settings, etc.)
- ✅ Wizard satellites (CLAUDE.md, GEMINI.md)
- ✅ Wizard CI/CD workflows (release-please, quality-guard, etc.)
- ✅ .wizard-state.json
- ✅ .wf-status
- ✅ .wizard-managed-files.json

**Preserves:**
- ✅ Project code
- ✅ gentle-ai files (MCPs, OpenSpec, Engram)
- ✅ Your AGENTS.md custom sections
- ✅ User configuration files
- ✅ User-created skills

**Safety Features:**
- ✅ Shows complete inventory before deleting
- ✅ Asks confirmation for each group
- ✅ Never deletes without user consent
- ✅ Preserves gentle-ai installations

---

## Decision Tree

```
/wf-refresh fails or seems wrong?
│
├─ Is it a simple file update?
│  └─ Continue with /wf-refresh
│
├─ Multiple files changed, some deleted?
│  └─ Run: /wf-cleanup && /wf-init
│
├─ User is 3+ releases behind?
│  └─ Run: /wf-cleanup && /wf-init
│
├─ Content hash mismatch (corrupted)?
│  └─ Run: /wf-cleanup && /wf-init
│
└─ State is broken/missing?
   └─ Run: /wf-cleanup && /wf-init
```

---

## Flow: When to Recommend Cleanup

In `/wf-refresh` Phase R4 (Diff and Plan):

```bash
ADDED_COUNT=$(jq '.added | length' refresh-plan.json)
UPDATED_COUNT=$(jq '.updated | length' refresh-plan.json)
DELETED_COUNT=$(jq '.deleted | length' refresh-plan.json)

if [[ $DELETED_COUNT -gt 2 ]] || [[ $((ADDED_COUNT + UPDATED_COUNT)) -gt 5 ]]; then
  echo "⚠ This update is complex (many additions, updates, or deletions)"
  echo ""
  echo "For safety, consider:"
  echo "  1. /wf-cleanup"
  echo "  2. /wf-init"
  echo ""
  echo "Continue with /wf-refresh? [yes/no]"
  read -p "Your choice: " choice
  
  if [[ "$choice" != "yes" ]]; then
    echo "Run /wf-cleanup when ready to start fresh"
    exit 0
  fi
fi
```

---

## Notes

- **Don't force users**: Always ask, never auto-cleanup
- **Document the reason**: Tell user WHY cleanup is safer
- **Offer recovery**: If /wf-refresh fails, offer /wf-cleanup + /wf-init path
- **wf-cleanup is safe**: It's designed to preserve project work
- **/wf-init is idempotent**: Running it twice is safe
- **Builder is single source of truth**: /wf-refresh reuses /wf-init Builder (B1-B9)
- **Custom sections are preserved**: Content inside `<!-- WF: DO NOT REGENERATE -->` markers is kept
