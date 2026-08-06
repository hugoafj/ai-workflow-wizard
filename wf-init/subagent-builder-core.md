# Sub-agent Builder-Core — runs B1-B6

You are a Builder agent. Your job is to assemble AGENTS.md router, packaged protocols, and per-IDE satellites into a staging directory on disk, using `.wizard-state.json` as the single source of truth.

## Context

- `PROJECT_PATH`: absolute path to the target project
- `WF_PATH`: absolute path to the workflow wizard repo
- `WF_STATE`: `{PROJECT_PATH}/.wizard-state.json`
- `WF_STAGING`: `{PROJECT_PATH}/.wizard-staging/`
- `WF_RAW`: `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`
- `TEMPLATES`: `{WF_PATH}/templates/`

## Universal extraction rule

All template files (`.tmpl.md`, `.yml.md`, `.json.md`) may contain code wrapped in markdown blocks (```` ```yaml ````, ```` ```json ````, ```` ```typescript ````, ```` ```bash ````). When writing a target file, extract ONLY the content INSIDE the code block, without fencing or prose markdown.

Exception: `.tmpl.md` templates WITHOUT code fence (like `vitest.config.tmpl.md`) have raw content with possible `# prose header` lines at the start. Strip those lines — the real content starts after them.

## Instructions

### 0. Setup

```bash
source "{WF_PATH}/wf-init/lib/state.md"
mkdir -p "{WF_STAGING}"
cd "{PROJECT_PATH}"
cat .wizard-state.json
```

### B1 — Cargar estado

Read the full `.wizard-state.json`. Verify that required fields exist. If any are missing, STOP and report what's missing — don't invent defaults.

### B2 — Resolve selection keys

```bash
STACK=$(jq -r '.discovery.stack_key' .wizard-state.json)
IDES=$(jq -r '.answers.ides[]' .wizard-state.json)
TDD_MODE=$(jq -r '.testing.tdd_mode' .wizard-state.json)
LAYERS=$(jq -r '.testing.layers[]' .wizard-state.json)
LADDER=$(jq -r '.features.decision_ladder' .wizard-state.json)
TDD=$(jq -r '.features.tdd_protocol' .wizard-state.json)
ROUTING=$(jq -r '.features.routing_abc' .wizard-state.json)
CICD=$(jq -r '.features.ci' .wizard-state.json)
CD=$(jq -r '.features.cd' .wizard-state.json)
RELEASE=$(jq -r '.features.release_please' .wizard-state.json)
BACKEND=$(jq -r '.sdd.backend' .wizard-state.json)
```

### B3 — Assemble protocol bodies

For each active protocol, download its `_base.md` from GitHub raw and build the final body:

```
build_protocol_body(name):
  body = curl -fsSL "$WF_RAW/templates/protocols/<name>/_base.md"
  # remove only the internal header comment (first <!-- ... --> lines if any)
  # insert stack variant if exists (templates/protocols/<name>/variants/<STACK>.md)
  if exists $WF_RAW/templates/protocols/<name>/variants/<STACK>.md:
    body = body with {{VARIANT_MARKER}} replaced by that variant
  # special case tdd: variant by mode, not by stack
  if name == "tdd":
    body = body with {{TDD_MODE_VARIANT}} replaced by variants/<TDD_MODE>.md
  return body
```

Active protocols (conditional by features):
| Protocol | Active if |
|-----------|-----------|
| `decision-ladder` | LADDER==true or ROUTING==true (composition rules below) |
| `tdd` | TDD==true AND LAYERS not empty |
| `sdd` | BACKEND != null |
| `architecture` | **always** |
| `testing` | **always** |
| `cicd` | **always** |
| `ides` | **always** |
| `commands` | **always** |
| `workflow` | **always** |

**Special case decision-ladder** (three possible compositions):
- ROUTING==true AND LADDER==true: `ladder.md` + `local-orchestration.md` unified
- ROUTING==true AND LADDER==false: only `local-orchestration.md`
- ROUTING==false AND LADDER==true: only `ladder.md`
- Both false: don't build this protocol

### B3b — Preserve custom content with markers (if migrating)

**Only if `.migration.wrap_custom_in_markers = true`**:

If Phase 2 detected custom content to migrate:

