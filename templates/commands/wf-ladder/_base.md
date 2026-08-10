# wf-ladder

Explicitly apply this wizard's own `wf-ladder` (Decision Ladder) for the next implementation.

This is a wizard-owned command (prefix `wf-`), independent from gentle-ai. It never decides
whether to use gentle-ai's SDD, nor how gentle-ai delegates — see `wf-sdd-trigger` for that axis.

## Activation Contract

Load before proposing any implementation, and before `wf-preflight` (see `wf-sdd-trigger`, when
this project has the routing feature active) — regardless of whether the change ends up as direct
work or forced SDD. This is a wizard-owned protocol (prefix `wf-`), independent from gentle-ai:
it never decides whether to use gentle-ai's SDD, nor how to delegate.

## Hard Rules

- Declare each rung and its answer **aloud** — never apply the ladder in silence. The analysis
  output must be visible so the user can audit it.
- Stop at the first rung where the answer is "yes" and use it.
- Only declare the rungs evaluated up to the ✓ — never list rungs you did not get to evaluate.

## Decision Gates

| Rung | Question | If yes |
|---|---|---|
| 1 | Does this really need to exist? | Skip it |
| 2 | Does it already exist in this codebase? | Reuse it instead of rewriting |
| 3 | Does the language's standard library already do it? | Use the standard library |
| 4 | Is it a native platform feature? | Use the native approach |
| 5 | Is there an already installed dependency that works? | Use it |
| 6 | Can it be done in a single line? | Do it in one line |
| 7 | (only if none above apply) | Write the minimum necessary code that works |

## Execution Steps

1. Walk the Decision Gates table in order, top to bottom.
2. Stop at the first rung whose answer is "yes" (or reach rung 7 if none apply).
3. Emit the Output Contract with the rungs evaluated up to that point.
4. Pause explicitly and wait for the user to review and confirm the ladder rungs before
   continuing (e.g., "Review these rungs and say 'continue' or 'no, let me clarify X'").
5. After user confirmation: if this project's routing feature is active, continue to
   `wf-sdd-trigger` — its classification uses this result as input (e.g. detecting "already exists
   in the code" at rung 2 may inform the SDD decision). If routing is not active, proceed directly
   to `wf-tdd` (if active) or to implementation.
6. When routing is active and `wf-sdd-trigger` results in forced SDD, repeat this ladder once per
   task inside gentle-ai's `sdd-apply`, once delegated — not for the full pipeline.

## Output Contract

```
🪜 WF-LADDER
  1. Does it need to exist? → <answer and brief reason>
  2. Does it already exist in the code? → <answer and brief reason>
  ...
  ✓ Rung N — <what is used or done and why>
```

## References

- `wf-sdd-trigger` — (when this project has the routing feature active) consumes this result as input to `wf-preflight`.
- `wf-orchestrator` — single entry point that sequences this protocol with `wf-sdd-trigger`/`wf-tdd`.
