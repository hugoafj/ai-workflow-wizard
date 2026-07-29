# Changelog

## [0.1.2-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.1.1-beta.1...v0.1.2-beta.1) (2026-07-29)


### Bug Fixes

* **phase45:** auto-delegate sdd-init via skill() with manual fallback ([6b64b92](https://github.com/hugoafj/ai-workflow-wizard/commit/6b64b925bd8ffd4ad3c01e19c3277557df023dbf))
* **phase45:** auto-delegate sdd-init via skill() with manual fallback ([56f1aa8](https://github.com/hugoafj/ai-workflow-wizard/commit/56f1aa871954066dcf5236cc4bf68238c71e1a91))
* **phase45:** try direct file read of sdd-init SKILL.md when skill() not available ([#8](https://github.com/hugoafj/ai-workflow-wizard/issues/8)) ([15670e2](https://github.com/hugoafj/ai-workflow-wizard/commit/15670e227b8343b8b3c0820a533133e037b82233))

## [0.1.1-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.1.0-beta.1...v0.1.1-beta.1) (2026-07-29)


### Bug Fixes

* **phase0c:** fall back to plain text when structured input doesn't support 6 options ([b4d17ad](https://github.com/hugoafj/ai-workflow-wizard/commit/b4d17add4d3062aaab3523adc8d1442ff25c52ac))
* **phase0c:** fall back to plain text when structured input doesn't support 6 options ([a2abcdc](https://github.com/hugoafj/ai-workflow-wizard/commit/a2abcdcdfe2601bb60da8f8efe80bd633551995e)), closes [#3](https://github.com/hugoafj/ai-workflow-wizard/issues/3)

## [0.1.0-beta.1](https://github.com/hugoafj/ai-workflow-wizard/releases/tag/v0.1.0-beta.1)

Initial beta release.
See [AI_DEV_WORKFLOW.md](AI_DEV_WORKFLOW.md) for full documentation.

### Install

```bash
curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/install.sh | bash
```

Supports: Claude, Cursor, Windsurf, Kiro, Codex, Copilot, Antigravity, OpenCode.
