## PHASE 4.6 — Testing stack setup — conditional

> **Gate**: only runs if `features.tdd_protocol == true`.

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

FEATURES_TDD=$(jq -r '.features.tdd_protocol // false' .wizard-state.json)
if [ "$FEATURES_TDD" != "true" ]; then
  echo "PHASE 4.6 skipped — TDD Protocol not selected."
  NEXT=
  if [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
    NEXT="phase47-cicd"
  else
    NEXT="phase5"
  fi
  wf_phase_done phase46 "$NEXT"
  echo "ℹ Next phase: $NEXT"
  cat "$WF_DIR/$NEXT.md"
  exit 0
fi
```

The testing stack converts `sdd-apply` from "implement and hope it works" to "implement and the pipeline automatically verifies". Without this phase, `checks_before_done` only has `lint + build`. With this phase it adds `test`, `test:e2e`, or both depending on what the user activates.

This phase is optional but highly recommended. If the user prefers to configure it later, they can run `/wf-onboard` when they install a test runner.

First detect if there's already a test runner configured:

```bash
grep -E '"(@(playwright/test|testing-library/|vitest/)|vitest|jest|cypress|playwright)"' package.json 2>/dev/null
ls vitest.config.ts vitest.config.js jest.config.ts playwright.config.ts 2>/dev/null
```

**If a test runner already exists**: report what was found and ask if they want to add missing layers. Don't install anything without confirmation.

**If there's no test runner**, ask what layers to activate:

```
No configured testing framework detected.

Without tests, sdd-verify only runs lint + build. With tests, the SDD pipeline
automatically verifies that changes don't break existing behavior.

What testing layers would you like to configure now?

────────────────────────────────────────────────────────────
1. Unit tests — Vitest + Testing Library

   WHAT IT DOES: tests functions, hooks, and utilities in isolation.
   INSTALLS: vitest, @testing-library/react, @testing-library/user-event,
            @testing-library/jest-dom, jsdom, @vitest/ui, @vitest/coverage-v8
   GENERATES: vitest.config.ts, src/test/setup.ts
   ADDS SCRIPTS: "test", "test:ui", "test:coverage"
   CONVENTION: Component.test.tsx next to the tested file.

2. Integration tests — same stack as unit

   WHAT IT DOES: tests components with real dependencies in jsdom.
   Doesn't require a separate install — uses the layer 1 runner.
   CONVENTION: *.integration.test.tsx in src/__tests__/integration/
   Requires layer 1 to be activated.

3. E2E tests — Playwright

   WHAT IT DOES: complete flows in a real browser (Chromium by default).
   INSTALLS: @playwright/test + browsers via npx playwright install
   GENERATES: playwright.config.ts, e2e/ folder with example spec
   ADDS SCRIPTS: "test:e2e", "test:e2e:ui", "test:e2e:report"
   ENABLES: Playwright MCP so the agent controls the browser during
           sdd-apply and sdd-verify.

────────────────────────────────────────────────────────────

What do I activate? [1 / 2 / 1,2 / 1,2,3 / 3 only / none for now]
```

**Wait for user response.**

### TDD Mode (only if they activated layer 1, 2, or both)

If the user activated unit and/or integration tests, ask what TDD discipline mode they prefer. This is an exclusive choice — they don't combine, one replaces the other:

```
What TDD mode do you want for this project?

────────────────────────────────────────────────────────────
1. Standard TDD Protocol (recommended)

   The agent proposes which test layers apply to each change (according
   to a coverage matrix) and LETS YOU CHOOSE: apply the full
   suggestion, apply only unit, or skip TDD for that change if
   you decide it doesn't warrant it. Flexible, you have the final say
   on each task.

   This protocol is custom content of this workflow — the exact
   text that gets written to your AGENTS.md is documented in this
   wizard and has been tested in real usage.

2. Strict TDD Mode (native gentle-ai mechanism)

   More disciplined mode: no option to skip TDD, requires real
   evidence (RED → GREEN → REFACTOR table per task) instead
   of the agent narrating a result without having verified it. The
   `sdd-apply` skill of gentle-ai rejects the work if that evidence
   is missing or incomplete.

   IMPORTANT — unlike option 1, this is NOT content that
   this wizard writes. The real source of truth is a field in
   `openspec/config.yaml` that gentle-ai's own `sdd-apply`
   queries directly (confirmed against the actual installed skill).
   This wizard does not simulate or control the behavior itself —
   it only writes the field that activates the native mechanism.
────────────────────────────────────────────────────────────

Which do you prefer? [1 / 2]
```

**Wait for user response.**

**If they chose option 1 (Standard TDD Protocol)**: the Builder writes the standard protocol
(source `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-tdd/variants/standard.md`) in the AGENTS.md.

> **CRITICAL — reset Strict TDD if it was active (known bug)**: choosing "standard" is NOT
> enough to just write the protocol in AGENTS.md. If the project **already had Strict TDD
> activated before** (common: `openspec/config.yaml → testing.strict_tdd: true` and/or the
> Engram observation `sdd/{project}/testing-capabilities` with `Strict TDD Mode: enabled`),
> those sources **override AGENTS.md** — `sdd-apply` would still be enforced in strict even if
> the AGENTS.md says standard. Therefore, when choosing standard you must **sync all three
> sources to "no strict"**:
>
> 1. Detect the previous state:
> ```bash
> grep -q "strict_tdd: *true" openspec/config.yaml 2>/dev/null && echo "config: strict" || echo "config: ok"
> # Engram: check the project's testing-capabilities observation (Strict TDD Mode)
> ```
> 2. If `openspec/config.yaml` exists (openspec/hybrid backend), set `testing.strict_tdd: false`.
> 3. Update the Engram observation `sdd/{project}/testing-capabilities` with
>    `**Strict TDD Mode**: disabled` (same `--type config`, same project auto-detected from the
>    remote). Don't leave the old observation saying `enabled`.
> 4. Save in the state `state.testing.tdd_mode = "standard"`.
>
> Only when all three sources agree on "standard" is the mode truly applied.
> (Rule in the `wf-tdd` protocol.) If there was NO prior strict, there's nothing to reset.

**If they chose option 2 (Strict TDD Mode)**:

> **Round 7 of this verification — back to direct writing, with
> real empirical evidence**: Round 6 proposed delegating this writing to
> `/sdd-init`, assuming that skill would ask the user about Strict
> TDD or respect a marker the wizard had left beforehand. The
> maintainer tested this on a real project: `/sdd-init` **never asks**
> about Strict TDD interactively (confirmed by re-reading its own
> Decision Gates table: it only *uses* a value if it already exists, or applies an
> *automatic default* if it doesn't exist — there's no step in the skill that
> asks the user for confirmation), and furthermore **doesn't rewrite anything if
> `openspec/` already exists** — the Hard Rule of the skill explicitly says
> that if the structure is already initialized, it reports what's there and asks
> before touching it, instead of merging or updating a value. In
> practice, this means changing `strict_tdd` in an already
> initialized project by running `/sdd-init` again simply does nothing.
>
> **Fixed**: for this phase (activating Strict TDD during `/wf-init`,
> before any prior SDD initialization exists in this project),
> this wizard does write directly — as `/wf-settings` already does
> correctly, quality-tested by the maintainer. The real difference from
> what this wizard did before Round 5 is that we now know the
> exact format (confirmed against `references/init-details.md` of the
> actual skill) and write to both applicable sources, synced
> with each other — not an approximate simulation.

Always write to Engram, with the exact format from the official template
of `sdd-init` (confirmed in its `references/init-details.md`):

```bash
engram save "sdd/{project}/testing-capabilities" "## Testing Capabilities

**Strict TDD Mode**: enabled
**Detected**: $(date +%Y-%m-%d)

### Test Runner
- Command: <detected command, e.g. npm run test>
- Framework: <detected framework, e.g. vitest>

### Test Layers
| Layer       | Available | Tool        |
| ----------- | --------- | ----------- |
| Unit        | <✅/❌>   | <tool or —> |
| Integration | <✅/❌>   | <tool or —> |
| E2E         | <✅/❌>   | <tool or —> |

### Coverage
- Available: <✅/❌>
- Command: <command or —>

### Quality Tools
| Tool         | Available | Command        |
| ------------ | --------- | -------------- |
| Linter       | <✅/❌>   | <command or —> |
| Type checker | <✅/❌>   | <command or —> |
| Formatter    | <✅/❌>   | <command or —> |" \
  --project "{project-name}" --type config
```

> Use `--type config`, not `--type convention` as earlier versions of this wizard said — confirmed against `init-details.md`, the correct type for this observation is `config`. The project name is auto-detected from the git remote (normalized to lowercase) from Engram v1.11.0 — use `git remote get-url origin 2>/dev/null` to confirm it.

Additionally, if the detected backend is `openspec` or `hybrid`, update
`openspec/config.yaml` using `yq` to ensure atomic, safe YAML modification:

```bash
# Ensure the Go mikefarah/yq binary is available.
# pip3's kislyuk/yq wrapper does NOT support `yq eval ... -i`.
if ! command -v yq &>/dev/null || ! yq --version 2>/dev/null | grep -q "mikefarah"; then
  if command -v yq &>/dev/null && yq --version 2>/dev/null | grep -q "kislyuk"; then
    echo "WARNING: detected Python yq wrapper (kislyuk); it does not support 'eval -i'." >&2
  fi

  YQ_INSTALL_DIR="${HOME}/.local/bin"
  mkdir -p "$YQ_INSTALL_DIR"

  case "$(uname -s)-$(uname -m)" in
    Linux-x86_64)     YQ_BINARY="yq_linux_amd64" ;;
    Linux-aarch64|Linux-arm64) YQ_BINARY="yq_linux_arm64" ;;
    Darwin-x86_64)    YQ_BINARY="yq_darwin_amd64" ;;
    Darwin-arm64)     YQ_BINARY="yq_darwin_arm64" ;;
    *)
      echo "ERROR: unsupported platform for automatic yq install ($(uname -s)-$(uname -m))." >&2
      echo "Install Go yq from https://github.com/mikefarah/yq and re-run this step." >&2
      exit 1
      ;;
  esac

  echo "Installing Go yq (${YQ_BINARY}) to ${YQ_INSTALL_DIR}..."
  if command -v curl &>/dev/null; then
    curl -fsSL "https://github.com/mikefarah/yq/releases/latest/download/${YQ_BINARY}" -o "$YQ_INSTALL_DIR/yq"
  elif command -v wget &>/dev/null; then
    wget -q "https://github.com/mikefarah/yq/releases/latest/download/${YQ_BINARY}" -O "$YQ_INSTALL_DIR/yq"
  else
    echo "ERROR: curl or wget is required to install yq." >&2
    exit 1
  fi
  chmod +x "$YQ_INSTALL_DIR/yq"
  export PATH="$YQ_INSTALL_DIR:$PATH"

  if ! command -v yq &>/dev/null; then
    echo "ERROR: yq install to ${YQ_INSTALL_DIR} failed or the directory is not in PATH." >&2
    exit 1
  fi
