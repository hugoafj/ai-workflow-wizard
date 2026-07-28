# Fragment: Local Orchestration (MANDATORY, always-on)

<!--
  SINGLE SOURCE of the Local Orchestration (Minimal Exploration, Decision Tree, Routes
  A/B/C, Preflight, Route B Lock Protocol). MANDATORY — always included.
  DO NOT rewrite the tree or the Preflight format: the tree is computed silently and
  the Preflight output is simple (Route + Impact Analysis + Checklist only in Route B).
  Section 5 (PRECHECK) is an enforcement addendum of ours, on top of the legacy.
  Consumed by: Builder (B3/B5), wf-refresh (Layer 2, mandatory). Do not omit subsections
  (breaks classification silently). The wf-version footer does NOT go here (it goes in the router).
-->

### 📋 Local Orchestration: Complexity Flow (SDD, SDD Lite, or Direct)

> This matrix only decides which SDD phases to run for a local change
> (direct / lite / full). It is independent of gentle-ai's global Delegation Stop Rules
> (4-file rule, multi-file write rule, etc.), which
> still apply in parallel for sub-agent delegation and fresh review.
> They do not replace or overlap it; they are separate axes.

> **Important:** The examples in this section are illustrative only and **not exhaustive**. Classification must always be based on the criteria and the decision tree, never on similarity to an example.

This project operates under the `gentle-ai` global ecosystem. For local
changes at the delegation boundary, the agent evaluates complexity
**before touching the workspace** to decide whether to apply the full harness or
an abbreviated flow.

#### 0. Minimal exploration beforehand (does not count as "touching the workspace")

Before classifying, the agent reads enough to know if the change
alters existing contracts or introduces new abstractions. This exploration
may open more files than will ultimately be modified.

The Preflight (section 2) is always declared **after** this exploration.

Classification must be based on the real project state discovered during
exploration, even if that state modifies the initial interpretation of the
prompt.

The agent must never assume that a feature exists or does not exist without
verifying it first.

During this exploration, the agent must internally perform all complexity
evaluation before issuing the Preflight. The diagnosis issued must be
unique and definitive. The agent must not reclassify the route during the same turn or issue multiple Preflights. If it detects new information before completing the analysis, it must
integrate it into a single definitive Preflight; it must never correct itself mid-response.

If during this exploration the agent identifies two or more reasonable
architectures for solving the problem, it should mention them briefly in the
Preflight Impact Analysis.

---

#### 1. Decision Tree

Before evaluating the limits of each route, the agent must mentally answer
the following questions in order.

**1. Does the change modify architecture, public contracts, data model, or introduce important tradeoffs?**

If the answer is **Yes**, the task belongs directly to **Route C**.

Otherwise, continue.

**2. Does the requirement leave functional, behavioral, UX, or design decisions that the user did not specify and that cannot be reasonably resolved through widely accepted conventions?**

Decisions considered conventional or low-risk do not qualify for Route B, for example:

- Common validations.
- Usual framework conventions.
- Mechanical implementation decisions.
- Small interaction details (e.g., Enter vs. onBlur when both
  represent a conventional implementation).
- Internal extensions needed to implement the functionality.

They do qualify for Route B when:

- There are several equally valid functional behaviors.
- An important business rule must be decided.
- UX can be resolved through multiple approaches with different consequences.
- The decision will condition future implementations.

If the answer is **Yes**, it at least belongs to **Route B** (as long as it meets its restrictions). If any restriction fails, it automatically escalates to **Route C**.

Otherwise, continue.

**3. Is the implementation deterministic, low-risk, and is there only one reasonable implementation?**

If the answer is **Yes**, evaluate Route A.

---

#### 2. Local Routing Matrix

The agent will classify the task into one of the following three exclusive routes.

### 🟢 Route A — Direct Inline Work

**Criterion**

Deterministic changes where there is an obvious implementation and minimal
design risk.

**Examples (not exhaustive)**

- Specific bug fixes.
- UI or style changes.
- Mechanical refactors.
- Renames.
- Documentation.
- Logs.
- Tests.
- Repetitive changes even if they involve several files, as long as they do not change
  the system design.

**Action**

Direct implementation without planning or SDD.

---

### 🟡 Route B — SDD Lite

**Criterion**

