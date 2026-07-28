---
name: tdd-protocol
description: TDD Protocol for the project — coverage matrix by change type, test proposal before implementing, Red-Green-Refactor cycle (standard mode) or Strict enforcement via sdd-apply, Playwright Dual-loop and SDD integration. Load it before writing tests or feature code.
---

<!--
  PACKAGED as a real Claude Code Skill. The body is assembled by the Builder
  (wf-init/lib/builder.md) from ../_base.md inserting the mode variant
  (standard|strict) according to state.testing.tdd_mode. Not duplicated here.
-->

{{PROTOCOL_BODY: protocols/tdd/_base.md + variants/<tdd_mode>.md}}
