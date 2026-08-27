## PHASE 6 — Deterministic assembly (part A: Builder-Core)

> This phase assembles operations B1-B6: AGENTS.md, packaged protocols, and per-IDE
> satellites into `.wizard-staging/`. Builder-Core is a deterministic Python script —
> no sub-agent delegation, no inline fallback.

### Step 1: Run Builder-Core (deterministic script)

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

python3 "$WF_DIR/lib/builder-core.py" \
  --state ".wizard-state.json" \
  --staging ".wizard-staging" \
  --raw "${WF_RAW:-https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main}" \
  --wf-dir "$WF_DIR"
```

- `--state` → `.wizard-state.json` (project root; the script writes back `build_plan`).
- `--staging` → `.wizard-staging`.
- `--raw` → the wizard raw base (same as `WF_RAW` used by `/wf-init`).
- `--wf-dir` → the downloaded phase directory (`$WF_DIR`).
- The script implements B1-B6: AGENTS.md router, protocols, skills, satellites.
  It exits non-zero on any unresolved placeholder or missing template.

### Step 2: (removed — deterministic script replaces delegation)

Builder-Core is executed exclusively via the Python script in Step 1. There is no
sub-agent or manual inline path anymore; `_archive/subagent-builder-core.md` and
`lib/builder.md` are kept only as specification references.

### Step 3: Validation — verify staging was populated

Validate that `.wizard-staging/` was created and contains expected files:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

if [ ! -d .wizard-staging ]; then
  echo "ERROR: .wizard-staging/ was not created."
  echo "This means Builder-Core (B1-B6) did not complete successfully."
  echo ""
  echo "Troubleshooting:"
  echo "  1. Check .wizard-state.json is valid: cat .wizard-state.json | jq ."
  echo "  2. Re-run the Step 1 script and check stderr for unresolved placeholders"
  echo ""
  echo "Re-run with: cat \"$WF_DIR/phase6a-agents.md\""
  exit 1
fi

echo "=== Staging directory created ==="
find .wizard-staging -type f | wc -l
echo "files in .wizard-staging/"

# Verify key artifacts exist (.wizard-state.json stays at the project root,
# never in staging — staging holds only generated files)
for artifact in AGENTS.md; do
  if [ ! -f ".wizard-staging/$artifact" ]; then
    echo "ERROR: Missing critical artifact: .wizard-staging/$artifact"
    echo "Builder-Core did not complete correctly. Check steps above."
    exit 1
  fi
done

echo "✓ Builder-Core validation passed"
```

### Step 4: Mark Builder-Core done and continue to Builder-Heavy

If validation succeeds, mark this phase done and continue with part B:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Validate state before phase transition
jq -e '.build_plan.generated_files != null and .build_plan.managed_paths != null' .wizard-state.json || { echo "FAIL: build_plan validation failed"; exit 1; }

echo "✓ Phase 6a complete"
if [ "$WF_REFRESH" != "1" ]; then
  wf_phase_done phase6a-agents phase6b-build-heavy
  cat "$WF_DIR/phase6b-build-heavy.md"
else
  echo "ℹ Refresh mode: Builder-Heavy (B7-B9) runs separately per refresher.md R3 — do not promote phase7 here."
fi
```