The change requires validating a design decision with the user because there are
several reasonable approaches that produce different functional behaviors and
none can be considered clearly dominant.

To remain in Route B, **ALL** of the following conditions must be met:

- [ ] Maximum 3 files modified.
- [ ] Does not introduce new reusable abstractions.
- [ ] Does not alter public system contracts (external APIs, SDKs,
      shared libraries or interfaces consumed outside the local scope of the
      change). Adding internal methods needed to implement a
      functionality is not considered, by itself, a public contract
      alteration.
- [ ] Is completely reversible with a single revert.
- [ ] There is a single recommended approach after analysis.

**Examples (not exhaustive)**

- Extending an existing flow.
- Adding complex validations.
- Introducing new logic within an existing feature.
- Changes where initially there are two reasonable alternatives but,
  after analysis, one is clearly superior.

**Action**

Stop and execute the protocol in Section 4.

---

### 🔴 Route C — Full SDD / OpenSpec by Gentle-ai

**Criterion**

The change modifies the architecture, introduces significant uncertainty,
alters public contracts, creates important new abstractions, or fails to meet
any of the Route B restrictions.

**Examples (not exhaustive)**

- Architecture changes.
- New subsystems.
- Important migrations.
- Data model changes.
- Cross-cutting refactors.
- Replacing core libraries.
- Changing public APIs.
- Converting synchronous APIs to asynchronous.
- Changing the state system.

**Action**

Mandatorily initiate the full gentle-ai SDD pipeline. **In standard mode, since `sdd-apply` is a headless sub-agent, the orchestrator issues the `🧪 TDD PROPOSAL` (per task/phase) and waits for the user's choice BEFORE delegating to `sdd-apply`**; then it delegates with the decision *baked* into the prompt and injects the `tdd-protocol` skill (under `## Skills to load before work`) for execution. In strict mode there is no proposal (you delegate directly; `sdd-apply` enforces RED→GREEN via `strict_tdd: true`).

> **Delegation**: Delegate each phase to the corresponding sub-agent using the IDE's native delegation mechanism (`task()`, `spawn_agent()`, `run_subagent()`, etc.). In Route B, the `/sdd-lite` command handles the simplified pipeline (propose → tasks → apply). In Route C, the full pipeline is the project phases (propose → spec → design → tasks → apply → verify → archive).

#### 3. Mandatory Preflight Declaration

> **Mandatory output format according to the selected route**
>
> **🟢 Route A**
> - Declare the Preflight.
> - Indicate the chosen route and a brief justification.
> - Proceed immediately to implementation.
> - **Do not show the SDD Lite Checklist.**
> - **Do not generate a plan.**
>
> **🟡 Route B**
> - Declare the Preflight.
> - Show the full SDD Lite Checklist.
> - Present a brief plan (3–5 points).
> - Wait for approval before implementing.
>
> **🔴 Route C**
> - Declare the Preflight.
> - Briefly explain why it requires SDD.
> - Initiate the corresponding SDD pipeline.
> - **Do not show the SDD Lite Checklist.**

Before writing code, planning, or delegating, the agent must perform the mental calculation silently and emit a single definitive diagnosis with the following structure:

### 🔍 LOCAL COMPLEXITY PREFLIGHT
- **Determined Route:** [Route A / Route B / Route C]
- **Impact Analysis:** [Which files are altered, why it qualifies or not for Lite, and if 2+ architectures were identified]
> **Important:** The SDD Lite Checklist belongs exclusively to **Route B**.
> It must never be shown for tasks classified as **Route A** or **Route C**.
- **SDD Lite Checklist:**
    - [ ] Maximum 3 files: [✓ / ✗]
    - [ ] No new abstractions: [✓ / ✗]
    - [ ] No contract alteration/extension (signatures/returns): [✓ / ✗]
    - [ ] 100% Reversible: [✓ / ✗]
    - [ ] Single unambiguous approach: [✓ / ✗]

Each checklist item is marked ✓ or ✗ without semantic interpretation. If the agent hesitates between pass and fail, it marks ✗ by default. A single ✗ invalidates Route B and automatically converts the task to Route C (Full SDD).

If the determined route is **Route C**, the agent will **NOT** offer options to skip the harness or ask if they prefer to omit it. It will mandatorily declare the start of the full global pipeline.

#### 4. EXCLUSIVE Lock Protocol for Route B (SDD Lite)

