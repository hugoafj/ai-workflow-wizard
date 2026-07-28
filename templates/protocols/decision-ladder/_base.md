# Protocol: Decision Ladder + Local Orchestration (assembler)

<!--
  SINGLE SOURCE of the local flow control mechanism. The VERBATIM CONTENT lives in two
  separately addressable fragments (they have different lifecycles):

    - ladder.md              → Decision Ladder (rungs). OPTIONAL feature
                               (state.answers.decision_ladder / footer decision-ladder=yes/no).
    - local-orchestration.md  → Local Orchestration (Minimal Exploration, Decision Tree,
                               Routes A/B/C, Preflight, Route B Lock). MANDATORY (always-on).

  ASSEMBLY (applied by Builder B3/B5, and wf-refresh/wf-settings when re-injecting):
    body = (if decision_ladder==true: ladder.md) + local-orchestration.md
  Copied VERBATIM, character by character, without summarizing or omitting subsections. The HTML
  wf-version footer does NOT go here (it goes in templates/AGENTS.router.md).

  Dual packaging from this assembly: skill/SKILL.md (Claude) and
  .agents/protocols/decision-ladder.md (flat). The body marker of skill/SKILL.md points to
  this _base.md, which the Builder resolves by concatenating the fragments according to the state.
-->

{{ASSEMBLE: (if state.answers.decision_ladder) ladder.md + local-orchestration.md}}
