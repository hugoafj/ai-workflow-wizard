# Protocol: TDD (Test-Driven Development)

<!--
  SINGLE SOURCE of the TDD Protocol. Written once here; wf-init (Builder),
  wf-refresh and wf-settings READ IT from this file — none embed or paraphrase it.
  Copied VERBATIM. Dual packaging: skill/SKILL.md + .agents/protocols/tdd.md.

  ASSEMBLY (applied by the Builder based on state.testing):
  - Included only if state.testing.layers has at least one layer.
  - Part 1 (intro + matrix) ALWAYS.
  - Then, if state.testing.tdd_mode == "standard": insert variants/standard.md.
    If tdd_mode == "strict": insert variants/strict.md (the standard protocol is NOT
    written; sdd-apply enforces via openspec/config.yaml → testing.strict_tdd).
  - Part 2 (Dual-loop Playwright — only if e2e layer active — + SDD Integration)
    ALWAYS when the E2E layer is active, regardless of mode.

  ===== PART 1: intro + matrix (VERBATIM phase6a 90-109) =====
-->

<if the user activated testing in Phase 4.6 (at least one layer)>:

### 🧪 TDD Protocol

Applies when testing is configured. The agent evaluates which layers are needed
based on the type of change and presents a proposal before writing any code.

> **⛔ HARD GATE — the TDD ritual always occurs, but WHEN/WHERE depends on the route
> (don't do it out of place)**: with testing configured, no production code is ever written
> without first performing the TDD ritual corresponding to the mode (the `🧪 TDD PROPOSAL`
> in standard mode; the RED→GREEN evidence in strict) and, in standard, having received the user's
> choice. **BUT the timing and place depend on the route — don't do it "just in case"
> right after finishing Preflight**:
> - **Route A**: do it after Preflight and before implementing (at the local task level).
> - **Route B/C (SDD)**: **DON'T do it in the local pre-pipeline flow** — in B/C there is no
>   direct local implementation. **BUT be careful with the mechanism (real fixed bug)**: the
>   `🧪 TDD PROPOSAL` is **interactive** (proposes coverage and waits for your choice) and `sdd-apply`
>   is a **headless sub-agent** (`user-invocable: false`: it executes and returns, cannot
>   ask you). Therefore, the proposal **CANNOT occur "inside" `sdd-apply`**. Correct flow:
>     1. Run `sdd-propose` and `sdd-tasks` first (so the tasks already exist).
>     2. In B, show the Route B lock menu (`decision-ladder`, Section 4) and its approval.
>     3. **The ORCHESTRATOR issues the `🧪 TDD PROPOSAL`** covering the tasks from `tasks.md` (in
>        batch, or grouped by phase in large changes) and **waits for your coverage choice**.
>     4. Only then delegate to `sdd-apply` with the decision **baked in the prompt** (e.g.,
>        "coverage: unit + integration + e2e") and **inject this skill (`tdd-protocol`)** under
>        `## Skills to load before work` so the sub-agent executes the RED→GREEN cycle and
>        respects the mandatory `--headed` output if it generates E2E specs.
>     5. The sub-agent executes headless and returns the summary (including the `--headed` command),
>        which the orchestrator shows you.
>   In `strict` mode **there is NO interactive proposal**: you delegate directly and `sdd-apply` loads
>   `strict-tdd.md` from `openspec/config.yaml → strict_tdd: true` (RED→GREEN enforcement headless).
>
> Summary: "mandatory" = the TDD ritual ALWAYS occurs at some point based on the route; it does NOT
> mean "always do it here and now". In Route C, here and now it is NOT issued.
>
> **What is the ritual according to the project MODE** (`state.testing.tdd_mode`):
> - **Standard mode** → the ritual IS the `🧪 TDD PROPOSAL`: the agent proposes the test
>   layers and the user chooses `[Apply]` / `[Skip TDD]`. **The agent does NOT decide to skip TDD on
>   its own** (even if it seems mechanical) — the skip is the user's EXCLUSIVE choice via the
>   block option. Omitting the block = violation.
> - **Strict mode** → **There is NO `🧪 TDD PROPOSAL` or skip option**; `sdd-apply` requires
>   real RED→GREEN→REFACTOR evidence per task and rejects the work if it's missing. (That's why, in
>   this protocol, "🧪 TDD PROPOSAL" always refers to the standard mode mechanism.)
> - Self-correction instruction: if you find yourself writing/editing production code
>   without having performed the TDD ritual corresponding to the mode (PROPOSAL in standard; evidence in
>   strict), STOP and do it first.

