## PHASE 4.5 — SDD Initialization (`/sdd-init`) — conditional

> **Gate**: runs only if `features.routing_abc == true` or `features.tdd_protocol == true`.
> Otherwise, skip to the next applicable phase.

```bash
# WF_DIR fallback before sourcing (only phase that sourced without it).
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

FEATURES_ROUTING=$(jq -r '.features.routing_abc // false' .wizard-state.json)
FEATURES_TDD=$(jq -r '.features.tdd_protocol // false' .wizard-state.json)
if [ "$FEATURES_ROUTING" != "true" ] && [ "$FEATURES_TDD" != "true" ]; then
  echo "Phase 4.5 skipped — SDD not required (no ABC Routing nor TDD Protocol)."
  NEXT=
  if [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
    NEXT="phase47-cicd"
  else
    NEXT="phase5"
  fi
  wf_phase_done phase45 "$NEXT"
  echo "ℹ Next phase: $NEXT"
  cat "$WF_DIR/$NEXT.md"
  exit 0
fi
```

---

### Windsurf-specific fix (if applicable)

**Before SDD initialization**, check if Windsurf (or Devin) is in the project's active IDEs and apply
the gentle-ai compatibility workaround:

```bash
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  WINDSURF_ACTIVE=true
else
  WINDSURF_ACTIVE=false
fi
```

**If Windsurf is active** (`WINDSURF_ACTIVE=true`):

