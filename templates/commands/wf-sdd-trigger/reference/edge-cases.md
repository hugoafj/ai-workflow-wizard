# wf-sdd-trigger — extended rationale and edge cases

## Why this protocol exists

gentle-ai only starts SDD when the user explicitly asks or accepts a proposal — it never infers
SDD purely from size/risk (`explicit_request_or_accepted_proposal` gate). Some projects need a
stronger, explicit project policy (including "always force SDD, even for trivial changes").
`wf-sdd-trigger` is how this wizard expresses that policy as an **explicit request** gentle-ai's
own gate accepts — it is a trigger INTO gentle-ai's legitimate entry point, not a competing
routing system.

## The Windsurf/Devin capability-detection nuance

gentle-ai's own native orchestrator (installed/synced per-adapter) already owns HOW to route
(Direct inline / Delegated direct) and HOW to delegate SDD phases per adapter (Full sub-agents /
Hermes delegate_task / Solo-agent inline — see gentle-ai `docs/agents.md`). This protocol never
re-specifies that as a fixed, hardcoded mechanism.

The old (retired) protocol's bug was assuming ONE universal delegation mechanism ("delegate via
`task()`/`spawn_agent()`/`run_subagent()`") for every adapter. The fix is not to swap in a
different hardcoded assumption per IDE name: gentle-ai has no dedicated adapter entry for Devin (a
fork that shares Windsurf's file paths), so its installed content for "Windsurf" can say "no
sub-agents" even when the actual running agent (Devin) genuinely has a working subagent/task tool.

**The correct rule**: self-check your OWN real toolset in this session before trusting any label
(yours or gentle-ai's) about whether you can delegate. If you have a real subagent-launching tool
available right now, use it. If you don't, execute inline as the solo executor.

## Invocation form: `sdd-new` (no slash) is canonical; `/sdd-new` is the fallback

Invoke the skill as the literal string `sdd-new <feature or fix>` WITHOUT the leading slash — that
is the canonical natural-language trigger that gentle-ai's orchestrator recognizes on every adapter
(e.g., Codex/ChatGPT, and historically Devin when it lacks subagent tooling). If your adapter only
supports native slash syntax, use `/sdd-new <feature or fix>` instead — gentle-ai recognizes it as
a skill invocation either way.

## Worked examples

| Type of change | Expected outcome | Why |
|---|---|---|
| Typo, dependency patch bump, color/spacing change | `wf-no-sdd` | Cause & solution obvious, no alternatives |
| Mechanical refactor across many files (no behavior change) | `wf-no-sdd` | Deterministic, no design decisions |
| Simple bug fix (cause clear, solution direct) | `wf-no-sdd` | One obvious path, no trade-offs |
| Small new feature (max 3 files, direct implementation, behavior obvious) | `wf-no-sdd` | Simple & straightforward, no alternatives |
| Extend existing flow with unspecified UX decision | `wf-force-sdd` | Multiple valid approaches, needs validation |
| New abstraction, shared hook, or architectural pattern | `wf-force-sdd` | Design decision required |
| New global state, new API/endpoint, public contract change | `wf-force-sdd` | Impacts system design, trade-offs present |
| Data model change, dependency migration (major) | `wf-force-sdd` | Breaking changes, multiple valid architectures |
