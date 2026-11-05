# GGA file patterns

<!--
  SINGLE SOURCE of the FILE_PATTERNS / EXCLUDE_PATTERNS written to the project's `.gga`
  file (builder-heavy.py, write_cicd). Verified against GGA 2.10.1 (get_staged_files):

  - Both values are COMMA-separated lists. Brace expansion is NOT supported, so
    `**/*.{ts,tsx}` is split on its inner comma into pieces that match nothing.
  - A pattern starting with `*` is a SUFFIX match on the whole staged path: `*.ts`
    matches `src/a.ts`. Any other pattern is matched as a shell glob against the full
    path or the basename (`dist/**` matches everything under dist/).
  - When no staged file matches, `gga run` prints "No matching files staged for commit"
    and exits 0, so a wrong pattern passes silently instead of failing.

  `file_patterns_by_framework` is keyed by `discovery.stack.framework`; a framework that is
  not listed uses `file_patterns`. State overrides win: `state.ci.gga_file_patterns` and
  `state.ci.gga_exclude_patterns`.
-->

```json
{
  "file_patterns": "*.ts,*.tsx,*.js,*.jsx",
  "exclude_patterns": "*.test.ts,*.test.tsx,*.spec.ts,*.spec.tsx,*.d.ts,dist/**,build/**",
  "file_patterns_by_framework": {
    "vue": "*.ts,*.tsx,*.js,*.jsx,*.vue",
    "nuxt": "*.ts,*.tsx,*.js,*.jsx,*.vue"
  }
}
```