1. **Merge the AGENTS.md rule** (read temp-files/AGENTS.md and fuse into the project's AGENTS.md):
   - If `AGENTS.md` does NOT exist (greenfield — the Builder generates it later in Phase 6):
     copy the whole file `$WF_DIR/temp-files/AGENTS.md` → `AGENTS.md`. That file IS the
     "Gentle AI — Legacy Path Bridge for Windsurf/Devin" rule and must exist before
     `/sdd-init` runs in the new Windsurf session.
   - If `AGENTS.md` already exists (legacy project): read the rule from
     `$WF_DIR/temp-files/AGENTS.md` (the **Gentle AI — Legacy Path Bridge for Windsurf/Devin** section),
     insert it at the top (after the title and before other content) so it loads first, and save.
   - Verify the rule is present: `grep -q "Gentle AI — Legacy Path Bridge" AGENTS.md`.
     If it is not, fix it before continuing.

   **Why**: gentle-ai installs SDD skills into Windsurf's legacy paths (`~/.codeium/windsurf/skills/`), not the Devin paths. This rule tells the agent where to find them. Without it, sdd-init will not load the skills correctly in Windsurf. Phase 45 runs BEFORE the Builder (Phase 6) creates AGENTS.md, so a greenfield project needs the rule file created here directly.

2. **Create `.windsurf/workflows/sdd-new.md`** (to replace the legacy version):
   - If `.windsurf/workflows/` does not exist, create it.
   - Write the content from `$WF_DIR/temp-files/sdd-new.md` to `.windsurf/workflows/sdd-new.md`.
   - Adapt the file to use the actual SDD backend chosen by the user (read from `state.sdd.backend`).

```bash
SDD_BACKEND=$(jq -r '.sdd.backend // "hybrid"' .wizard-state.json)
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
SDD_PATH="$SDD_BACKEND"
[ "$SDD_BACKEND" = "hybrid" ] && SDD_PATH="openspec"
mkdir -p .windsurf/workflows
cp "$WF_DIR/temp-files/sdd-new.md" .windsurf/workflows/sdd-new.md
if [ "$SDD_BACKEND" = "engram" ]; then
  sed -i.bak "s|{{sdd.backend}}/changes/<name>/proposal.md|Engram memory:|g" .windsurf/workflows/sdd-new.md
else
  sed -i.bak "s|{{sdd.backend}}/changes/|$SDD_PATH/changes/|g" .windsurf/workflows/sdd-new.md
fi
sed -i.bak "s/{{sdd.backend}}/$SDD_BACKEND/g" .windsurf/workflows/sdd-new.md
rm -f .windsurf/workflows/sdd-new.md.bak
```

Tell the user:

```
⚙️ Windsurf compatibility setup:
  ✓ AGENTS.md: gentle-ai Windsurf paths rule in place (created if it did not exist)
  ✓ Created .windsurf/workflows/sdd-new.md (modern SDD workflow)

This is a temporary workaround for a gentle-ai bug with Windsurf. The agent will now
be able to find and run SDD skills correctly.

Note: After /sdd-init runs, gentle-ai sync may overwrite .windsurf/workflows/sdd-new.md
with the legacy version. If that happens, run /wf-settings → "Fix Windsurf gentle-ai" 
to reapply this fix.
```

---

This phase runs here — after reverse engineering (Phase 4) — because the wizard already knows the project: whether it's greenfield or legacy, how many committers it has, what stack it uses. With that context it can make a well-founded persistence backend recommendation instead of a generic question.

> **Note**: the official gentle-ai documentation states that the SDD orchestrator runs `/sdd-init` automatically if it doesn't detect SDD context in the project. This means that if the user starts SDD without having run `/sdd-init` manually, the orchestrator does it on its own — but it will use its defaults (likely engram). Wizard Phase 4.5 ensures the backend choice is deliberate, not a silent default.

**If `openspec/config.yaml` already exists**, read the current backend and display:

```
SDD was already initialized in this repo.
  Current backend: <backend detected from config>
  openspec/config.yaml ✓
  openspec/changes/ ✓
  openspec/specs/ ✓

Official documentation recommends re-running /sdd-init when the project's
capabilities change: testing tools, core dependencies, team size, or stack.
The post-commit hook installed in Phase 8 will notify you when that happens.

Do you want to refresh the configuration now? [yes / no, continue]
```

If the user says "no, continue": skip to the end of this phase.
If "yes": continue with the backend selection below.

**If `openspec/config.yaml` does NOT exist**, proceed directly to backend selection.

---

### Persistence backend selection

Before running `/sdd-init`, the user must choose the backend. To make the right recommendation, the wizard evaluates the project context discovered in Phases 1-4:

```bash
# How many unique committers in the history?
# CRITICAL: must use explicit `HEAD` and `< /dev/null` — without this, `git shortlog`
# in a repo with no commits waits for stdin input indefinitely instead of failing fast,
# hanging the wizard without warning.
# Confirmed reproducible: exit code 124 (timeout) without this fix.
git shortlog -sne HEAD < /dev/null 2>/dev/null | wc -l

# Is CI configured?
ls .github/workflows/ 2>/dev/null | wc -l
```

If the previous command returns `0`, it's a repo with no commits yet (not a detection error) — treat it as the "greenfield without committers" case from the table below, not as a wizard-stopping failure.

The wizard uses this information to prefill the recommendation in the message to the user.

Always present all three options in full — the user decides, not the wizard. The wizard only indicates which one it recommends based on context:

```
To initialize SDD in this project, I need to know which persistence backend
to use. Here are the three options with their real implications:

────────────────────────────────────────────────────────────────
1. engram — Local memory, no files in the repo

   HOW IT WORKS: Each SDD phase (sdd-propose, sdd-spec, sdd-design, etc.) saves
   decisions and context in Engram, which is a local SQLite database on your
   machine (~/.engram/). Later phases query Engram to have context
   of what was decided before. When you close the session, the context persists.
   When you open the project on another machine, there is no context.

   ADVANTAGES:
   - No file noise in the repo (openspec/ is not created).
   - Automatic cross-session memory without thinking about commits.
   - Simple if you always work on the same machine.

   DISADVANTAGES:
   - SDD context lives ONLY on your machine. Other developers can't see it.
   - Official gentle-ai warning: engram-only does NOT maintain canonical
     versionable specs. There is no merge layer to sync decisions to files.
   - If you switch machines or clean ~/.engram/, you lose accumulated context.
   - Migrating to hybrid later is possible but the Engram history does not
     transfer retroactively to the repo — old decisions remain local only.

   WHEN TO CHOOSE: throwaway project, personal learning, or if you are
   certain you will always work alone on the same machine indefinitely.

────────────────────────────────────────────────────────────────
2. openspec — Versioned files in the repo, no Engram

   HOW IT WORKS: Each SDD phase generates and reads files in openspec/:
   config.yaml, specs/<domain>/spec.md, changes/<change-id>/. Files are
   committed to the repo. sdd-sync merges a change's deltas into the canonical
   spec. sdd-archive moves the complete change to history under
   changes/archive/. The agent reads those files at the start of each session
   to have context.

   ADVANTAGES:
   - All SDD context lives in git: full history, blame, PRs, code review.
   - Any developer with repo access has access to SDD context.
   - Does not require Engram installed on any machine.
   - Auditable: you can see exactly what was decided, when, and in which commit.

   DISADVANTAGES:
   - No automatic cross-session persistent memory: each session the agent reads
     files, it doesn't "remember" — it works fine but is less fluid than Engram.
   - Adds files to the repo that need maintenance (openspec/ can grow).

   WHEN TO CHOOSE: team where not everyone has Engram installed, or if you
   prioritize SDD context being an explicit and audited artifact in git.

────────────────────────────────────────────────────────────────
3. hybrid — Versioned files + Engram memory (recommended)

   HOW IT WORKS: Combines openspec and engram. SDD phases generate files in
   openspec/ (which get committed) AND save context in local Engram. Files
   provide the canonical and shared layer; Engram provides the fast
   cross-session memory layer. If Engram is not available, openspec works
   as fallback.

   ADVANTAGES:
   - Best of both modes: versioned specs + fluid memory.
   - If the team grows, new developers only need to clone the repo —
     specs are already in openspec/. Engram is a plus for each developer.
   - No migration required if the team grows or if someone works without
     Engram at any given time.

   DISADVANTAGES:
   - Requires Engram installed and running on each machine that wants to use
     persistent memory (without Engram, it works as pure openspec).
   - Adds files to the repo just like openspec.

   WHEN TO CHOOSE: most cases. Even if you start alone, hybrid
   is the option that generates the least friction in the future.

────────────────────────────────────────────────────────────────

<IF the project has more than 1 active committer in its history>:
  Wizard recommendation: option 3 (hybrid) — there is more than one committer
  in the history, suggesting current or future team work.

<IF the project is greenfield without committers or just-you>:
  Wizard recommendation: option 3 (hybrid) if you plan to grow, option 1
  (engram) if it's just for learning or using on your machine.

What backend do you choose? [1 / 2 / 3]
```

**If the user chooses 1 (engram)**, ask for explicit confirmation:

```
You chose engram. Confirmation before continuing:

  ✗ No openspec/ files will be created in the repo
  ✗ Other developers won't be able to see SDD context
  ✗ Decision history stays only in ~/.engram/ on your machine
  ✗ Migrating to hybrid later is possible but history won't transfer

Do you confirm? [yes, I understand and accept / no, I prefer hybrid]
```

If the user switches to hybrid, use that option.

---

### Running `/sdd-init` (gentle-ai skill)

`/sdd-init` is a **gentle-ai skill**, not a terminal command. `gentle-ai sdd-init` does not exist as a CLI subcommand. The wizard **does not install** `/sdd-init` as a command — it is a native gentle-ai skill.

> **⛔ BLOCKING RULE (read the full `sdd` protocol)**:
> it is **FORBIDDEN** to read `SKILL.md` from sdd-init to replicate its steps manually, or to create `openspec/config.yaml`, `openspec/specs/`, `openspec/changes/` or any SDD artifact yourself. Creating them manually silently corrupts the initialization (it fails only at `sdd-apply`/`sdd-verify`).
>
> **Exception**: reading the SKILL.md file to delegate execution to a sub-agent
> executor is permitted — this is necessary for Path A to work.
>
> At the slightest doubt about whether it worked → apply this rule, don't improvise.

Read from the current state to build the exact prompt with resolved values:

```bash
SDD_BACKEND=$(jq -r '.sdd.backend // "hybrid"' .wizard-state.json)
TDD_MODE=$(jq -r '.testing.tdd_mode // "standard"' .wizard-state.json)

if [ "$TDD_MODE" = "strict" ]; then
  STRICT_TDD="enabled"
else
  STRICT_TDD="disabled"
fi
```

If `testing.tdd_mode` is not in the state (phase 46 hasn't run yet), the prompt assumes "standard" = Strict TDD disabled, which is the wizard default.

---

**Required: Run `/sdd-init` in a NEW session**

The wizard has just written the new rules and skills to your IDE's configuration. For those
to be loaded correctly by gentle-ai's own orchestrator, **sdd-init MUST run in a fresh session**
where the new context is available. Running it in the current session would use the old (or 
missing) context.

Do NOT try to delegate sdd-init inline in this conversation. Instead:

Show the user this message:

```bash
SDD_BACKEND=$(jq -r '.sdd.backend // "hybrid"' .wizard-state.json)
TDD_MODE=$(jq -r '.testing.tdd_mode // "standard"' .wizard-state.json)
if [ "$TDD_MODE" = "strict" ]; then STRICT_TDD="enabled"; else STRICT_TDD="disabled"; fi

cat <<MESSAGE
To continue, you need to initialize SDD with this configuration.

⚠️ IMPORTANT — OPEN A NEW SESSION/CHAT:

  1. Open a NEW chat/session in your IDE/CLI — do NOT run this in the current
     wf-init session. The wizard has just written new rules and skills to your
     IDE configuration; they only load in a fresh session.
  2. In that NEW session, say exactly:

       Initialize the gentle-ai sdd-init skill in ${SDD_BACKEND} mode with Strict TDD ${STRICT_TDD}

  3. When the skill finishes and you see openspec/config.yaml, openspec/changes/,
     and openspec/specs/ were created, return to THIS session and reply **continue**
     so I can verify and proceed.

Important notes:
- `/sdd-init` is a gentle-ai skill, not a terminal command. If your IDE supports it, you can try
  `/sdd-init` as a slash command. If not, say exactly: "Initialize the gentle-ai sdd-init skill
  in ${SDD_BACKEND} mode with Strict TDD ${STRICT_TDD}".
- Some adapters (e.g., Codex/ChatGPT) may not have slash command support — use the plain 
  language instruction instead.
- If your IDE is Windsurf/Devin: verify the project AGENTS.md contains the
  "Gentle AI — Legacy Path Bridge for Windsurf/Devin" rule BEFORE opening the new
  session (the wizard applies it in this phase).
MESSAGE
```

**Wait for explicit confirmation from the user** that `/sdd-init` ran in a new session and finished. 
Do not continue or verify files until they confirm. When they reply "continue", proceed to verification.

---

### Verification (runs after Path A or Path B)

```bash
ls openspec/config.yaml openspec/changes openspec/specs 2>/dev/null
cat openspec/config.yaml
```

All three must exist. Show the `config.yaml` contents to the user so they can see and confirm it reflects their choice. If there is any problem:

```
SDD initialization was not completed. Missing: <list of what's missing>.

Possible causes:
- /sdd-init failed silently (check the IDE output)
- gentle-ai install did not configure SDD slash commands for this agent
- Write permissions in the project directory

Solution: run `gentle-ai doctor` to verify the skill is available, then
open a **NEW** session/chat and say:

  Initialize the gentle-ai sdd-init skill in **<SDD_BACKEND>** mode and
  Strict TDD **<STRICT_TDD>**

Replace <SDD_BACKEND> and <STRICT_TDD> with your configuration values.

When it finishes, come back and confirm so the wizard can continue.
```

> **Do NOT manually complete the missing files** (BLOCKING RULE from the `sdd` protocol): even if only one is missing, creating it manually leaves `openspec/` inconsistent. Stop the wizard and wait for the user to run `/sdd-init` in a new session.

Stop the wizard until the verification passes.

### ✓ PHASE 4.5 COMPLETED

```
SDD initialized:
  Backend: <chosen backend>
  openspec/config.yaml ✓
  openspec/changes/ ✓
  openspec/specs/ ✓

The post-commit hook (Phase 8) will detect structural changes that warrant
re-running /sdd-init and will notify in .wf-status.

Continuing with project questions...
```

**PAUSE — Wait for "continue" or "yes" to move to the next phase (depending on features).**

---
> **⛔ STOP HERE — do not execute anything else.**
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `sdd.backend` (`engram`|`openspec`|`hybrid`) and `sdd.already_initialized`. Mark `wf_phase_done phase45 <next>`.
> Calculate the next phase based on features: `phase46` if `features.tdd_protocol = true`; else `phase47-cicd` if `features.ci`, `features.cd`, or `features.release_please` is true; else `phase5`.
> Tell the user: *"SDD initialized. Reply **continue** when you are ready to proceed."*
> Wait for the response. Only when they confirm, run in bash:
```bash
NEXT=
if [ "$(jq -r '.features.tdd_protocol // false' .wizard-state.json)" = "true" ]; then
  NEXT="phase46"
elif [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
  NEXT="phase47-cicd"
else
  NEXT="phase5"
fi
wf_phase_done phase45 "$NEXT"
echo "ℹ Next phase: $NEXT"
cat "$WF_DIR/$NEXT.md"
```
