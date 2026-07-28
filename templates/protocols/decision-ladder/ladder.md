# Fragment: Decision Ladder (OPTIONAL feature)

<!--
  SINGLE SOURCE of the Decision Ladder (rungs). OPTIONAL feature: injected only if
  state.answers.decision_ladder == true (footer decision-ladder=yes). VERBATIM phase6a
  209-250. Consumed by: Builder (B3/B5), wf-refresh (optional features catalog),
  wf-settings (toggle Decision Ladder). Do not paraphrase.
-->

### Decision Ladder (before writing any code)

Before proposing any implementation, walk this ladder in order and
**declare each rung and its answer aloud**. Do not apply the ladder in
silence — the analysis output must be visible so the user can
audit it. Stop at the first rung where the answer is "yes" and use it.

**When it applies:**

The Ladder applies **always before Preflight**, in all routes. This is
intentional: the Ladder can simplify a task before classifying it — if
it detects that it "already exists in the code" (rung 2), the task can move from Route C
to Route A. The Preflight uses the Ladder's result as input for classification.

Universal order: 🪜 **Ladder → 🔍 Preflight → flow based on route**.

In Routes B and C, the Ladder applies **a second time** inside `sdd-apply`,
before implementing each individual task — the SDD pipeline already approved the what and
the how, and the Ladder confirms each implementation follows the minimal path.

Mandatory output format (in any case):

```
🪜 DECISION LADDER
  1. Does it need to exist? → <answer and brief reason>
  2. Does it already exist in the code? → <answer and brief reason>
  ...
  ✓ Rung N — <what is used or done and why>
```

Rungs:

1. Does this really need to exist? If not, skip it.
2. Does it already exist in this codebase? If yes, reuse it instead of rewriting.
3. Does the language's standard library already do it? If yes, use the standard library.
4. Is it a native platform feature? If yes, use the native approach.
5. Is there already an installed dependency in the project that works? If yes, use it.
6. Can it be done in a single line? If yes, do it in one line.
7. Only if nothing above applies: write the minimum necessary code that works.

Only declare the rungs evaluated up to the ✓. In Route B/C,
the Ladder is applied once per task — not to the full pipeline.
