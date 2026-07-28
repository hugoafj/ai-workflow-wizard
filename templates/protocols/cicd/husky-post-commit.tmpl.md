# husky-post-commit — workflow drift detector hook
#
# Husky v9+ (2024+): hooks are direct scripts. Do NOT include shebang
# or the line . "$(dirname -- "$0")/_/husky.sh" — DEPRECATED since v9, BROKEN in v10.
#
# SINGLE SOURCE of the drift detection body: NOT duplicated here.
# The Builder inserts the body from templates/protocols/cicd/hook.post-commit.tmpl.md

{{DRIFT_BODY: protocols/cicd/hook.post-commit.tmpl.md}}
