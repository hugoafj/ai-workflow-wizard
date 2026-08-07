# wf-ladder

Explicitly apply this wizard's own `wf-ladder` (Decision Ladder) for the next implementation.

This is a wizard-owned command (prefix `wf-`), independent from gentle-ai. It never decides
whether to use gentle-ai's SDD, nor how gentle-ai delegates — see `wf-sdd-trigger` for that axis.

The Ladder always applies before `wf-preflight` (see `wf-sdd-trigger`), regardless of the outcome.
Universal order: 🪜 wf-ladder → 🔍 wf-preflight → flow per the wf-sdd-trigger outcome.
When SDD is forced (`wf-force-sdd`), it also applies within gentle-ai's `sdd-apply` for each
individual task once delegated.

Walk through each rung in order, declare the question and your answer out loud,
and stop at the first one where the answer is "yes".

Required output format:

🪜 WF-LADDER
  1. Does it need to exist? → <answer and brief reason>
  2. Does it already exist in the code? → <answer and brief reason>
  ...
  ✓ Rung N — <what is used or done and why>

Rungs:
1. Does this really need to exist? If not, skip it.
2. Does it already exist in this codebase? If yes, reuse it instead of rewriting it.
3. Does the language's standard library already do it? If yes, use the standard library.
4. Is it a native platform feature? If yes, use the native approach.
5. Is there an already installed dependency in the project that works? If yes, use it.
6. Can it be done in a single line? If yes, do it in one line.
7. Only if none of the above apply: write the minimum code necessary that works.

Only declare the rungs you evaluated until reaching the ✓.
Do not list rungs you did not get to evaluate.
After the ✓, propose the implementation.
