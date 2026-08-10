## PHASE 2 — Migration of previous artifacts

If previous workflow artifacts with **own content** exist (not empty stubs nor current wizard templates):

```
I found previous workflow artifacts with customized content:
  <brief list of each one's content>

What should I do with them?
  [migrate] — I'll try to preserve the custom content in the new files.
  [replace] — I'll overwrite them completely with new templates.
  [review first] — Show me each file before I decide.
```

**PAUSE — Wait for response.**

If no previous artifacts with own content exist: tell the user and continue to Phase 3 directly.

### Step 2.2 — Mark custom content for automatic protection

**Only if the user chose "migrate":**

If `.wizard-state.json` has `migration.prior_content_action = "migrate"`:

```bash
# Mark in state that custom content will be wrapped with protection markers
jq '.migration.wrap_custom_in_markers = true' .wizard-state.json > /tmp/state.tmp
mv /tmp/state.tmp .wizard-state.json
```

Inform the user:

```
✓ Migration plan saved.

Your custom content will be automatically wrapped with protection markers:

<!-- WF: DO NOT REGENERATE -->
[your custom content]
<!-- /WF: DO NOT REGENERATE -->

This ensures your customizations are preserved when you run /wf-refresh in the future.
The markers tell the wizard: "Never touch this section, it's user-maintained."

You will see the protected content in Phase 7 before I write any files.
```

---

### Step 2.1 — Missing commands verification (mandatory in upgrades)

> **Why this step exists**: Phase 2 detects artifacts with *custom* content to
> preserve, but that is not the same as detecting *missing* commands. A
> `.claude/commands/` directory may already exist with 2 of 4 expected commands (for example, from
> an earlier wizard version that didn't include `wf-onboard` or `wf-refresh`), and the
> "custom content" logic doesn't detect it as incomplete because it's not looking for
> absences — only presences with own content. This step fixes that gap.

For each active IDE in the project (detected in Phase 2 or confirmed in Phase 0c),
check file by file — not just whether the directory exists:

```bash
# List of commands expected by this wizard version (update every
# version that adds new commands)
EXPECTED_COMMANDS="wf-ladder wf-onboard wf-worktree wf-settings"

# Example verification for Claude Code — repeat the pattern for each
# active IDE, adjusting directory and extension based on its format:
for cmd in $EXPECTED_COMMANDS; do
  if [ ! -f ".claude/commands/${cmd}.md" ]; then
    echo "FALTA: .claude/commands/${cmd}.md"
  fi
done
```

Apply the same pattern to each active IDE, adjusting path and extension:

| IDE | Base path | Extension |
|---|---|---|
| Claude Code | `.claude/commands/` | `.md` |
| Cursor | `.cursor/commands/` | `.md` |
| Windsurf | `.windsurf/workflows/` | `.md` |
| Kiro | `.kiro/steering/` | `.md` (caution: this directory mixes satellites `inclusion: always` with commands `inclusion: manual` — verify by filename, don't assume everything there is a satellite) |
| OpenCode | `.opencode/commands/` | `.md` |
| Copilot | `.github/prompts/` | `.prompt.md` |

If the `EXPECTED_COMMANDS` of this wizard version differs from the one the previous
detected version had (for example, an upgrade that added `wf-onboard` and
`wf-refresh` as new commands), tell the user:

```
Command verification — <IDE>:
  ✓ wf-ladder.md
  ✗ wf-onboard.md   ← missing (new in this wizard version)
  ✗ wf-refresh.md   ← missing (new in this wizard version)

Although the directory already existed, 2 commands from the current version are missing.
I will add them in Phase 8 without touching the existing ones that have their own content.
```

**Rule for the executing agent**: never assume a commands directory is
complete just because it exists or because it contains *some* of the expected files.
Always verify the full list, file by file, for each active IDE. This
check is repeated in every future wizard version that adds new commands —
keeping `EXPECTED_COMMANDS` updated is the wizard maintainer's responsibility.

---
> **⛔ STOP HERE — do not execute anything else.**
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `migration.prior_content_action` (migrate/replace/review) and `migration.missing_commands` (the ones detected as missing). Mark `wf_phase_done phase2 phase3`.
> Tell the user: *"Migration reviewed. Reply **continue** when you're ready for project classification."*
> Wait for the response. Only when they confirm, run in bash: `cat "$WF_DIR/phase3.md"`