fi

# Update testing.strict_tdd safely — preserves all other keys
yq eval '.testing.strict_tdd = true' -i openspec/config.yaml
```

If the backend is pure `engram`, the Engram step above is already
sufficient — there's no `openspec/config.yaml` to edit.

**Important**: Always use `yq eval ... -i` (in-place) to modify YAML, never echo/cat fragments. This ensures:
- Existing keys under `testing:` are preserved
- No formatting/indentation errors
- Idempotent: running multiple times produces the same result
- If `testing:` doesn't exist, it is created automatically

Additionally, for Claude Code and Windsurf specifically, gentle-ai
also exposes a sync flag that reflects this choice in their
global context files (`~/.claude/CLAUDE.md` or
`~/.codeium/windsurf/memories/global_rules.md`) — this is an
informational signal for the orchestrator, not the source that `sdd-apply` queries:

```bash
gentle-ai sync --strict-tdd
```

> **Accuracy note that still applies**: `gentle-ai install --strict-tdd`
> does NOT exist as a flag — confirmed with `flag provided but not defined:
> -strict-tdd` against a real installation (v1.43.3). Nor does
> `gentle-ai sdd-init` exist as a binary subcommand — confirmed against the
> actual `--help`. `/sdd-init` is a session skill with orchestrator→sub-agent
> delegation, correct for initializing `openspec/`
> in Phase 4.5 of this wizard, but does not rewrite values in an
> already-existing structure — that's why this specific phase (TDD mode
> change) writes directly, instead of delegating.

Inform the user:

```
Activated Strict TDD Mode.

Saved strict_tdd: enabled in Engram, under sdd/{project}/testing-capabilities
— confirmed that this is the first source sdd-apply queries.

<if openspec or hybrid backend>
Also wrote strict_tdd: true in openspec/config.yaml, synced
with the Engram value.

<if the active agent is Claude Code or Windsurf>
Also synced your agent's global context block
(gentle-ai sync --strict-tdd) — it's an additional signal for the
orchestrator, not the actual behavior source.

How to deactivate it later if you change your mind: use /wf-settings — it
already writes correctly to both sources in sync.
```

---
> **⛔ STOP HERE — don't execute anything else.**
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `testing.layers` (activated layers), `testing.tdd_mode` (`standard`|`strict`), `testing.runner_detected`. Mark `wf_phase_done phase46 phase46b`.
> Tell the user: *"Testing and TDD mode configured. Reply **continue** to review optional testing extras (coverage, visual regression, POM) and generate configs."*
> Wait for the response. Only when they confirm, execute in bash: `cat "$WF_DIR/phase46b.md"`
