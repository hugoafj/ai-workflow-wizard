---
name: wf-tdd
description: "Trigger: writing tests, feature code, TDD, red green refactor. OR when sdd-apply is about to execute. Wizard-owned TDD ritual — coverage matrix, test proposal, Red-Green-Refactor (standard) or Strict via gentle-ai's strict_tdd. Auto-activates before sdd-apply to enforce TDD protocol. Load before writing tests or code."
license: MIT
metadata:
  author: hugoafj
  version: "1.0"
---

<!--
  PACKAGED as a real Claude Code Skill. The body is assembled by the Builder
  (wf-init/lib/builder.md) from ../_base.md inserting the mode variant
  (standard|strict) according to state.testing.tdd_mode. Not duplicated here.
-->

{{PROTOCOL_BODY: templates/commands/wf-tdd/_base.md + variants/<tdd_mode>.md}}
