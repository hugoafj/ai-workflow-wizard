---
description: "Use Devin/Windsurf subagents for independent tasks"
trigger: always_on
---

## Subagent delegation (Windsurf / Devin)

Use `run_subagent` with the appropriate profile whenever it reduces context bloat and the subtasks are independent. Parallelize independent work; keep the parent thread as a thin coordinator.

### When to delegate

| Task type | Profile | Execution | Why |
|-----------|---------|-----------|-----|
| Explore / understand 4+ files | `subagent_explore` | Background | Compress broad context into a handoff |
| Write 2+ non-trivial, isolated files | `subagent_general` | Foreground or background | Keep the parent context lean |
| Run independent tests / builds / installs | `subagent_general` | Background | Parallelize verification |
| Compare alternative approaches | `subagent_explore` | Background | Evaluate options in parallel |
| Single mechanical one-file edit | — | Inline | Subagent overhead not worth it |

### Rules

- **Isolate work**: each subagent must own a distinct set of files or concerns. Never run two subagents that edit the same file in parallel.
- **Foreground vs background**: use foreground for critical-path / blocking work; background for work the parent can continue without.
- **Profile choice**: read-only exploration → `subagent_explore`; any writing or tool use → `subagent_general`.
- **Handoff**: give each subagent a narrow, outcome-shaped prompt and return a concise summary, not a raw transcript.
- **No nested subagents**: do not spawn subagents from inside a subagent unless a custom profile explicitly allows it.
- **Cost check**: subagents run as separate sessions and bill independently. Use them when the saved context-window / context-bloat and wall-clock time outweigh the extra spend.
- **Fallback**: if a subagent returns ambiguous or incomplete results, do not spawn another to retry; synthesize inline or ask the user.

### Anti-patterns

- Do not parallelize tightly coupled tasks that must be designed together.
- Do not delegate trivial one-line fixes.
- Do not use subagents as a generic “do it for me” replacement for inline reasoning.
