<!-- STANDARD VARIANT of the TDD Protocol (VERBATIM phase6a 111-169).
     The Builder inserts this block when state.testing.tdd_mode == "standard". -->

#### Protocol per change

> **This subsection and "Implementation cycle" (the 5 Red-Green-Refactor steps
> below) are only written in `AGENTS.md` if the user chose option 1
> (Standard TDD Protocol) in the Phase 4.6 question.** If they chose option 2
> (Strict TDD Mode), these two subsections are omitted — that behavior is
> handled directly by the gentle-ai `sdd-apply` skill from the
> `openspec/config.yaml → testing.strict_tdd` field, without needing its own text
> in `AGENTS.md`.
>
> **The "Playwright Dual-loop" and "SDD and Local Orchestration Integration"
> below are NOT subject to this condition** — they are written
> whenever the E2E layer is active, regardless of which TDD mode was
> chosen. They answer a different question ("how is the E2E spec built?"
> and "at what point in the flow does the test proposal appear?"), not the
> skip/no-skip discipline that does depend on the mode.

Before implementing, the agent declares:

```
🧪 TDD PROPOSAL
  Change: <brief description>
  Suggestion: <Unit / Integration / E2E / combination> — <one-line reason>
```

If the suggestion already covers unit + integration + e2e (it is complete):
```
  Options:
    1. [Apply suggestion] — unit + integration + e2e
    2. [Skip TDD] — straight to code (user's risk)
```

If the suggestion is partial (only some layers):
```
  Options:
    1. [Apply suggestion] — <suggested layers>
    2. [TDD Full] — unit + integration + e2e
    3. [Skip TDD] — straight to code (user's risk)
```

The agent stops and waits for a response before writing any test or code.

#### Implementation cycle (once the option is confirmed)

1. Write the tests — they must compile and fail (RED) before continuing.
2. Show the runner output confirming the RED.
3. Implement the minimum code to pass the tests (GREEN).
4. Refactor if applicable, without breaking green.
5. Declare done only when all `checks_before_done` are green.

If E2E specs were generated, when closing the cycle it is **MANDATORY** to show the
`--headed` command with the exact path of the spec (see the "⛔ MANDATORY OUTPUT when
closing a cycle with E2E specs" section below). Do not omit it to move on to the commit.