The agent will show this menu **ONLY** if the Preflight cleanly determined that the final route is **Route B**. The agent will stop immediately after printing the menu, and it is strictly prohibited to write code or detail technical tasks until receiving the option number:

> ⚡ **SDD Lite proposal detected.** Please select how to proceed by writing the option number:
> 1. **`[Execute Standard SDD Lite]`** -> `sdd-propose` → `sdd-tasks` and then `sdd-apply` will be executed. **Important (standard mode)**: `sdd-apply` is a **headless** sub-agent that cannot ask you questions, so after `sdd-tasks` **the ORCHESTRATOR issues the `🧪 TDD PROPOSAL` (coverage per task, in batch) and waits for your choice BEFORE delegating to `sdd-apply`**; then it delegates with the decision *baked* into the prompt and injects the `tdd-protocol` skill (under `## Skills to load before work`) for RED→GREEN execution. In strict mode there is no proposal (you delegate directly; `sdd-apply` enforces via `strict_tdd: true`). When finished, with tests/checks green, the agent **suggests** running `sdd-archive` as cleanup (moves the change to `archive/`; it does not execute it on its own and requires explicit user OK).
> 2. **`[Execute Custom SDD Lite]`** -> The agent proposes a tailored intermediate path. *(ATTENTION AGENT: If you suggest this option, you must list here which specific 4 or 6 phases from the global gentle-ai phases you suggest for this case and why. The full global pipeline consists of the project's indexed phases, do not invent a generic 5-phase flow)*.
> 3. **`[Force Full SDD]`** -> Ignore the Route B shortcut and initiate the full global gentle-ai pipeline with all its indexed phases.
> 4. **`[Ignore SDD (Direct)]`** -> Skip all design harnesses entirely and jump directly to code under user risk.

#### 5. ✅ Mandatory PRECHECK — enforcement addendum (paste BEFORE writing code)

> This PRECHECK is an addendum of ours **on top of** the legacy protocol above; it does not
> replace it. It gathers the gates into **a single literal output that the agent MUST paste** (with
> each item marked) **before touching production code**. EXTERNAL gate: if you did not paste it,
> you did not start. Any applicable item with ✗ or not done → STOP.

Mandatory format (paste it as-is, resolved, right before implementing / delegating):

```
✅ PRE-IMPLEMENTATION PRECHECK
  🪜 Decision Ladder declared (rungs visible up to ✓)                      → [✓/✗]
  🔍 Preflight issued with Route (A/B/C) + visible Impact Analysis         → [✓/✗]
  🚦 Route gate fulfilled:
       • Route A → no extra gate (proceed)                                → [✓ / n/a]
       • Route B → SDD Lite Checklist shown ✓, lock menu shown,
                   and the user CHOSE an option                            → [✓/✗ / n/a]
        • Route C → mandatory SDD pipeline start declared and
                   delegated to gentle-ai SDD skills using the IDE's
                   native delegation mechanism; NO inline proposal
                   or direct local implementation                          → [✓/✗ / n/a]
  🧪 Mode TDD ritual, in the correct place:
       • Route A → 🧪 TDD PROPOSAL issued + user choice (standard)
                   / RED→GREEN evidence (strict)                          → [✓/✗ / n/a]
       • Route B/C → n/a here (the TDD ritual goes INSIDE sdd-apply, per task)
  → If all applicable items are ✓: proceed. If any is ✗: STOP.
```

PRECHECK rules:
- It is **mandatory in ALL routes** (in Route A too, even if the change seems obvious).
- It is pasted **once per task/change**, right before implementing (Route A) or delegating to the
  pipeline (Route C). In Route B it is pasted only when the user has already chosen the menu option.
- **Route C — no inline proposal**: the agent does NOT draft the proposal/spec/design itself in
  the turn. It declares the mandatory start of the pipeline and delegates to the gentle-ai SDD skills
  using the IDE's native delegation mechanism (`task()`, `spawn_agent()`, `run_subagent()`,
  etc.), which run the **actual indexed project phases** (not a generic 4-5 phase flow
  invented). Route C's PRECHECK is marked ✓ when that happened, not when
  you wrote a proposal by hand.
- It is not decorative: marking an item ✓ when you did not actually do it is as serious a violation
  as skipping the gate.