1. Read the migrated custom content from `.wizard-state.json` (field: `migration.prior_artifacts_content`)
2. When writing to AGENTS.md, wrap preserved sections:
   ```markdown
   <!-- WF: DO NOT REGENERATE -->
   [custom content here]
   <!-- /WF: DO NOT REGENERATE -->
   ```
3. Update `.wizard-state.json`: `migration.custom_content_protected = true`

This ensures custom sections from the previous AGENTS.md are never accidentally overwritten by future /wf-refresh runs.

---

### B4 — Pack protocols per IDE

For each active protocol (body already built):

**1. Flat file** (universal fallback):
`{WF_STAGING}/.agents/protocols/<name>.md` = cuerpo

**2. Native skills per IDE** (only IDEs that support SKILL.md):

| IDE | Skills path |
|-----|-------------|
| `claude-code` | `{WF_STAGING}/.claude/skills/<name>/SKILL.md` |
| `kiro` | `{WF_STAGING}/.kiro/skills/<name>/SKILL.md` |
| `codex` | `{WF_STAGING}/.codex/skills/<name>/SKILL.md` |
| `windsurf` | `{WF_STAGING}/.windsurf/skills/<name>/SKILL.md`, `{WF_STAGING}/.devin/skills/<name>/SKILL.md` (both written for Windsurf/Devin compatibility) |
| `antigravity` | `{WF_STAGING}/.agents/skills/<name>/SKILL.md` |

For each native skill: download `$WF_RAW/templates/protocols/<name>/skill/SKILL.md`,
  replace `{{PROTOCOL_BODY: ...}}` with the body, write to the corresponding path (or paths for `windsurf`).

Record each file. Don't ask — write everything directly to staging.

### B5 — Assemble AGENTS.md (thin router)

1. Download `$WF_RAW/templates/AGENTS.router.md`
2. Replace ALL `{{...}}` placeholders with values from `.wizard-state.json`:
   - `{{answers.*}}`, `{{discovery.*}}`, `{{testing.*}}`, `{{features.*_yesno}}`
   - `{{wizard_version}}` → from the root field `wizard_version`
3. Resolve `<if ...>` blocks based on state
4. Insert testing sections if LAYERS is not empty
5. Build MCPs table based on STACK + LAYERS
6. Write to `{WF_STAGING}/AGENTS.md`
7. Footer: last line with `wf-version` + stack + all features as flags

### B6 — Satellites per IDE (only selected + CLAUDE.md)

**CRITICAL**: Only generate satellites (files AND directories) for IDEs actually in `IDES`.
Do NOT create empty directories for unselected IDEs.

For each IDE in IDES (and ALWAYS for CLAUDE.md), download template and write:

| IDE | Template | Destination | Notes |
|-----|----------|---------|---------|
| `claude-code` | `satellites/claude.tmpl` | `{WF_STAGING}/CLAUDE.md` | ALWAYS generated |
| `vscode-copilot` | `satellites/copilot.tmpl` | `{WF_STAGING}/.github/copilot-instructions.md` | Only if in IDES |
| `cursor` | `satellites/cursor.tmpl` | `{WF_STAGING}/.cursor/rules/project.mdc` | Only if in IDES |
| `windsurf` | `satellites/windsurf.tmpl` | `{WF_STAGING}/.windsurf/rules/project.md` | Only if in IDES |
| `kiro` | `satellites/kiro.tmpl` | `{WF_STAGING}/.kiro/steering/project-context.md` | Only if in IDES |
| `gemini-cli` | `satellites/gemini.tmpl` | `{WF_STAGING}/GEMINI.md` | Only if in IDES |
| `antigravity` | `satellites/antigravity.tmpl` | `{WF_STAGING}/ANTIGRAVITY.md` | Only if in IDES |

**Process**:
1. Always download and write `satellites/claude.tmpl` → `CLAUDE.md`
2. For each IDE in IDES: download its template, create parent directories as needed, write the file
3. Do NOT pre-create empty directories
4. Verify: `ls -la {WF_STAGING}` should show ONLY Claude.md + directories for IDEs in IDES, no empty dirs

## Expected output

```
✓ Builder-Core completado:
  - Packaged protocols: N (flat) + M (skills)
  - AGENTS.md router ready
  - Satellites generated: N
```

Don't delete the staging. Leave everything in `{WF_STAGING}` so the next sub-agent can continue.
