#!/usr/bin/env python3
"""
builder-heavy.py — Deterministic wizard builder: B7-B9 + build_plan registration.

Replaces the builder-heavy sub-agent with a deterministic inline pipeline so that
wf-refresh runs B7-B9 exactly the same way every time.

Usage:
  python3 builder-heavy.py --state <path> --staging <path> --raw <WF_RAW> --wf-dir <WF_DIR>

Exit codes:
  0  success
  1  unrecoverable error (missing state, unresolved placeholder, failed download)

Stdlib only. No sub-agent delegation.
"""

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.request

# Reuse helpers from builder-core (same WF_DIR install).
import importlib.util

_HERE = os.path.dirname(os.path.abspath(__file__))
_SPEC = importlib.util.spec_from_file_location("builder_core", os.path.join(_HERE, "builder-core.py"))
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load builder-core.py from %s" % _HERE)
builder_core = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(builder_core)


# ---------------------------------------------------------------------------
# B7. Commands
# ---------------------------------------------------------------------------

# filename -> frontmatter formatter per IDE
# (cmd, description) -> per-IDE command file contents
COMMAND_PATHS = {
    "claude-code": (".claude/commands/%s.md", None),
    "opencode": (".opencode/commands/%s.md", None),
    "cursor": (".cursor/commands/%s.md", None),
    "codex": (".codex/commands/%s.md", None),
    "windsurf": (".windsurf/workflows/%s.md", "description"),
    "kiro": (".kiro/steering/%s.md", "inclusion"),
    "vscode-copilot": (".github/prompts/%s.prompt.md", "agent"),
    "antigravity": (".agents/skills/%s/SKILL.md", "name"),
}

FRONTMATTER = {
    "description": "---\ndescription: \"%s\"\n---\n\n",
    "inclusion": "---\ninclusion: manual\ndescription: \"%s\"\n---\n\n",
    "agent": "---\nagent: 'agent'\ndescription: \"%s\"\n---\n\n",
    "name": "---\nname: %s\ndescription: \"%s\"\n---\n\n",
}

# Commands that ship in every IDE: the 3 maintenance commands are always included.
ALWAYS_COMMANDS = ["wf-worktree", "wf-settings", "wf-onboard"]


def active_command_names(state):
    """Return the command list for this state (B7)."""
    names = list(ALWAYS_COMMANDS)
    ladder = builder_core.bool_feature(state, "decision_ladder")
    tdd = builder_core.bool_feature(state, "tdd_protocol")
    routing = builder_core.bool_feature(state, "routing_abc")
    if ladder:
        names.append("wf-ladder")
    if tdd:
        names.append("wf-tdd")
    if routing or ladder or tdd:
        names.append("wf-orchestrator")
    if routing:
        names.append("wf-sdd-trigger")
    return names


def command_description(raw, cmd):
    """Read the description from templates/commands/meta.md.

    The description column is located by header name, not hardcoded index:
    meta.md grew a 4th column (scope | category | description) in eddd218,
    which broke the old cells[2] lookup.
    """
    meta_url = builder_core.base_url(raw, "templates/commands/meta.md")
    try:
        meta = builder_core.fetch_with_retries(meta_url)
    except RuntimeError:
        return cmd
    lines = meta.splitlines()
    desc_col = None
    for line in lines:
        if "|" not in line:
            continue
        cells = [c.strip().lower() for c in line.split("|")]
        if any("description" in c for c in cells):
            desc_col = next((i for i, c in enumerate(cells) if "description" in c), None)
            break
    for line in lines:
        if "|" not in line or cmd not in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 2 and cells[1] == cmd:
            if desc_col is not None and desc_col < len(cells):
                return cells[desc_col]
            # No header found: fall back to the last non-empty cell.
            return next((c for c in reversed(cells) if c), cmd)
    return cmd


