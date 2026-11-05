<!--
  SOURCE of the coverage matrix for stacks without UI (profiles with "ui": false in
  profiles.md). builder-core.py (_testing_guidance_parts) uses it instead of the head of
  testing-approach.section.md, which talks about hooks and components. The E2E guidance
  (from "### Playwright dual loop" on) still comes from testing-approach.section.md.
  Do not add the "## Testing Approach" heading or the command blocks here.
-->

### Coverage by change type

| Change type | Unit | Integration | E2E |
|---|---|---|---|
| Pure logic in a service, helper or util | Yes | No | No |
| Handler, controller or route with its own validation | Yes | Optional | No |
| Endpoint that touches the database or another service | No | Yes | No |
| Complete API feature across layers | No | Yes | Only if a browser or full-stack flow exists |
| Bug fix with possible regression | Based on origin | No | No |
| Config, DTOs or typings only | No | No | No |

This matrix is a guideline. If logic could break silently and the table does not
cover it, add tests anyway.