#### Coverage matrix by change type

| Change type | Unit | Integration | E2E |
|---|---|---|---|
| Logic in hook or `lib/` | ✓ | — | — |
| Component with its own state | ✓ | optional | — |
| Multi-component flow | — | ✓ | — |
| Complete user feature | — | ✓ | ✓ |
| Bug fix with possible regression | based on origin | — | — |
| Pure UI/styles | — | — | — |

The matrix is a guideline. If there is logic that could break silently and
the table does not cover it, the agent proposes tests anyway.

<!-- {{TDD_MODE_VARIANT: protocols/tdd/variants/<standard|strict>.md}} -->

<!-- ===== PART 2: Dual-loop (if e2e) + SDD Integration (VERBATIM phase6a 170-206) ===== -->

<if e2e layer active (layer 3)>:

#### Playwright Dual-loop (independent of the TDD mode chosen above)

Before writing a new E2E spec, the agent evaluates whether the flow warrants
prior visual exploration with the Playwright MCP, or whether it can go directly
to writing the versioned spec. This is not a mandatory step in all cases
— forcing it always would be unnecessary ceremony in simple, well-known flows.

**Use the MCP to explore first when**:
- The flow has multiple visual states or transitions (e.g., loading,
  error, success, with animations or layout changes).
- It is the first time this interaction is being tested — there is no prior
  similar spec to confidently start from.
- The user explicitly asks for visual validation before committing
  to the spec.

**Go directly to writing the spec when**:
- The flow is a simple, well-known CRUD (create → appears in list, edit
  → updates, delete → disappears) with no complex visual states.
- A similar spec already exists in the project that can serve as a template.

If the agent decides to explore first: use the Playwright MCP to navigate,
interact, and (if applicable) capture screenshots of the real flow running on
the dev server — without writing any files yet. Once visually confirmed
that the flow behaves as expected, write the versioned spec
in `e2e/` following the normal Red-Green-Refactor cycle above.

#### ⛔ MANDATORY OUTPUT when closing a cycle with E2E specs

Applies **whenever E2E specs have been generated** (in any TDD mode). Upon completing
the (green) cycle and BEFORE declaring the task done or committing, ALWAYS show the user
the command to see them run in the browser, with the **exact path of the newly generated spec**
(never a generic command):

```
To see these tests running in the browser:
npm run test:e2e -- --headed --workers=1 --project=chromium e2e/<exact-name>.spec.ts
```

It is mandatory output, not optional: it is easy to omit due to momentum toward the commit. If
you declare "done" or commit without having shown this command (having generated E2E specs),
it is a protocol violation. It also appears as an item in `checks_before_done`.

#### SDD and Local Orchestration Integration

- **Route A**: the `🧪 TDD PROPOSAL` appears after `🔍 PREFLIGHT`, before implementing.
- **Route B/C (SDD)**: the `🧪 TDD PROPOSAL` is issued inside `sdd-apply`, per task from `tasks.md` — not to the full pipeline.
- `🧪` always comes after `🪜 DECISION LADDER` and after `🔍 PREFLIGHT`.

Full order in Route A: 🪜 Ladder → 🔍 Preflight → 🧪 TDD Proposal → implementation.
Order in sdd-apply (Routes B/C): 🪜 Ladder (per task) → 🧪 TDD Proposal (per task) → implementation.