def write_commands(raw, state, staging):
    """Write per-IDE command files (B7)."""
    created = []
    cmds = active_command_names(state)
    ides = builder_core.active_ides(state)
    for cmd in cmds:
        url = builder_core.base_url(raw, "templates/commands/%s/_base.md" % (cmd))
        try:
            body = builder_core.fetch_with_retries(url)
        except RuntimeError:
            continue
        body = builder_core.strip_internal_comment(body)
        body = builder_core.resolve_if_blocks(body, state, raw)
        desc = command_description(raw, cmd)
        for ide in ides:
            if ide not in COMMAND_PATHS:
                continue
            rel_tmpl, fm_kind = COMMAND_PATHS[ide]
            rel = rel_tmpl % cmd
            target = os.path.join(staging, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            content = body + "\n"
            if fm_kind == "name":
                content = FRONTMATTER[fm_kind] % (cmd, desc) + content
            elif fm_kind:
                content = FRONTMATTER[fm_kind] % desc + content
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(content)
            created.append(rel)
    return created


# ---------------------------------------------------------------------------
# B8. Hook
# ---------------------------------------------------------------------------

def write_hook(raw, state, staging):
    """Install the post-commit drift-check hook (B8 hook dual).

    Conventional commits (phase47 L59) migrate the drift hook to Husky: when
    ``ci.conventional_commits`` is true the hook lives in ``.husky/post-commit``
    alongside ``commit-msg``; otherwise it is a plain ``.git/hooks/post-commit``.
    Never both (plan L187: husky XOR .git/hooks).
    """
    if not builder_core.bool_feature(state, "hook"):
        return []
    created = []
    # Husky is used when conventional commits create .husky/ (commit-msg), or
    # when the project already has a .husky directory.
    husky_dir = os.path.join(staging, ".husky")
    conventional = bool(builder_core.get_state_value(state, "ci.conventional_commits", False))
    if conventional or os.path.isdir(husky_dir):
        tmpl_url = builder_core.base_url(raw, "templates/protocols/cicd/husky-post-commit.tmpl.md")
        try:
            tmpl = builder_core.fetch_with_retries(tmpl_url)
        except RuntimeError:
            return []
        tmpl = builder_core.extract_block(tmpl, "bash")
        # Replace the {{DRIFT_BODY: ...}} marker with the hook body.
        hook_body_url = builder_core.base_url(raw, "templates/protocols/cicd/hook.post-commit.tmpl.md")
        hook_body = builder_core.fetch_with_retries(hook_body_url)
        hook_body = builder_core.extract_block(hook_body, "bash")
        # Husky hooks are direct scripts: strip the body's shebang (plan: body
        # SIN fence, SIN shebang for husky; the plain .git/hooks variant keeps it).
        if hook_body.startswith("#!/"):
            hook_body = hook_body.split("\n", 1)[1]
        tmpl = re.sub(r"\{\{DRIFT_BODY:[^}]*\}\}", lambda m: hook_body, tmpl)
        target = os.path.join(husky_dir, "post-commit")
        os.makedirs(husky_dir, exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(tmpl + "\n")
        os.chmod(target, 0o755)
        created.append(os.path.relpath(target, staging))
        return created

    # Plain git hook.
    git_dir = os.path.join(staging, ".git", "hooks")
    os.makedirs(git_dir, exist_ok=True)
    hook_url = builder_core.base_url(raw, "templates/protocols/cicd/hook.post-commit.tmpl.md")
    hook_body = builder_core.fetch_with_retries(hook_url)
    hook_body = builder_core.extract_block(hook_body, "bash")
    target = os.path.join(git_dir, "post-commit")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(hook_body + "\n")
    os.chmod(target, 0o755)
    created.append(os.path.relpath(target, staging))
    return created


# ---------------------------------------------------------------------------
# B8. Testing configs
# ---------------------------------------------------------------------------

def write_testing_configs(raw, state, staging):
    """Write vitest/playwright configs with fragment injection (B8 testing)."""
    created = []
    layers = builder_core.normalize_layers(state)

    # Vitest (unit/integration layers).
    if "unit" in layers or "integration" in layers:
        cfg = builder_core.fetch_with_retries(
            builder_core.base_url(raw, "templates/protocols/testing/vitest.config.tmpl.md"))
        cfg = builder_core.extract_block(cfg, "typescript")
        # Inject coverage fragment inside the test: { } block.
        frag = builder_core.fetch_with_retries(
            builder_core.base_url(raw, "templates/protocols/testing/coverage-thresholds.tmpl.md"))
        frag = builder_core.strip_prose_header(frag)
        threshold = builder_core.get_state_value(state, "testing.coverage_threshold", "80")
        frag = frag.replace("{{threshold}}", str(threshold))
        # Indent the fragment to sit inside the test: { } block (F11).
        frag = textwrap.indent(frag, "    ")
        cfg = cfg.replace("test: {\n", "test: {\n" + frag + "\n")
        target = os.path.join(staging, "vitest.config.ts")
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(cfg + "\n")
        created.append(os.path.relpath(target, staging))

    # Playwright (e2e layer).
    if "e2e" in layers:
        cfg = builder_core.fetch_with_retries(
            builder_core.base_url(raw, "templates/protocols/testing/playwright.config.tmpl.md"))
        cfg = builder_core.extract_block(cfg, "typescript")
        frag = builder_core.fetch_with_retries(
            builder_core.base_url(raw, "templates/protocols/testing/visual-snapshots.tmpl.md"))
        frag = builder_core.strip_prose_header(frag)
        # Insert before the final closing brace of defineConfig, indented to
        # match the surrounding defineConfig block (F11).
        frag = textwrap.indent(frag, "  ")
        cfg = cfg.rstrip()
        if cfg.endswith("})"):
            cfg = cfg[: -2] + frag + "\n})"
        target = os.path.join(staging, "playwright.config.ts")
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(cfg + "\n")
        created.append(os.path.relpath(target, staging))

        # POM extra (field report B3): phase 4.6b offers "Page Object Model"
        # in its menu and the docs promised e2e/pages/, but neither builder
        # generated anything. Stage the minimal scaffold when active; real
        # page objects emerge with features via sdd-apply following the
        # AGENTS.md convention line.
        if builder_core.get_state_value(state, "testing.page_object_model", False):
            pom = builder_core.fetch_with_retries(
                builder_core.base_url(raw, "templates/protocols/testing/pom-example.tmpl.md"))
            pom = builder_core.extract_block(pom, "typescript")
            pom_target = os.path.join(staging, "e2e", "pages", "HomePage.ts")
            os.makedirs(os.path.dirname(pom_target), exist_ok=True)
            with open(pom_target, "w", encoding="utf-8") as fh:
                fh.write(pom + "\n")
            created.append(os.path.relpath(pom_target, staging))
    return created


# ---------------------------------------------------------------------------
# B8b. CI/CD
# ---------------------------------------------------------------------------

def read_package_version():
    """Read the version field from package.json in the project root (cwd).

    Returns the version string, or None when package.json is absent, invalid,
    or has no version field.
    """
    try:
        with open(os.path.join(os.getcwd(), "package.json"), "r", encoding="utf-8") as fh:
            pkg = json.load(fh)
        version = pkg.get("version")
        return str(version) if version else None
    except (OSError, ValueError):
        return None


def resolve_cicd_placeholder(state, key):
    """Resolve CI/CD specific placeholders."""
    value = builder_core.get_state_value(state, key, None)
    if value is not None:
        return value if isinstance(value, str) else json.dumps(value)
    raise ValueError("unresolved CI/CD placeholder: %s" % key)


def write_cicd(raw, state, staging):
    """Write CI/CD workflows and configs (B8b)."""
    created = []
    ci = builder_core.get_state_value(state, "ci", {}) or {}
    if not isinstance(ci, dict):
        ci = {}

    release_please = builder_core.bool_feature(state, "release_please") or \
        bool(ci.get("release_please", False))
    cd = builder_core.bool_feature(state, "cd")
    cicd = builder_core.bool_feature(state, "ci")
    ai_reviewer = ci.get("ai_reviewer", "copilot")
    cicd_dir = builder_core.base_url(raw, "templates/protocols/cicd")

    # --- Quality guard workflow (only under full CI).
    if cicd:
        qg_url = builder_core.base_url(raw, "templates/protocols/cicd/variants/quality-guard.yml.md")
        qg = builder_core.fetch_with_retries(qg_url)
        qg = builder_core.strip_prose_header(qg, keep_notes=True)
        qg = builder_core.resolve_if_blocks(qg, state, raw)
        qg = builder_core.resolve_gh_escapes(qg)
        qg = qg.replace("{{node_version}}", str(builder_core._coalesce(state, "discovery.node_engine", "22")))
        qg = qg.replace("{{npm_major}}", str(builder_core._coalesce(state, "discovery.npm_major", "10")))
        if builder_core.unresolved_placeholders(qg):
            raise ValueError("unresolved placeholders in quality-guard.yml")
        qg_target = os.path.join(staging, ".github", "workflows", "quality-guard.yml")
        os.makedirs(os.path.dirname(qg_target), exist_ok=True)
        with open(qg_target, "w", encoding="utf-8") as fh:
            fh.write(qg + "\n")
        created.append(os.path.relpath(qg_target, staging))

    # --- AI review workflow (gga / claude / gemini) — only under full CI.
    if cicd and ai_reviewer in ("gga", "claude", "gemini"):
        if ai_reviewer == "gga":
            # .gga config + gga-review workflow.
            gga_cfg = builder_core.fetch_with_retries(builder_core.base_url(raw, "templates/protocols/cicd/variants/gga-config.tmpl.md"))
            gga_cfg = builder_core.extract_block(gga_cfg, "yaml")
            gga_provider = ci.get("gga_provider", "claude")
            gga_cfg = gga_cfg.replace("{{provider}}", gga_provider)
            file_patterns = ci.get("gga_file_patterns", "**/*.{ts,tsx,js,jsx}")
            exclude_patterns = ci.get("gga_exclude_patterns", "**/*.test.{ts,tsx},**/*.spec.{ts,tsx},dist/**,build/**")
            gga_cfg = gga_cfg.replace("{{file_patterns}}", file_patterns)
            gga_cfg = gga_cfg.replace("{{exclude_patterns}}", exclude_patterns)
            pr_base = builder_core.get_state_value(state, "discovery.default_branch", "main")
            gga_cfg = gga_cfg.replace("{{pr_base_branch}}", pr_base)
            gga_target = os.path.join(staging, ".gga", "config.yml")
            os.makedirs(os.path.dirname(gga_target), exist_ok=True)
            with open(gga_target, "w", encoding="utf-8") as fh:
                fh.write(gga_cfg + "\n")
            created.append(os.path.relpath(gga_target, staging))

            gga_wf = builder_core.fetch_with_retries(builder_core.base_url(raw, "templates/protocols/cicd/variants/gga-review.yml.md"))
            gga_wf = builder_core.strip_prose_header(gga_wf, keep_notes=True)
            provider_cli = {"claude": "@anthropic-ai/claude-code", "gemini": "@google/gemini-cli", "codex": "@openai/codex"}.get(gga_provider, "@anthropic-ai/claude-code")
            provider_secret = {"claude": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "codex": "OPENAI_API_KEY"}.get(gga_provider, "ANTHROPIC_API_KEY")
            gga_wf = gga_wf.replace("{{provider_cli}}", provider_cli)
            gga_wf = gga_wf.replace("{{provider_secret}}", provider_secret)
            # The {{provider_secret}} inside `${{ '{{' }}...{{ '}}' }}` escapes is
            # already replaced above; resolve the remaining escape wrappers and
            # any bare inner placeholder names.
            def _gga_resolver(key):
                if key == "provider_cli":
                    return provider_cli
                if key == "provider_secret":
                    return provider_secret
                raise KeyError(key)

            gga_wf = builder_core.resolve_gh_escapes(gga_wf, _gga_resolver)
            if builder_core.unresolved_placeholders(gga_wf):
                raise ValueError("unresolved placeholders in gga-review.yml")
            gga_wf_target = os.path.join(staging, ".github", "workflows", "gga-review.yml")
            os.makedirs(os.path.dirname(gga_wf_target), exist_ok=True)
            with open(gga_wf_target, "w", encoding="utf-8") as fh:
                fh.write(gga_wf + "\n")
            created.append(os.path.relpath(gga_wf_target, staging))
        elif ai_reviewer == "claude":
            cl = builder_core.fetch_with_retries(builder_core.base_url(raw, "templates/protocols/cicd/variants/claude-review.yml.md"))
            cl = builder_core.strip_prose_header(cl, keep_notes=True)
            inline = ci.get("inline_suggestions", True)
            if not inline:
                cl = re.sub(r"^\s*claude_args:\s*\|.*?^\s*[^\s].*$", "", cl, flags=re.MULTILINE | re.DOTALL)
            cl_target = os.path.join(staging, ".github", "workflows", "claude-review.yml")
            os.makedirs(os.path.dirname(cl_target), exist_ok=True)
            with open(cl_target, "w", encoding="utf-8") as fh:
                fh.write(cl + "\n")
            created.append(os.path.relpath(cl_target, staging))
        elif ai_reviewer == "gemini":
            gm = builder_core.fetch_with_retries(builder_core.base_url(raw, "templates/protocols/cicd/variants/gemini-review.yml.md"))
            gm = builder_core.strip_prose_header(gm, keep_notes=True)
            auto_improve = ci.get("auto_improve", False)
            # pr-agent-config.toml lives with the workflow; toggle auto_improve.
            gm_target = os.path.join(staging, ".github", "workflows", "gemini-review.yml")
            os.makedirs(os.path.dirname(gm_target), exist_ok=True)
            with open(gm_target, "w", encoding="utf-8") as fh:
                fh.write(gm + "\n")
            created.append(os.path.relpath(gm_target, staging))

            if auto_improve:
                pr_agent = builder_core.fetch_with_retries(builder_core.base_url(raw, "templates/protocols/cicd/variants/pr-agent-config.toml.md"))
                pr_agent = builder_core.extract_block(pr_agent, "toml")
                pr_agent_target = os.path.join(staging, ".pr_agent.toml")
                with open(pr_agent_target, "w", encoding="utf-8") as fh:
                    fh.write(pr_agent + "\n")
                created.append(os.path.relpath(pr_agent_target, staging))

    # --- Dedicated security review (only under full CI).
    # Default provider derives from the AI reviewer (cicd protocol PHASE 3):
    # Claude when the reviewer is Claude/GGA-Claude, Gemini otherwise. Copilot or
    # none means no LLM API key -> no dedicated security review unless explicit.
    gga_provider = ci.get("gga_provider", "claude")
    if ai_reviewer == "claude" or (ai_reviewer == "gga" and gga_provider == "claude"):
        sec_default = "claude"
    elif ai_reviewer in ("gemini",) or (ai_reviewer == "gga" and gga_provider == "gemini"):
        sec_default = "gemini"
    else:
        sec_default = False
    security_review = ci.get("security_review", sec_default)
    if cicd and security_review in ("claude", "gemini"):
        sec_url = builder_core.base_url(raw, "templates/protocols/cicd/variants/security-review.%s.yml.md" % security_review)
        sec = builder_core.fetch_with_retries(sec_url)
        sec = builder_core.strip_prose_header(sec, keep_notes=True)
        sec = builder_core.resolve_gh_escapes(sec)
        if builder_core.unresolved_placeholders(sec):
            raise ValueError("unresolved placeholders in security-review.yml")
        sec_target = os.path.join(staging, ".github", "workflows", "security-review.yml")
        os.makedirs(os.path.dirname(sec_target), exist_ok=True)
        with open(sec_target, "w", encoding="utf-8") as fh:
            fh.write(sec + "\n")
        created.append(os.path.relpath(sec_target, staging))

    # --- Conventional commits (CI or release-only: commitlint + husky hook).
    if ci.get("conventional_commits", False):
        clrc_url = builder_core.base_url(raw, "templates/protocols/cicd/variants/commitlintrc.json.md")
        clrc = builder_core.fetch_with_retries(clrc_url)
        clrc = builder_core.extract_block(clrc, "json")
        clrc_target = os.path.join(staging, ".commitlintrc.json")
        with open(clrc_target, "w", encoding="utf-8") as fh:
            fh.write(clrc + "\n")
        created.append(os.path.relpath(clrc_target, staging))

        cm_url = builder_core.base_url(raw, "templates/protocols/cicd/variants/husky-commit-msg.md")
        cm = builder_core.fetch_with_retries(cm_url)
        cm = builder_core.extract_block(cm, "bash")
        cm_target = os.path.join(staging, ".husky", "commit-msg")
        os.makedirs(os.path.dirname(cm_target), exist_ok=True)
        with open(cm_target, "w", encoding="utf-8") as fh:
            fh.write(cm + "\n")
        os.chmod(cm_target, 0o755)
        created.append(os.path.relpath(cm_target, staging))

    # --- Release-please.
    if release_please:
        rel = builder_core.fetch_with_retries(builder_core.base_url(raw, "templates/protocols/cicd/variants/release-please.yml.md"))
        rel = builder_core.strip_prose_header(rel, keep_notes=True)
        rel = builder_core.resolve_gh_escapes(rel)
        if ci.get("release_ai_summary", True):
            provider = ci.get("release_ai_provider", "claude")
            if provider not in ("claude", "gemini", "openai"):
                provider = "claude"
            ai_url = builder_core.base_url(raw, "templates/protocols/cicd/variants/ai-summary-job.%s.yml.md" % provider)
            ai_sum = builder_core.fetch_with_retries(ai_url)
            ai_sum = builder_core.extract_block(ai_sum, "yaml")
            # The variant fragments carry no code fence, so extract_block falls
            # back to the raw text INCLUDING the documentation banner (field
            # report B3: the generated workflow must contain only real YAML).
            # Neither extract_block nor strip_prose_header can be used here for
            # the BODY: both end in .strip(), which left-flushes only the FIRST
            # line and destroys the fragment's internal relative indent (its
            # job key ships pre-indented two spaces). Split the banner off
            # manually so the body keeps its original indentation, normalize to
            # the fragment's own minimum common indent, then shift every
            # non-empty line to the anchor's column so the job lands as a true
            # sibling of `release-please:` regardless of template style.
            frag_lines = ai_sum.splitlines()
            _i = 0
            while _i < len(frag_lines) and (
                frag_lines[_i].startswith("#") or not frag_lines[_i].strip()
            ):
                _i += 1
            frag_lines = frag_lines[_i:]
            while frag_lines and not frag_lines[-1].strip():
                frag_lines.pop()
            margins = [
                len(line) - len(line.lstrip())
                for line in frag_lines
                if line.strip()
            ]
            base = min(margins) if margins else 0
            anchor = "  # {{AI_SUMMARY_JOB}}"
            indent = anchor[: len(anchor) - len(anchor.lstrip())]
            ai_sum = "\n".join(
                (indent + line[base:]) if line.strip() else ""
                for line in frag_lines
            )
            # Fail loudly if the anchor drifts — a silent str.replace no-op would
            # ship release-please.yml with a live placeholder inside.
            if anchor not in rel:
                raise RuntimeError(
                    "release-please.yml.md template: {{AI_SUMMARY_JOB}} anchor "
                    "missing — refusing to merge the AI summary job silently")
            rel = rel.replace(anchor, ai_sum)
        else:
            rel = re.sub(r"^\s*#\s*\{\{AI_SUMMARY_JOB\}\}\s*$", "", rel, flags=re.MULTILINE)
        rel_target = os.path.join(staging, ".github", "workflows", "release-please.yml")
        os.makedirs(os.path.dirname(rel_target), exist_ok=True)
        with open(rel_target, "w", encoding="utf-8") as fh:
            fh.write(rel + "\n")
        created.append(os.path.relpath(rel_target, staging))

        rel_cfg = builder_core.fetch_with_retries(builder_core.base_url(raw, "templates/protocols/cicd/variants/release-please-config.json.md"))
        rel_cfg = builder_core.extract_block(rel_cfg, "json")
        primary = builder_core.stack_primary(state)
        release_type = "node" if "node" in str(primary).lower() else "simple"
        rel_cfg = rel_cfg.replace("{{release_type}}", release_type)
        rel_cfg_target = os.path.join(staging, "release-please-config.json")
        with open(rel_cfg_target, "w", encoding="utf-8") as fh:
            fh.write(rel_cfg + "\n")
        created.append(os.path.relpath(rel_cfg_target, staging))

        rel_manifest = builder_core.fetch_with_retries(
            builder_core.base_url(raw, "templates/protocols/cicd/variants/release-please-manifest.json.md"))
        rel_manifest = builder_core.extract_block(rel_manifest, "json")
        # {{version}} resolves to the current package version when the project has
        # one, otherwise the release-please bootstrap version 0.1.0. It must NOT
        # come from answers.stack_versions (a human-readable "React 19.2.4, ..."
        # string, not a semver).
        manifest_version = read_package_version()
        if not manifest_version:
            manifest_version = "0.1.0"
        rel_manifest = rel_manifest.replace("{{version}}", str(manifest_version))
        rel_manifest_target = os.path.join(staging, ".release-please-manifest.json")
        with open(rel_manifest_target, "w", encoding="utf-8") as fh:
            fh.write(rel_manifest + "\n")
        created.append(os.path.relpath(rel_manifest_target, staging))

    # --- CD deploy workflow.
    if cd:
        vps = builder_core.get_state_value(state, "answers.vps_runtime", "nginx-phpfpm.laravel")
        deploy_url = builder_core.base_url(raw, "templates/protocols/cicd/variants/deploy-nginx-phpfpm.laravel.yml.md")
        try:
            dep = builder_core.fetch_with_retries(deploy_url)
        except RuntimeError:
            dep = ""
        if dep:
            dep = builder_core.strip_prose_header(dep, keep_notes=True)
            dep = builder_core.resolve_gh_escapes(dep)
            trigger_event = "tags:\n        - 'v*'" if builder_core.get_state_value(state, "cd.trigger", "tags") == "tags" else "branches:\n        - main"
            php_version = builder_core.get_state_value(state, "discovery.php_version", "8.3")
            node_version = builder_core._coalesce(state, "discovery.node_engine", "22")
            has_node_assets = "true" if builder_core.get_state_value(state, "cd.stack_detected", "") == "laravel_node" else "false"
            dep = dep.replace("{{trigger_event}}", trigger_event)
            dep = dep.replace("{{php_version}}", str(php_version))
            dep = dep.replace("{{node_version}}", str(node_version))
            dep = dep.replace("{{has_node_assets}}", has_node_assets)
            deploy_path = builder_core.get_state_value(state, "cd.deploy_path", "/var/www/html")
            dep = dep.replace("{{deploy_path}}", deploy_path)
            # {{if has_node_assets}}...{{/if}} blocks.
            def _if_repl(m):
                return m.group(1) if has_node_assets == "true" else ""
            dep = re.sub(r"\{\{if has_node_assets\}\}(.*?)\{\{/if\}\}", _if_repl, dep, flags=re.DOTALL)
            if builder_core.unresolved_placeholders(dep):
                raise ValueError("unresolved placeholders in deploy workflow")
            dep_target = os.path.join(staging, ".github", "workflows", "deploy.yml")
            os.makedirs(os.path.dirname(dep_target), exist_ok=True)
            with open(dep_target, "w", encoding="utf-8") as fh:
                fh.write(dep + "\n")
            created.append(os.path.relpath(dep_target, staging))

    return created


# ---------------------------------------------------------------------------
# B9. Registration + advance
# ---------------------------------------------------------------------------

def register_build_plan(state, staging, created_files):
    """B9: append heavy-created files to build_plan and scan staging for SHA256."""
    build = state.setdefault("build_plan", {})
    build["builder_heavy"] = {
        "generated": sorted(created_files),
    }

    def _path_of(entry):
        # Legacy refresh states may store path objects ({path, sha256, ...})
        # instead of plain path strings; normalize before set-union.
        return entry.get("path") if isinstance(entry, dict) else entry

    existing = [_path_of(e) for e in build.get("generated_files", [])]
    build["generated_files"] = sorted(set(p for p in existing if p) | set(created_files))
    existing_m = [_path_of(e) for e in build.get("managed_paths", [])]
    build["managed_paths"] = sorted(set(p for p in existing_m if p) | set(created_files))

    # SHA256 scan of the staged tree.
    shas = {}
    for root, _dirs, files in os.walk(staging):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, staging)
            shas[rel] = builder_core.sha256_text(open(full, "rb").read().decode("utf-8", errors="replace"))
    build["staged_sha256"] = shas


def advance_phase(state, wf_dir):
    """Advance the phase pointer only when in the builder pipeline (B9)."""
    pointer = builder_core.get_state_value(state, "phase", None)
    if pointer not in ("phase6", "phase6a-agents", "phase6b-build-heavy"):
        return pointer
    next_phase = {
        "phase6": "phase6a-agents",
        "phase6a-agents": "phase6b-build-heavy",
        "phase6b-build-heavy": "phase7",
    }.get(pointer, pointer)
    # WF_REFRESH=1 guard: refresher keeps its own pointer.
    if os.environ.get("WF_REFRESH") == "1":
        return pointer
    state["phase"] = next_phase
    return next_phase


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic wizard builder heavy (B7-B9)")
    parser.add_argument("--state", required=True, help="path to .wizard-state.json")
    parser.add_argument("--staging", required=True, help="staging directory to write files into")
    parser.add_argument("--raw", required=True, help="raw wizard dir (base URL or local path)")
    parser.add_argument("--wf-dir", required=True, help="WF_DIR (wizard install dir)")
    args = parser.parse_args(argv)

    state = builder_core.load_state(args.state)
    staging = args.staging
    raw = os.environ.get("WF_BUILDER_RAW", args.raw)
    wf_dir = args.wf_dir
    os.makedirs(staging, exist_ok=True)

    created = []
    created += write_commands(raw, state, staging)
    created += write_hook(raw, state, staging)
    created += write_testing_configs(raw, state, staging)
    created += write_cicd(raw, state, staging)

    register_build_plan(state, staging, created)
    next_phase = advance_phase(state, wf_dir)

    with open(args.state, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)

    print("builder-heavy: generated=%d phase=%s" % (len(created), next_phase))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - deterministic hard-fail contract
        print("builder-heavy ERROR: %s" % exc, file=sys.stderr)
        sys.exit(1)