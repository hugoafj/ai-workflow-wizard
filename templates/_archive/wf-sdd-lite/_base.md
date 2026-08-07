# wf-sdd-lite (ARCHIVED)

This command has been archived as part of the refactor to simplify the SDD routing system
to 2 outcomes: `wf-no-sdd` / `wf-force-sdd`. The old "severity" concept (lite vs full) is no
longer used. See `wf-sdd-trigger` for the current protocol.

Original content preserved below for reference:

---

# wf-sdd-lite

Explicitly request gentle-ai's SDD at `wf-sdd-lite` severity for the next task (this wizard's own
lighter sequencing — see `wf-sdd-trigger`). **`wf-sdd-lite` is NOT a gentle-ai command**; it is
this wizard's own name for asking gentle-ai to run its real `sdd-propose → sdd-tasks → sdd-apply`
phases, skipping `sdd-spec`/`sdd-design`. Never present it to the user as if it were native to
gentle-ai, and never confuse it with gentle-ai's own `/sdd-new` or `/sdd-lite` (the latter does
not exist in gentle-ai at all).

Wait for proposal approval before generating tasks.
Wait for task approval before implementing.

The user chose `wf-sdd-lite` consciously.
Do not ask if they prefer full SDD — they already know.
Do not ask if they prefer direct implementation — they already know.

## What to actually do

Explicitly request gentle-ai's SDD for this task, telling it to run `sdd-propose → sdd-tasks →
sdd-apply` (no `sdd-spec`, no `sdd-design`). **Do not specify how gentle-ai delegates or executes
these phases** — gentle-ai's own native orchestrator, already installed for this project's active
IDE(s), owns that decision (sub-agents, inline solo-agent execution, `delegate_task`, etc., per
adapter). Re-specifying a delegation mechanism here is exactly the bug this command used to have.

`sdd-apply` is HEADLESS (it executes and returns, it cannot ask you). Therefore, after approving
tasks, YOU (the orchestrator) issue the 🧪 TDD PROPOSAL covering the tasks in batch and wait for
the user's coverage choice BEFORE requesting `sdd-apply`. Only then make the request with the
decision baked in (e.g. "coverage: unit + integration + e2e") and reference the `wf-tdd` skill so
the RED→GREEN cycle runs per task, showing the `--headed` command if it generates E2E specs. In
strict mode there is no proposal (request directly; `sdd-apply` enforces via `strict_tdd: true`
read from `openspec/config.yaml`).

When `sdd-apply` finishes, with tests/checks green, SUGGEST to the user
to run gentle-ai's `sdd-archive` as cleanup (it moves the change to `openspec/changes/archive/`;
do not run it on your own and it requires explicit user approval).
