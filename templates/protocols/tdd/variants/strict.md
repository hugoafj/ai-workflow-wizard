<!-- STRICT VARIANT of the TDD Protocol.
     The Builder inserts this block when state.testing.tdd_mode == "strict".
     Logic source: phase6a 111-127 (omission condition) + phase46 79-218
     (gentle-ai native mechanism). In Strict mode, the "Protocol per
     change" and the standard "Implementation cycle" are NOT written: that behavior is handled
     directly by the gentle-ai `sdd-apply` skill. -->

#### Strict TDD Mode (gentle-ai native mechanism)

This project is in **Strict TDD Mode**. Unlike the standard TDD Protocol:

- **There is no option to skip TDD.** The agent does not offer "Skip TDD" for any change.
- **Real evidence is required** per task: `RED → GREEN → REFACTOR` table with the runner
  output, not an unverified result narration.
- **The source of truth is `openspec/config.yaml → testing.strict_tdd: true`** (and its
  Engram mirror `sdd/{project}/testing-capabilities`). The gentle-ai `sdd-apply` skill
  consults that value and **rejects the work** if the evidence is missing or incomplete.
- That is why this `AGENTS.md` does **not** repeat the "Protocol per change" or the
  "Implementation cycle": it is not content this workflow simulates, but a native mechanism.

The coverage matrix (above), the Playwright Dual-loop, and the SDD and Local
Orchestration Integration **do** still apply equally, because they answer different questions
from the skip/no-skip discipline.
