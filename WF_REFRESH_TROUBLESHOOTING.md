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

### 2. **Deleted Files in Release** (_deleted_files in manifest)

If the manifest shows deleted files AND:
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

If a file's content_hash doesn't match what's expected:
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
echo "Your wizard is 3+ versions behind."
echo "For safety, we recommend a fresh install:"
echo ""
echo "/wf-cleanup   # Remove old artifacts"
echo "/wf-init      # Install latest version"
echo ""
echo "This ensures no orphaned or conflicting files."
```

---

## How /wf-refresh Detects These Cases

### Content Hashes (WIZARD_MANIFEST-*.json)

Each file includes SHA256 hash of content:

```json
{
  "files": {
    "release-please": {
      "content_hash": "abc123def456...",
      "status": "changed"
    }
  }
}
```

If downloaded file's hash ≠ manifest hash:
- File was modified outside /wf-refresh
- Regeneration might conflict
- **Warn user: offer /wf-cleanup option**

### Deleted Files (_deleted_files in manifest)

```json
{
  "_deleted_files": {
    "files": [
      ".github/workflows/old-ci.yml",
      ".agents/protocols/deprecated.md"
    ]
  }
}
```

If manifest shows deleted files:
- /wf-cleanup will ask about each one
- User decides whether to keep or remove
- Safer than auto-delete

### Multi-Version Detection

In `/wf-refresh` Phase -1:

```bash
LOCAL_VERSION=$(grep "wf-version:" AGENTS.md)      # 0.1.0
REMOTE_VERSION=$(curl .../VERSION)                   # 0.2.5
VERSION_GAP=$((REMOTE_VERSION - LOCAL_VERSION))     # 3 releases

if [ "$VERSION_GAP" -gt 2 ]; then
  echo "⚠️ WARNING: Jump of $VERSION_GAP releases"
  echo "For safety, consider: /wf-cleanup && /wf-init"
  echo "Continue anyway? [yes/no]"
fi
```

---

## What /wf-cleanup Does (Safe)

**Removes:**
- ✅ Wizard skills (but NOT gentle-ai skills like sdd-*)
- ✅ Wizard commands (/wf-refresh, /wf-settings, etc.)
- ✅ Wizard satellites (CLAUDE.md, GEMINI.md)
- ✅ Wizard CI/CD workflows (release-please, quality-guard, etc.)
- ✅ .wizard-state.json
- ✅ .wf-status

**Preserves:**
- ✅ Project code
- ✅ gentle-ai files (MCPs, OpenSpec, Engram)
- ✅ Your AGENTS.md custom sections
- ✅ User configuration files

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

## Flow: When to Recommend

In `/wf-refresh` **Phase 2** or **Phase 3**:

```bash
# After manifest analysis
DELETED_COUNT=$(jq '.[] | select(.status=="deleted") | length' MANIFEST)
CHANGED_COUNT=$(jq '.[] | select(.regenerate==true) | length' MANIFEST)

if [ "$DELETED_COUNT" -gt 2 ] || [ "$CHANGED_COUNT" -gt 5 ]; then
  echo "⚠️ This update is complex (many deletions or regenerations)"
  echo ""
  echo "For safety, consider:"
  echo "  1. /wf-cleanup"
  echo "  2. /wf-init"
  echo ""
  echo "Continue with /wf-refresh? [yes/no]"
  read -p "Your choice: " choice
  
  if [ "$choice" != "yes" ]; then
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
