# decision-ladder

Explicitly apply the Decision Ladder for the next implementation.

The Ladder always applies before Preflight on any route.
Universal order: 🪜 Ladder → 🔍 Preflight → flow by route.
In Routes B/C it also applies within sdd-apply for each individual task.

Walk through each rung in order, declare the question and your answer out loud,
and stop at the first one where the answer is "yes".

Required output format:

🪜 DECISION LADDER
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
