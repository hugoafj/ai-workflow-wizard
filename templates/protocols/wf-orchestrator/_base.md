# Fragment: wf-orchestrator (single entry point to this wizard's own protocols)

<!--
  wf-orchestrator is the ONLY name a model needs to remember to reach this wizard's own
  protocols. It mirrors gentle-ai's own `gentle-orchestrator` pattern (a single entry point to
  gentle-ai's sub-skills) — added because even gentle-ai's own MANDATORY guards (e.g. the SDD
  Init Guard) are not always followed when they live only as passive prompt text; a single,
  clearly-named entry point is more reliable than 3 independently-discovered skills.
  Body follows gentle-ai's own docs/skill-style-guide.md structure (Activation Contract, Hard
  Rules, Decision Gates, Execution Steps, Output Contract, References).
  Consumed by: Builder (B3/B5), packaged as a native skill per IDE (Step B4).
  DISCOVERY MECHANISM VARIES BY ADAPTER (confirmed empirically + against gentle-ai's own source,
  internal/skillregistry/registry.go):
  - Claude Code / OpenCode / Cursor / Kiro / Codex (and other adapters whose orchestrator reads
    `.atl/skill-registry.md` before delegating): ALSO registered there via `gentle-ai
    skill-registry refresh`, so gentle-ai's own Skill Resolver Protocol picks it up too.
  - Windsurf / Devin: gentle-ai's `ProjectSkillDirs`/`UserSkillDirs` do NOT scan `.windsurf/skills/`
    (project) or `.devin/skills/` (project or global) at all — confirmed reading gentle-ai's own
    source. Registering there is a no-op for these two adapters. Discovery instead relies entirely
    on the IDE's OWN native skill loader reading `.windsurf/skills/*/SKILL.md` /
    `.devin/skills/*/SKILL.md` directly from the filesystem — already confirmed working (Devin's
    own `<available_skills>` system block lists project skills from these exact paths without any
    registry involved). Do not claim gentle-ai's registry helps discovery for these two adapters.
-->

## Activation Contract

Load before implementing any non-trivial change. Single entry point to this project's own `wf-`
protocols — never replaces, redecides, or duplicates gentle-ai's own native routing/SDD/
delegation, which remains gentle-ai's exclusive authority.

## Hard Rules

- Never hardcode "delegate via `task()`, `spawn_agent()`, `run_subagent()`" as a universal
  mechanism, and never assert a fixed delegation capability from an IDE name alone.
- **Self-check your own actual toolset in this session** before trusting any capability label —
  yours or gentle-ai's. gentle-ai has no dedicated adapter entry for Devin (a fork that shares
  Windsurf's file paths), so its installed content for "Windsurf" may incorrectly say "no
  sub-agents" even when the running agent (Devin) genuinely has a working subagent/task tool. If a
  real subagent-launching tool is available right now, trust that over the IDE-name assumption. If
  not, execute inline as the solo executor.
- Namespace rule: everything with a `wf-` prefix belongs to THIS wizard, never to gentle-ai.
  Anything named `sdd-*` (no `wf-` prefix) belongs to gentle-ai. Never attribute one to the other.

## Hard Stop Protocol (MANDATORY ENFORCEMENT)

**Hard Stop #1 — Gate Confirmation (before ANY code write)**

Before you write, edit, or generate any file for this project:

```
GATE CONFIRMATION CHECKLIST:
  ✓ wf-ladder completed (if active)                       → [✓/✗/n/a]
  ✓ wf-sdd-trigger shown and user chose outcome           → [✓/✗]
  ✓ wf-preflight displayed with decision visible          → [✓/✗]
  ✓ wf-tdd ritual DONE (if active) — NO SKIPPING          → [✓/✗/n/a]

IF ALL are ✓: proceed to implementation
IF ANY is ✗ or not confirmed: STOP. Wait for explicit user confirmation.
If any feature is active, it MUST be completed (✓) — no exceptions or skipping.
```

**Exception**: None. This applies to wf-no-sdd (trivial/straightforward), wf-force-sdd (complex), all changes, all complexity levels.

**Hard Stop #2 — Skill Protocol Fidelity (if sdd-*)**

If the user invokes any `sdd-*` skill (sdd-new, sdd-explore, sdd-apply, sdd-verify, sdd-archive, etc.):

```
SKILL PROTOCOL CONTRACT:
  ✓ Read the skill's SKILL.md completely        → [done/not done]
  ✓ Execute the skill's steps EXACTLY as written → [following/not following]
  ✓ Do NOT shortcut, merge, or reorder steps     → [compliant/violating]
  ✓ Do NOT draft artifacts manually             → [respecting/bypassing]

**CRITICAL — if `wf-tdd` is active AND this is SDD (wf-force-sdd route)**:
  ✓ TDD PREFLIGHT issued and confirmed BEFORE sdd-apply → [✓/✗]
  
  If TDD is active and you chose force-SDD, you MUST run wf-tdd BEFORE sdd-apply.
  The TDD ritual (TDD PROPOSAL in standard mode) is part of the skill workflow.
  Do NOT skip it or run sdd-apply before completing wf-tdd.

IF you cannot or will not follow the skill 100%: STOP.
Say "I cannot run this skill as written because [reason]" and wait for user decision.
Do NOT run it partially or your own way.
```

**Enforcement**: Both hard stops must be visibly satisfied in your response BEFORE any file write, edit, or skill invocation. No silent skipping.

## Decision Gates

| This project has active | Load, in order |
|---|---|
| `wf-ladder` feature | 1. `wf-ladder` (anti-over-engineering, declared first) |
| always | 2. `wf-sdd-trigger` (decides `wf-no-sdd`/`wf-force-sdd`, emits `wf-preflight`, asks for confirmation) |
| `wf-tdd` feature | 3. `wf-tdd` (at the point `wf-sdd-trigger`'s outcome indicates) |

Skip a step only if its feature is not active for this project.

## Execution Steps

1. Load this skill before starting any non-trivial implementation task.
2. Walk the Decision Gates table above, in order, loading only the active protocols.
3. After `wf-ladder` (if active), pause explicitly and wait for the user to review and confirm
   the ladder rungs before continuing to `wf-sdd-trigger`.
4. After `wf-sdd-trigger`, if the user confirms the outcome:
   - **If `wf-no-sdd`**: proceed to `wf-tdd` (if active) or directly to implementation.
   - **If `wf-force-sdd`**: invoke the gentle-ai SDD pipeline (sdd-new/propose/spec/design/tasks). After sdd-tasks completes, ALWAYS invoke `wf-tdd` (if active) to emit TDD PROPOSAL BEFORE proceeding to sdd-apply. This is mandatory — do not skip wf-tdd or run sdd-apply without TDD confirmation.
5. No additional checklist or combined precheck is emitted — the ladder rungs (if active) and the
   `wf-preflight` block are sufficient before proceeding.

## Output Contract

Ladder rungs (if active) with an explicit pause for user confirmation, then the `wf-preflight`
block with its own confirmation request. Exact formats defined in `wf-ladder` and `wf-sdd-trigger`.

## References

- `wf-ladder` — anti-over-engineering discipline (7 rungs).
- `wf-sdd-trigger` — this project's own SDD-forcing policy and `wf-preflight`.
- `wf-tdd` — TDD ritual.
