# Changelog

## [0.8.6-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.8.5-beta.1...v0.8.6-beta.1) (2026-08-19)


### Bug Fixes

* **wf-refresh:** network resilience, full script list, blank-line cleanup and R6 non-interactive gate ([#98](https://github.com/hugoafj/ai-workflow-wizard/issues/98)) ([9a96a1b](https://github.com/hugoafj/ai-workflow-wizard/commit/9a96a1be12d0e94abddbcb52ad050812e56748cc))

## [0.8.5-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.8.4-beta.1...v0.8.5-beta.1) (2026-08-18)


### Bug Fixes

* **wf-refresh:** restore spec satellites, nested stack_key, layers-aware checks and staging writes ([#96](https://github.com/hugoafj/ai-workflow-wizard/issues/96)) ([3cf4fa1](https://github.com/hugoafj/ai-workflow-wizard/commit/3cf4fa14ffe8bbdef7fcb5be0adb94499db44a5c))

## [0.8.4-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.8.3-beta.1...v0.8.4-beta.1) (2026-08-18)


### Bug Fixes

* **wf-refresh:** deterministic builder-core/heavy scripts, deprecated cleanup, 1:1 validation ([#94](https://github.com/hugoafj/ai-workflow-wizard/issues/94)) ([f28710c](https://github.com/hugoafj/ai-workflow-wizard/commit/f28710c24158c30e43a81cfa741d7e2358c13240))

## [0.8.3-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.8.2-beta.1...v0.8.3-beta.1) (2026-08-18)


### Bug Fixes

* **wf-refresh:** issues 2,3,5 — AGENTS.md placeholders, IDE detection, Windsurf/Devin bridge ([#92](https://github.com/hugoafj/ai-workflow-wizard/issues/92)) ([97d661a](https://github.com/hugoafj/ai-workflow-wizard/commit/97d661a0a9cb9c5d788f4c46e452c7d7e453aad4))

## [0.8.2-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.8.1-beta.1...v0.8.2-beta.1) (2026-08-18)


### Bug Fixes

* **wf-refresh:** atomic state in staging, explicit R5 gate, safe commit msg ([#90](https://github.com/hugoafj/ai-workflow-wizard/issues/90)) ([b2ce9ab](https://github.com/hugoafj/ai-workflow-wizard/commit/b2ce9ab8a7213b9763976241b09a97560430a19f))

## [0.8.1-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.8.0-beta.1...v0.8.1-beta.1) (2026-08-18)


### Bug Fixes

* **wf-refresh:** fix infinite loop in R-1 and false drift detection in R1 ([#88](https://github.com/hugoafj/ai-workflow-wizard/issues/88)) ([84d47ae](https://github.com/hugoafj/ai-workflow-wizard/commit/84d47ae00f632dca7ae642a64c081a1604bb4641))

## [0.8.0-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.7.1-beta.1...v0.8.0-beta.1) (2026-08-17)


### Features

* add HARD STOP RULE to AGENTS.md router ([#64](https://github.com/hugoafj/ai-workflow-wizard/issues/64)) ([9474a63](https://github.com/hugoafj/ai-workflow-wizard/commit/9474a638e195f566d941201821b0e7b0ce92a8ca))
* add mandatory hard stops for SDD workflow enforcement ([#59](https://github.com/hugoafj/ai-workflow-wizard/issues/59)) ([29b14eb](https://github.com/hugoafj/ai-workflow-wizard/commit/29b14eb8301253d48e67355d47b9a4b9f878f9e8))
* atomic wf-refresh versioning and custom content protection ([#22](https://github.com/hugoafj/ai-workflow-wizard/issues/22)) ([a1c72c2](https://github.com/hugoafj/ai-workflow-wizard/commit/a1c72c25e435a1b061965b364cc8616a60192e54))
* implement auto-generated WIZARD_MANIFEST.json ([#26](https://github.com/hugoafj/ai-workflow-wizard/issues/26)) ([0063415](https://github.com/hugoafj/ai-workflow-wizard/commit/0063415dbae3f525c6dd862daa867135e15afa79))
* initial release v0.1.0-beta.1 ([b826d39](https://github.com/hugoafj/ai-workflow-wizard/commit/b826d39ce26e550272e9928c53d5e90974e07be6))
* manifest versioning with checksums and recovery guide ([#29](https://github.com/hugoafj/ai-workflow-wizard/issues/29)) ([ba3800e](https://github.com/hugoafj/ai-workflow-wizard/commit/ba3800e40fd4fbb61b876f7e8571c030bf736521))
* refactor /wf-refresh to builder-driven migration mechanism ([#84](https://github.com/hugoafj/ai-workflow-wizard/issues/84)) ([cdda4a4](https://github.com/hugoafj/ai-workflow-wizard/commit/cdda4a4961edde5c7df39abbd3c567ecf3ad4b42))
* support both .windsurf/ and .devin/ IDE paths for wizard compatibility ([#44](https://github.com/hugoafj/ai-workflow-wizard/issues/44)) ([1e8bb71](https://github.com/hugoafj/ai-workflow-wizard/commit/1e8bb712efae2d3257f29a925735e26c125cac77))


### Bug Fixes

* /wf-refresh Layer 2 must always update footer and state ([#41](https://github.com/hugoafj/ai-workflow-wizard/issues/41)) ([bfefa16](https://github.com/hugoafj/ai-workflow-wizard/commit/bfefa16819f1b62c86f435343bf3360f8a50863c))
* apply orphaned testing extras and fragments during build ([#60](https://github.com/hugoafj/ai-workflow-wizard/issues/60)) ([8a64e7b](https://github.com/hugoafj/ai-workflow-wizard/commit/8a64e7b36252ce7eb2f79079917565c1d5ee925f))
* avoid literal newlines inside YAML block scalar (fixes invalid workflow syntax) ([#35](https://github.com/hugoafj/ai-workflow-wizard/issues/35)) ([b322f03](https://github.com/hugoafj/ai-workflow-wizard/commit/b322f03e5ba6796feae3be1b9cce010a57680326))
* clean VERSION newline in manifest-generator to prevent invalid filenames ([1f881e7](https://github.com/hugoafj/ai-workflow-wizard/commit/1f881e7fec2ddf7468ce594b851f003b2b590658))
* conditional CLAUDE.md, complete wf-cleanup, add IDEs/CLIs settings ([#66](https://github.com/hugoafj/ai-workflow-wizard/issues/66)) ([4e62dc4](https://github.com/hugoafj/ai-workflow-wizard/commit/4e62dc4faafdd8196d43f622e73ba5df6e70b53d))
* correct gentle-ai links, clarify install vs usage flow, enforce YAML atomicity ([b9df2dd](https://github.com/hugoafj/ai-workflow-wizard/commit/b9df2ddcca2172cb780dd218b02bf0ddce2ee217))
* implement two-phase version check to prevent infinite loop in wf-refresh ([#76](https://github.com/hugoafj/ai-workflow-wizard/issues/76)) ([233d7d7](https://github.com/hugoafj/ai-workflow-wizard/commit/233d7d797203d01cb02cf1a04a616a377cb8e215))
* **install:** add codex commands, windsurf legacy paths, and devin detection ([#78](https://github.com/hugoafj/ai-workflow-wizard/issues/78)) ([78e78c4](https://github.com/hugoafj/ai-workflow-wizard/commit/78e78c42c7b0211919eaa199de9cabd72c616c88))
* integrate manifest regeneration into release-please workflow ([#37](https://github.com/hugoafj/ai-workflow-wizard/issues/37)) ([46a52cd](https://github.com/hugoafj/ai-workflow-wizard/commit/46a52cde3915ef905cd21b57e1f07c9a06f39fd1))
* make Phase -1 auto-execute at wf-refresh start ([#24](https://github.com/hugoafj/ai-workflow-wizard/issues/24)) ([4b70ff0](https://github.com/hugoafj/ai-workflow-wizard/commit/4b70ff07a00eb02bf616ad52b3a0c986777aa5a0))
* phase0b sync order + phase45 hardcoded paths ([#55](https://github.com/hugoafj/ai-workflow-wizard/issues/55)) ([e864b09](https://github.com/hugoafj/ai-workflow-wizard/commit/e864b0920d7fc16bb42ac6d3c42330e0ca8e9db5))
* **phase0c:** fall back to plain text when structured input doesn't support 6 options ([b4d17ad](https://github.com/hugoafj/ai-workflow-wizard/commit/b4d17add4d3062aaab3523adc8d1442ff25c52ac))
* **phase0c:** fall back to plain text when structured input doesn't support 6 options ([a2abcdc](https://github.com/hugoafj/ai-workflow-wizard/commit/a2abcdcdfe2601bb60da8f8efe80bd633551995e)), closes [#3](https://github.com/hugoafj/ai-workflow-wizard/issues/3)
* **phase1:** ensure wf_phase_done executes before phase2 to update state correctly ([#18](https://github.com/hugoafj/ai-workflow-wizard/issues/18)) ([9869728](https://github.com/hugoafj/ai-workflow-wizard/commit/9869728243cead4765dfe95f4e1499fd9eb29878))
* phase45 creates AGENTS.md greenfield for Windsurf legacy bridge ([#68](https://github.com/hugoafj/ai-workflow-wizard/issues/68)) ([23b800a](https://github.com/hugoafj/ai-workflow-wizard/commit/23b800a6a708466c6b00ab2cf7175f2c745b54ce))
* **phase45:** auto-delegate sdd-init via skill() with manual fallback ([6b64b92](https://github.com/hugoafj/ai-workflow-wizard/commit/6b64b925bd8ffd4ad3c01e19c3277557df023dbf))
* **phase45:** auto-delegate sdd-init via skill() with manual fallback ([56f1aa8](https://github.com/hugoafj/ai-workflow-wizard/commit/56f1aa871954066dcf5236cc4bf68238c71e1a91))
* **phase45:** try direct file read of sdd-init SKILL.md when skill() not available ([#8](https://github.com/hugoafj/ai-workflow-wizard/issues/8)) ([15670e2](https://github.com/hugoafj/ai-workflow-wizard/commit/15670e227b8343b8b3c0820a533133e037b82233))
* **phase47:** add structured input guard for 5-option AI reviewer question ([#9](https://github.com/hugoafj/ai-workflow-wizard/issues/9)) ([6d71da1](https://github.com/hugoafj/ai-workflow-wizard/commit/6d71da1e3c4fd17654fbe60e5bc1239ef6b1a98a))
* **phase5:** reconnect orphaned metadata phase into wizard flow ([#11](https://github.com/hugoafj/ai-workflow-wizard/issues/11)) ([30d5d17](https://github.com/hugoafj/ai-workflow-wizard/commit/30d5d17f0a1ac7439410e8fb9cec8826af2c7ce1))
* **phase6:** add inline fallback + validation for Builder when delegation unavailable ([#46](https://github.com/hugoafj/ai-workflow-wizard/issues/46)) ([f4859b4](https://github.com/hugoafj/ai-workflow-wizard/commit/f4859b44060f17b4cd69f428f4a8fd132642a3e7))
* phase8 8.1d — Windsurf rule reinsert + coverage test_command ([#72](https://github.com/hugoafj/ai-workflow-wizard/issues/72)) ([a985bee](https://github.com/hugoafj/ai-workflow-wizard/commit/a985bee2517485b6cc0ab421e927472d70a52913))
* phase8 8.1d falls back to agent edit when yq unavailable ([#70](https://github.com/hugoafj/ai-workflow-wizard/issues/70)) ([af43f45](https://github.com/hugoafj/ai-workflow-wizard/commit/af43f453f660dc7e6ab3ae69a752a760f2e3a9c3))
* phase8 unconditional IDE mkdir + complete Windsurf/Devin dual-path support ([#48](https://github.com/hugoafj/ai-workflow-wizard/issues/48)) ([7eff226](https://github.com/hugoafj/ai-workflow-wizard/commit/7eff226b2ec9fa327f2ad074616beb6bfb3222c9))
* phase8 validates AGENTS.md wf-version footer is concrete semver ([#74](https://github.com/hugoafj/ai-workflow-wizard/issues/74)) ([a1e0cb9](https://github.com/hugoafj/ai-workflow-wizard/commit/a1e0cb999da442f27ca882176ee0f7365dd0b34c))
* **phase8:** install testing dependencies before commit (stack-aware) ([#20](https://github.com/hugoafj/ai-workflow-wizard/issues/20)) ([2e1843a](https://github.com/hugoafj/ai-workflow-wizard/commit/2e1843ac881330b24ffc152d862065fdaab0d311))
* **protocols:** archive wf-cicd, make cicd/sdd protocols flat-only single source ([#80](https://github.com/hugoafj/ai-workflow-wizard/issues/80)) ([ece59bc](https://github.com/hugoafj/ai-workflow-wizard/commit/ece59bc16b49e961e0886b8fbfabdbca7f075348))
* **protocols:** make wf-orchestrator conditional on ladder, routing, or tdd ([#79](https://github.com/hugoafj/ai-workflow-wizard/issues/79)) ([56f79ab](https://github.com/hugoafj/ai-workflow-wizard/commit/56f79ab133a5fed7a18ca4f190eb3fa9f137167c))
* realign openspec/config.yaml edits to gentle-ai canonical schema ([#62](https://github.com/hugoafj/ai-workflow-wizard/issues/62)) ([337b3b2](https://github.com/hugoafj/ai-workflow-wizard/commit/337b3b29e53ab91ddf3a3dcfe19854b515a08105))
* reinsert windsurf rule in AGENTS.md after staging copy ([#57](https://github.com/hugoafj/ai-workflow-wizard/issues/57)) ([bce897a](https://github.com/hugoafj/ai-workflow-wizard/commit/bce897ab0824c14e13fbe25e2f3fe9a69c13876a))
* release-please config use config-file instead of inline release-type ([f461dba](https://github.com/hugoafj/ai-workflow-wizard/commit/f461dba52b1f3edd233d2f144ae2932425efc8c5))
* release-please manifest commit path must include .wizard-manifests/ folder ([#43](https://github.com/hugoafj/ai-workflow-wizard/issues/43)) ([c6e27bf](https://github.com/hugoafj/ai-workflow-wizard/commit/c6e27bfc3f228fdb1cd9626e6c7f387ed9f37acd))
* release-please manifest integration - use gh to get PR branch and fix Python ([#38](https://github.com/hugoafj/ai-workflow-wizard/issues/38)) ([83d2450](https://github.com/hugoafj/ai-workflow-wizard/commit/83d245080627e2253aaf4bbd42427c5cb6c5eebd))
* rewrite manifest-generator.yml to use Python for valid JSON generation ([#28](https://github.com/hugoafj/ai-workflow-wizard/issues/28)) ([2f76491](https://github.com/hugoafj/ai-workflow-wizard/commit/2f76491301b5c10559587971054f694c19b43989))
* **skills:** correct findings from skills ↔ commands 1:1 audit ([#81](https://github.com/hugoafj/ai-workflow-wizard/issues/81)) ([eddd218](https://github.com/hugoafj/ai-workflow-wizard/commit/eddd218bef6adfb0ba888d1b29fb5960eac77fd6))
* **wf-cicd & phase47:** ensure all 5 AI reviewer options always shown ([#17](https://github.com/hugoafj/ai-workflow-wizard/issues/17)) ([d23351f](https://github.com/hugoafj/ai-workflow-wizard/commit/d23351f033b421604d9236579c47fc1e5875fd97))
* **wf-cicd:** ensure all 5 AI reviewer options always presented with fallback ([#15](https://github.com/hugoafj/ai-workflow-wizard/issues/15)) ([c576e07](https://github.com/hugoafj/ai-workflow-wizard/commit/c576e07fa9e3daeaafdd5c9fe5dad92d40ee6770))
* **wf-init:** reconnect phase5 and fix ci/cd state fields ([#13](https://github.com/hugoafj/ai-workflow-wizard/issues/13)) ([400f3e0](https://github.com/hugoafj/ai-workflow-wizard/commit/400f3e0b8d5f673087acdc88d00c8491d2604afa))
* wf-refresh must sync wf-version footer even without AGENTS.md content changes ([#52](https://github.com/hugoafj/ai-workflow-wizard/issues/52)) ([f0e0d6f](https://github.com/hugoafj/ai-workflow-wizard/commit/f0e0d6f7f95a17362bacf96bfa854f7873f6b97f))
* **wizard:** resolve judgment-day issues definitively (phase5 loop, R2 features, R0b) and remove scratch files ([#86](https://github.com/hugoafj/ai-workflow-wizard/issues/86)) ([2d3e5fe](https://github.com/hugoafj/ai-workflow-wizard/commit/2d3e5fe1003b2b115c3427fdb2bd92d0ca2033f8))
* yaml syntax error in manifest-generator workflow ([#32](https://github.com/hugoafj/ai-workflow-wizard/issues/32)) ([5770ae0](https://github.com/hugoafj/ai-workflow-wizard/commit/5770ae0efd07431b81471a2a408444cd6df922a8))

## [0.7.1-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.7.0-beta.1...v0.7.1-beta.1) (2026-08-15)

### Bug Fixes

* resolve judgment-day v0.7.0 refresh contracts bugs (C1-C3, M1-M5, B1-B9) ([f3a8801](https://github.com/hugoafj/ai-workflow-wizard/commit/f3a8801))
* harden non-tty prompts, portable diff guard, staged bridge ([c282aa5](https://github.com/hugoafj/ai-workflow-wizard/commit/c282aa5))
* portable hashing, safe path handling, and refresh state guards ([144b046](https://github.com/hugoafj/ai-workflow-wizard/commit/144b046))
* complete builder-driven /wf-refresh state and refresh guards ([4d211fe](https://github.com/hugoafj/ai-workflow-wizard/commit/4d211fe))
* resolve 25 workflow issues across refresh, init, and docs ([b84c9e1](https://github.com/hugoafj/ai-workflow-wizard/commit/b84c9e1))
* deletion detection, approval gating, and phase7 cat gate ([93b5de9](https://github.com/hugoafj/ai-workflow-wizard/commit/93b5de9))
* resolve /wf-refresh executability, semver migration, and AGENTS.md drift ([dbedf32](https://github.com/hugoafj/ai-workflow-wizard/commit/dbedf32))
* stop sourcing lib/state.md as a shell script ([369c86f](https://github.com/hugoafj/ai-workflow-wizard/commit/369c86f))
* phase file robustness and git validation ([cafebac](https://github.com/hugoafj/ai-workflow-wizard/commit/cafebac))
* null-safe arrays and managed paths in core ([8c539c5](https://github.com/hugoafj/ai-workflow-wizard/commit/8c539c5))
* phase 8 promotion, git handling, and manifest recompute ([1d93c65](https://github.com/hugoafj/ai-workflow-wizard/commit/1d93c65))
* schema v3 migration, state helpers, and refresh core ([b18097a](https://github.com/hugoafj/ai-workflow-wizard/commit/b18097a))
* resolve pre-merge audit issues across wf-init/wf-refresh ([26d68e7](https://github.com/hugoafj/ai-workflow-wizard/commit/26d68e7))
* resolve pre-merge audit issues across wf-init, wf-refresh, templates and docs ([9e41a73](https://github.com/hugoafj/ai-workflow-wizard/commit/9e41a73))
* apply P0 fixes from judgment-day handoff ([1cb22f9](https://github.com/hugoafj/ai-workflow-wizard/commit/1cb22f9))
* apply P1 fixes from judgment-day handoff ([62e14e4](https://github.com/hugoafj/ai-workflow-wizard/commit/62e14e4))
* apply P2 fixes from judgment-day handoff ([6705f99](https://github.com/hugoafj/ai-workflow-wizard/commit/6705f99))
* correct gemini pr-agent env var and claude model after Context7 check ([ef30832](https://github.com/hugoafj/ai-workflow-wizard/commit/ef30832))

### Documentation

* sync AI workflow docs and translate non-English strings ([8c367f8](https://github.com/hugoafj/ai-workflow-wizard/commit/8c367f8))

### Chores

* add Devin agent rules for subagent delegation and CodeGraph ([93eefc0](https://github.com/hugoafj/ai-workflow-wizard/commit/93eefc0))
* add Windsurf workspace workflow for /sdd-new ([261deb4](https://github.com/hugoafj/ai-workflow-wizard/commit/261deb4))
* ignore .codegraph and translate temp-files/sdd-new.md to English ([3cde588](https://github.com/hugoafj/ai-workflow-wizard/commit/3cde588))

## [0.7.0-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.6.7-beta.1...v0.7.0-beta.1) (2026-08-13)


### Features

* refactor /wf-refresh to builder-driven migration mechanism ([#84](https://github.com/hugoafj/ai-workflow-wizard/issues/84)) ([cdda4a4](https://github.com/hugoafj/ai-workflow-wizard/commit/cdda4a4961edde5c7df39abbd3c567ecf3ad4b42))

## [0.6.7-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.6.6-beta.1...v0.6.7-beta.1) (2026-08-13)


### Bug Fixes

* **skills:** correct findings from skills ↔ commands 1:1 audit ([#81](https://github.com/hugoafj/ai-workflow-wizard/issues/81)) ([eddd218](https://github.com/hugoafj/ai-workflow-wizard/commit/eddd218bef6adfb0ba888d1b29fb5960eac77fd6))

## [0.6.6-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.6.5-beta.1...v0.6.6-beta.1) (2026-08-10)


### Bug Fixes

* implement two-phase version check to prevent infinite loop in wf-refresh ([#76](https://github.com/hugoafj/ai-workflow-wizard/issues/76)) ([233d7d7](https://github.com/hugoafj/ai-workflow-wizard/commit/233d7d797203d01cb02cf1a04a616a377cb8e215))
* **install:** add codex commands, windsurf legacy paths, and devin detection ([#78](https://github.com/hugoafj/ai-workflow-wizard/issues/78)) ([78e78c4](https://github.com/hugoafj/ai-workflow-wizard/commit/78e78c42c7b0211919eaa199de9cabd72c616c88))
* **protocols:** archive wf-cicd, make cicd/sdd protocols flat-only single source ([#80](https://github.com/hugoafj/ai-workflow-wizard/issues/80)) ([ece59bc](https://github.com/hugoafj/ai-workflow-wizard/commit/ece59bc16b49e961e0886b8fbfabdbca7f075348))
* **protocols:** make wf-orchestrator conditional on ladder, routing, or tdd ([#79](https://github.com/hugoafj/ai-workflow-wizard/issues/79)) ([56f79ab](https://github.com/hugoafj/ai-workflow-wizard/commit/56f79ab133a5fed7a18ca4f190eb3fa9f137167c))

## [0.6.5-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.6.4-beta.1...v0.6.5-beta.1) (2026-08-09)


### Bug Fixes

* phase8 validates AGENTS.md wf-version footer is concrete semver ([#74](https://github.com/hugoafj/ai-workflow-wizard/issues/74)) ([a1e0cb9](https://github.com/hugoafj/ai-workflow-wizard/commit/a1e0cb999da442f27ca882176ee0f7365dd0b34c))

## [0.6.4-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.6.3-beta.1...v0.6.4-beta.1) (2026-08-09)


### Bug Fixes

* phase8 8.1d — Windsurf rule reinsert + coverage test_command ([#72](https://github.com/hugoafj/ai-workflow-wizard/issues/72)) ([a985bee](https://github.com/hugoafj/ai-workflow-wizard/commit/a985bee2517485b6cc0ab421e927472d70a52913))

## [0.6.3-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.6.2-beta.1...v0.6.3-beta.1) (2026-08-09)


### Bug Fixes

* phase8 8.1d falls back to agent edit when yq unavailable ([#70](https://github.com/hugoafj/ai-workflow-wizard/issues/70)) ([af43f45](https://github.com/hugoafj/ai-workflow-wizard/commit/af43f453f660dc7e6ab3ae69a752a760f2e3a9c3))

## [0.6.2-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.6.1-beta.1...v0.6.2-beta.1) (2026-08-09)


### Bug Fixes

* phase45 creates AGENTS.md greenfield for Windsurf legacy bridge ([#68](https://github.com/hugoafj/ai-workflow-wizard/issues/68)) ([23b800a](https://github.com/hugoafj/ai-workflow-wizard/commit/23b800a6a708466c6b00ab2cf7175f2c745b54ce))

## [0.6.1-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.6.0-beta.1...v0.6.1-beta.1) (2026-08-09)


### Bug Fixes

* conditional CLAUDE.md, complete wf-cleanup, add IDEs/CLIs settings ([#66](https://github.com/hugoafj/ai-workflow-wizard/issues/66)) ([4e62dc4](https://github.com/hugoafj/ai-workflow-wizard/commit/4e62dc4faafdd8196d43f622e73ba5df6e70b53d))

## [0.6.0-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.5.2-beta.1...v0.6.0-beta.1) (2026-08-08)


### Features

* add HARD STOP RULE to AGENTS.md router ([#64](https://github.com/hugoafj/ai-workflow-wizard/issues/64)) ([9474a63](https://github.com/hugoafj/ai-workflow-wizard/commit/9474a638e195f566d941201821b0e7b0ce92a8ca))

## [0.5.2-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.5.1-beta.1...v0.5.2-beta.1) (2026-08-08)


### Bug Fixes

* realign openspec/config.yaml edits to gentle-ai canonical schema ([#62](https://github.com/hugoafj/ai-workflow-wizard/issues/62)) ([337b3b2](https://github.com/hugoafj/ai-workflow-wizard/commit/337b3b29e53ab91ddf3a3dcfe19854b515a08105))

## [0.5.1-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.5.0-beta.1...v0.5.1-beta.1) (2026-08-08)


### Bug Fixes

* apply orphaned testing extras and fragments during build ([#60](https://github.com/hugoafj/ai-workflow-wizard/issues/60)) ([8a64e7b](https://github.com/hugoafj/ai-workflow-wizard/commit/8a64e7b36252ce7eb2f79079917565c1d5ee925f))

## [0.5.0-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.4.5-beta.1...v0.5.0-beta.1) (2026-08-08)


### Features

* add mandatory hard stops for SDD workflow enforcement ([#59](https://github.com/hugoafj/ai-workflow-wizard/issues/59)) ([29b14eb](https://github.com/hugoafj/ai-workflow-wizard/commit/29b14eb8301253d48e67355d47b9a4b9f878f9e8))


### Bug Fixes

* reinsert windsurf rule in AGENTS.md after staging copy ([#57](https://github.com/hugoafj/ai-workflow-wizard/issues/57)) ([bce897a](https://github.com/hugoafj/ai-workflow-wizard/commit/bce897ab0824c14e13fbe25e2f3fe9a69c13876a))

## [0.4.5-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.4.4-beta.1...v0.4.5-beta.1) (2026-08-08)


### Bug Fixes

* phase0b sync order + phase45 hardcoded paths ([#55](https://github.com/hugoafj/ai-workflow-wizard/issues/55)) ([e864b09](https://github.com/hugoafj/ai-workflow-wizard/commit/e864b0920d7fc16bb42ac6d3c42330e0ca8e9db5))

## [0.4.4-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.4.3-beta.1...v0.4.4-beta.1) (2026-08-06)


### Bug Fixes

* wf-refresh must sync wf-version footer even without AGENTS.md content changes ([#52](https://github.com/hugoafj/ai-workflow-wizard/issues/52)) ([f0e0d6f](https://github.com/hugoafj/ai-workflow-wizard/commit/f0e0d6f7f95a17362bacf96bfa854f7873f6b97f))

## [0.4.3-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.4.2-beta.1...v0.4.3-beta.1) (2026-08-06)


### Bug Fixes

* correct gentle-ai links, clarify install vs usage flow, enforce YAML atomicity ([b9df2dd](https://github.com/hugoafj/ai-workflow-wizard/commit/b9df2ddcca2172cb780dd218b02bf0ddce2ee217))

## [0.4.2-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.4.1-beta.1...v0.4.2-beta.1) (2026-08-06)


### Bug Fixes

* phase8 unconditional IDE mkdir + complete Windsurf/Devin dual-path support ([#48](https://github.com/hugoafj/ai-workflow-wizard/issues/48)) ([7eff226](https://github.com/hugoafj/ai-workflow-wizard/commit/7eff226b2ec9fa327f2ad074616beb6bfb3222c9))

## [0.4.1-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.4.0-beta.1...v0.4.1-beta.1) (2026-08-04)


### Bug Fixes

* **phase6:** add inline fallback + validation for Builder when delegation unavailable ([#46](https://github.com/hugoafj/ai-workflow-wizard/issues/46)) ([f4859b4](https://github.com/hugoafj/ai-workflow-wizard/commit/f4859b44060f17b4cd69f428f4a8fd132642a3e7))

## [0.4.0-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.3.3-beta.1...v0.4.0-beta.1) (2026-08-04)


### Features

* support both .windsurf/ and .devin/ IDE paths for wizard compatibility ([#44](https://github.com/hugoafj/ai-workflow-wizard/issues/44)) ([1e8bb71](https://github.com/hugoafj/ai-workflow-wizard/commit/1e8bb712efae2d3257f29a925735e26c125cac77))

## [0.3.3-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.3.2-beta.1...v0.3.3-beta.1) (2026-08-04)


### Bug Fixes

* /wf-refresh Layer 2 must always update footer and state ([#41](https://github.com/hugoafj/ai-workflow-wizard/issues/41)) ([bfefa16](https://github.com/hugoafj/ai-workflow-wizard/commit/bfefa16819f1b62c86f435343bf3360f8a50863c))
* release-please manifest commit path must include .wizard-manifests/ folder ([#43](https://github.com/hugoafj/ai-workflow-wizard/issues/43)) ([c6e27bf](https://github.com/hugoafj/ai-workflow-wizard/commit/c6e27bfc3f228fdb1cd9626e6c7f387ed9f37acd))

## [0.3.2-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.3.1-beta.1...v0.3.2-beta.1) (2026-08-04)


### Bug Fixes

* avoid literal newlines inside YAML block scalar (fixes invalid workflow syntax) ([#35](https://github.com/hugoafj/ai-workflow-wizard/issues/35)) ([b322f03](https://github.com/hugoafj/ai-workflow-wizard/commit/b322f03e5ba6796feae3be1b9cce010a57680326))
* integrate manifest regeneration into release-please workflow ([#37](https://github.com/hugoafj/ai-workflow-wizard/issues/37)) ([46a52cd](https://github.com/hugoafj/ai-workflow-wizard/commit/46a52cde3915ef905cd21b57e1f07c9a06f39fd1))
* release-please manifest integration - use gh to get PR branch and fix Python ([#38](https://github.com/hugoafj/ai-workflow-wizard/issues/38)) ([83d2450](https://github.com/hugoafj/ai-workflow-wizard/commit/83d245080627e2253aaf4bbd42427c5cb6c5eebd))
* yaml syntax error in manifest-generator workflow ([#32](https://github.com/hugoafj/ai-workflow-wizard/issues/32)) ([5770ae0](https://github.com/hugoafj/ai-workflow-wizard/commit/5770ae0efd07431b81471a2a408444cd6df922a8))

## [0.3.1-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.3.0-beta.1...v0.3.1-beta.1) (2026-08-04)


### Bug Fixes

* clean VERSION newline in manifest-generator to prevent invalid filenames ([1f881e7](https://github.com/hugoafj/ai-workflow-wizard/commit/1f881e7fec2ddf7468ce594b851f003b2b590658))

## [0.3.0-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.2.1-beta.1...v0.3.0-beta.1) (2026-08-04)


### Features

* implement auto-generated WIZARD_MANIFEST.json ([#26](https://github.com/hugoafj/ai-workflow-wizard/issues/26)) ([0063415](https://github.com/hugoafj/ai-workflow-wizard/commit/0063415dbae3f525c6dd862daa867135e15afa79))
* manifest versioning with checksums and recovery guide ([#29](https://github.com/hugoafj/ai-workflow-wizard/issues/29)) ([ba3800e](https://github.com/hugoafj/ai-workflow-wizard/commit/ba3800e40fd4fbb61b876f7e8571c030bf736521))


### Bug Fixes

* rewrite manifest-generator.yml to use Python for valid JSON generation ([#28](https://github.com/hugoafj/ai-workflow-wizard/issues/28)) ([2f76491](https://github.com/hugoafj/ai-workflow-wizard/commit/2f76491301b5c10559587971054f694c19b43989))

## [0.2.1-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.2.0-beta.1...v0.2.1-beta.1) (2026-08-04)


### Bug Fixes

* make Phase -1 auto-execute at wf-refresh start ([#24](https://github.com/hugoafj/ai-workflow-wizard/issues/24)) ([4b70ff0](https://github.com/hugoafj/ai-workflow-wizard/commit/4b70ff07a00eb02bf616ad52b3a0c986777aa5a0))

## [0.2.0-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.1.8-beta.1...v0.2.0-beta.1) (2026-08-04)


### Features

* atomic wf-refresh versioning and custom content protection ([#22](https://github.com/hugoafj/ai-workflow-wizard/issues/22)) ([a1c72c2](https://github.com/hugoafj/ai-workflow-wizard/commit/a1c72c25e435a1b061965b364cc8616a60192e54))

## [0.1.8-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.1.7-beta.1...v0.1.8-beta.1) (2026-08-03)


### Bug Fixes

* **phase8:** install testing dependencies before commit (stack-aware) ([#20](https://github.com/hugoafj/ai-workflow-wizard/issues/20)) ([2e1843a](https://github.com/hugoafj/ai-workflow-wizard/commit/2e1843ac881330b24ffc152d862065fdaab0d311))

## [0.1.7-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.1.6-beta.1...v0.1.7-beta.1) (2026-08-03)


### Bug Fixes

* **phase1:** ensure wf_phase_done executes before phase2 to update state correctly ([#18](https://github.com/hugoafj/ai-workflow-wizard/issues/18)) ([9869728](https://github.com/hugoafj/ai-workflow-wizard/commit/9869728243cead4765dfe95f4e1499fd9eb29878))

## [0.1.6-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.1.5-beta.1...v0.1.6-beta.1) (2026-08-03)


### Bug Fixes

* **wf-cicd & phase47:** ensure all 5 AI reviewer options always shown ([#17](https://github.com/hugoafj/ai-workflow-wizard/issues/17)) ([d23351f](https://github.com/hugoafj/ai-workflow-wizard/commit/d23351f033b421604d9236579c47fc1e5875fd97))
* **wf-cicd:** ensure all 5 AI reviewer options always presented with fallback ([#15](https://github.com/hugoafj/ai-workflow-wizard/issues/15)) ([c576e07](https://github.com/hugoafj/ai-workflow-wizard/commit/c576e07fa9e3daeaafdd5c9fe5dad92d40ee6770))

## [0.1.5-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.1.4-beta.1...v0.1.5-beta.1) (2026-08-03)


### Bug Fixes

* **wf-init:** reconnect phase5 and fix ci/cd state fields ([#13](https://github.com/hugoafj/ai-workflow-wizard/issues/13)) ([400f3e0](https://github.com/hugoafj/ai-workflow-wizard/commit/400f3e0b8d5f673087acdc88d00c8491d2604afa))

## [0.1.4-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.1.3-beta.1...v0.1.4-beta.1) (2026-07-29)


### Bug Fixes

* **phase5:** reconnect orphaned metadata phase into wizard flow ([#11](https://github.com/hugoafj/ai-workflow-wizard/issues/11)) ([30d5d17](https://github.com/hugoafj/ai-workflow-wizard/commit/30d5d17f0a1ac7439410e8fb9cec8826af2c7ce1))

## [0.1.3-beta.1](https://github.com/hugoafj/ai-workflow-wizard/compare/v0.1.2-beta.1...v0.1.3-beta.1) (2026-07-29)


### Bug Fixes

* **phase47:** add structured input guard for 5-option AI reviewer question ([#9](https://github.com/hugoafj/ai-workflow-wizard/issues/9)) ([6d71da1](https://github.com/hugoafj/ai-workflow-wizard/commit/6d71da1e3c4fd17654fbe60e5bc1239ef6b1a98a))

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
