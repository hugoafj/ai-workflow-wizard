#!/usr/bin/env python3
"""
builder-core.py — Deterministic wizard builder: B1-B6 + core build_plan registration.

Replaces the builder-core sub-agent with a deterministic inline pipeline so that
wf-refresh runs B1-B6 exactly the same way every time.

Usage:
  python3 builder-core.py --state <path> --staging <path> --raw <WF_RAW> --wf-dir <WF_DIR>

Exit codes:
  0  success
  1  unrecoverable error (missing state, unresolved placeholder, failed download)

Stdlib only. No sub-agent delegation.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# IPv4-first DNS resolution: prefer AF_INET so urllib does not hang on
# IPv6-first resolution (many dev machines have no IPv6 route); IPv6 remains
# available as a fallback for IPv6-only networks.
# ---------------------------------------------------------------------------
_orig_getaddrinfo = socket.getaddrinfo

def _ipv4_first_getaddrinfo(*args, **kwargs):
    results = _orig_getaddrinfo(*args, **kwargs)
    return sorted(results, key=lambda r: (r[0] != socket.AF_INET))

socket.getaddrinfo = _ipv4_first_getaddrinfo

# ---------------------------------------------------------------------------
# Command description heuristics (universal + stack overrides)
# ---------------------------------------------------------------------------

# Stack-specific overrides — extensible without touching core logic
STACK_OVERRIDES = {
    "node": {
        "dev": "Start development server",
        "build": "Build for production",
        "lint": "Run linter (ESLint, etc.)",
        "preview": "Preview production build locally",
        "format": "Format code (Prettier, etc.)",
        "typecheck": "Run type checker (tsc, etc.)",
    },
    "python": {
        "test": "Run pytest",
        "lint": "Run ruff/flake8",
        "format": "Run black/isort",
        "typecheck": "Run mypy/pyright",
        "migrate": "Run database migrations",
    },
    "go": {
        "test": "Run go test",
        "build": "Run go build",
        "lint": "Run golangci-lint",
        "vet": "Run go vet",
        "fmt": "Run go fmt",
    },
    "rust": {
        "test": "Run cargo test",
        "build": "Run cargo build",
        "check": "Run cargo check",
        "clippy": "Run cargo clippy",
        "fmt": "Run cargo fmt",
    },
    "java": {
        "test": "Run maven/gradle test",
        "build": "Run maven/gradle build",
        "lint": "Run checkstyle/spotbugs",
    },
}

def _heuristic_description(script_name: str) -> str:
    """Generate description from script name using universal naming patterns."""
    name = script_name.lower()
    
    # Prefix-based universal patterns
    if name.startswith("test"):
        if "e2e" in name: return "Run end-to-end tests"
        if "ui" in name: return "Run tests with UI"
        if "coverage" in name: return "Run tests with coverage report"
        if "watch" in name: return "Run tests in watch mode"
        if "integration" in name: return "Run integration tests"
        return "Run tests"
    if name.startswith("lint"): return "Run linter"
    if name.startswith("build"): return "Build for production"
    if name.startswith("dev"): return "Start development server"
    if name.startswith("preview"): return "Preview production build locally"
    if name.startswith("format"): return "Format code"
    if name.startswith("typecheck") or name.startswith("type-check"): return "Run type checker"
    if name.startswith("db:") or name.startswith("db-"): return "Database operations"
    if name.startswith("docker"): return "Docker operations"
    if name.startswith("deploy"): return "Deploy application"
    if name.startswith("release"): return "Release workflow"
    if name.startswith("generate"): return "Code generation"
    if name.startswith("migrate"): return "Run migrations"
    if name.startswith("seed"): return "Seed database"
    if name.startswith("clean"): return "Clean build artifacts"
    if name.startswith("install"): return "Install dependencies"
    if name.startswith("update"): return "Update dependencies"
    if name.startswith("check"): return "Run checks"
    if name.startswith("fmt") or name.startswith("format"): return "Format code"
    if name.startswith("vet"): return "Run static analysis"
    if name.startswith("clippy"): return "Run linter (clippy)"
    if name.startswith("bench"): return "Run benchmarks"
    if name.startswith("doc"): return "Generate documentation"
    
    # Exact common names
    if name in ("dev", "start", "serve"): return "Start development server"
    if name in ("build", "compile"): return "Build for production"
    if name in ("test", "tests"): return "Run tests"
    if name in ("lint", "check"): return "Run linter"
    if name in ("fmt", "format"): return "Format code"
    if name in ("clean", "distclean"): return "Clean build artifacts"
    if name in ("install", "ci"): return "Install dependencies"
    
    # Fallback
    return f"Run {script_name} script"

def describe_command(script_name: str, stack_key: str = "") -> str:
    """Get description for a command: stack override > heuristic > generic."""
    stack = (stack_key or "").lower()
    # Match stack prefix (e.g., "node-react" -> "node")
    for prefix, overrides in STACK_OVERRIDES.items():
        if stack.startswith(prefix) and script_name in overrides:
            return overrides[script_name]
    return _heuristic_description(script_name)

def detect_project_structure(project_root: str) -> str:
    """Generate tree from actual filesystem (respecting common ignore patterns)."""
    import os
    
    ignore_dirs = {".git", "node_modules", ".next", "dist", "build", ".turbo", 
                   "coverage", ".vercel", ".netlify", "__pycache__", ".pytest_cache",
                   "venv", ".venv", "env", ".env", "target", "vendor", ".idea", ".vscode"}
    ignore_files = {".DS_Store", "Thumbs.db"}
    
    lines = []
    try:
        for root, dirs, files in os.walk(project_root):
            # Filter ignored dirs in-place
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            
            rel_root = os.path.relpath(root, project_root)
            if rel_root == ".":
                continue
                
            depth = rel_root.count(os.sep)
            indent = "  " * depth
            folder_name = os.path.basename(root) + "/"
            lines.append(f"{indent}{folder_name}")
            
            # List key config/entry files
            key_files = sorted(f for f in files 
                             if f not in ignore_files and 
                             (f.endswith((".json", ".ts", ".js", ".py", ".rs", ".go", ".java", ".toml", ".yaml", ".yml")) 
                              or f in ("package.json", "tsconfig.json", "vite.config.ts", "next.config.js",
                                       "main.py", "app.py", "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
                                       "requirements.txt", "pyproject.toml", "composer.json", "Makefile")))
            for f in key_files:
                lines.append(f"{indent}  {f}")
    except Exception:
        pass
    
    return "\n".join(lines) if lines else "flat"

# ---------------------------------------------------------------------------
# B1. State loading
# ---------------------------------------------------------------------------

def load_state(path):
    """Load the wizard state JSON. Hard-fail when absent or malformed."""
    with open(path, "r", encoding="utf-8") as fh:
        state = json.load(fh)
    if not isinstance(state, dict):
        raise ValueError("state root must be a JSON object")
    return state


def get_state_value(state, dot_path, default=None):
    """Resolve a dot-path against the state dict (e.g. 'discovery.stack_key')."""
    node = state
    for part in dot_path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def _coalesce(state, dot_path, default):
    """
    Coalesce a state value: returns `default` when the value is missing, null, empty string,
    or the string "None". This ensures that quality-guard and deploy workflows never
    render empty/"None" values even before R2 normalization runs.
    """
    val = get_state_value(state, dot_path, None)
    if val is None or val == "" or val == "None":
        return default
    return val


def stack_key(state):
    """Resolve the stack key with the nested fallback (Bug 2, PR #88)."""
    return get_state_value(state, "discovery.stack.stack_key") or \
           get_state_value(state, "discovery.stack_key") or ""


def stack_primary(state):
    """Primary stack from discovery.stack.primary, falling back to stack_key.

    States migrated by R2 get discovery.stack.stack_key normalized but never
    gain a .primary field; without this fallback those npm projects resolved
    release-type "simple" instead of "node" in builder-heavy's
    release-please-config rendering.
    """
    primary = get_state_value(state, "discovery.stack.primary")
    if isinstance(primary, list) and primary:
        return primary[0]
    if isinstance(primary, str) and primary:
        return primary
    return stack_key(state)


def bool_feature(state, name):
    """Resolve a features.<name> boolean safely (None -> False)."""
    return bool(get_state_value(state, "features.%s" % name, False))


# ---------------------------------------------------------------------------
# Remote file helpers
# ---------------------------------------------------------------------------

def fetch_text(url):
    """Fetch a UTF-8 text file. Hard-fail on HTTP errors or network failure."""
    if url.startswith("file://"):
        path = url[len("file://"):]
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read()
        except OSError as exc:
            raise RuntimeError("failed to fetch %s: %s" % (url, exc)) from exc
    req = urllib.request.Request(url, headers={"User-Agent": "wf-builder/0.8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except Exception as exc:  # HTTPError, URLError, timeout, decode errors
        raise RuntimeError("failed to fetch %s: %s" % (url, exc)) from exc


def fetch_with_retries(url, attempts=3):
    """Fetch with bounded retries; the last failure propagates as RuntimeError."""
    last = None
    for i in range(attempts):
        try:
            print(">>> fetching %s" % url, file=sys.stderr)
            return fetch_text(url)
        except RuntimeError as exc:
            last = exc
            print("    attempt %d/%d failed: %s" % (i + 1, attempts, exc), file=sys.stderr)
    if last is None:
        raise RuntimeError("failed to fetch %s (no attempts made)" % url)
    raise last


# ---------------------------------------------------------------------------
# Template extraction helpers
# ---------------------------------------------------------------------------

def strip_internal_comment(text):
    """Remove the leading internal HTML comment block from a template body."""
    # Remove a leading `<!-- ... -->` block together with surrounding blank lines.
    return re.sub(r"^\s*<!--.*?-->\s*", "", text, count=1, flags=re.DOTALL).strip()


def extract_block(text, lang="markdown"):
    """Extract the content of the first fenced code block; if none, return raw text."""
    m = re.search(r"```" + re.escape(lang) + r"\s*\n(.*?)\n```", text, flags=re.DOTALL)
    if m:
        return m.group(1)
    return text.strip()


def strip_prose_header(text, keep_notes=False):
    """Remove leading `#` prose header lines from a variant file (CI/CD files).

    With keep_notes=True, preserve the `# Notes:` documentation block (YAML
    comments are valid in the generated workflow) while still dropping the
    title, placeholder-resolution and conditional-resolution lines above it.
    Only safe for YAML workflow targets; TS/JSON fragments keep the default
    False because `#` is not a valid comment there.
    """
    lines = text.splitlines()
    if keep_notes:
        for i, line in enumerate(lines):
            if line.lstrip().startswith("# Notes:"):
                return "\n".join(lines[i:]).strip()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#") or not line.strip():
            i += 1
            continue
        break
    return "\n".join(lines[i:]).strip()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def unresolved_placeholders(text):
    """Return leftover `{{...}}` that are NOT legitimate `${{ ... }}` expressions."""
    return re.findall(r"(?<!\$)\{\{[^}]*\}\}", text)


# ---------------------------------------------------------------------------
# B3. Protocol body construction
# ---------------------------------------------------------------------------

# SPLIT protocols live under templates/commands/; pure protocols under templates/protocols/.
SPLIT_PROTOCOLS = {"wf-ladder", "wf-tdd", "wf-orchestrator", "wf-sdd-trigger"}
# Maintenance commands also live under templates/commands/ and ship skills.
MAINTENANCE_COMMANDS = ["wf-onboard", "wf-worktree", "wf-settings"]
# Everything resolved from templates/commands/ (SPLIT + maintenance).
COMMAND_PROTOCOLS = SPLIT_PROTOCOLS | set(MAINTENANCE_COMMANDS)
PURE_PROTOCOLS = {
    "architecture", "cicd", "commands", "ides", "sdd", "testing", "workflow",
}


def base_url(raw, rel):
    """Join a wizard base dir (http/https/file path) with a relative template path."""
    if raw.startswith(("http://", "https://", "file://")):
        return "%s/%s" % (raw.rstrip("/"), rel.lstrip("/"))
    return "%s/%s" % (raw.rstrip("/"), rel.lstrip("/"))


def protocol_base_url(raw, name):
    """Return the URL of the base template for a protocol name."""
    if name in COMMAND_PROTOCOLS:
        return base_url(raw, "templates/commands/%s/_base.md" % name)
    if name in PURE_PROTOCOLS:
        return base_url(raw, "templates/protocols/%s/_base.md" % name)
    raise ValueError("unknown protocol: %s" % name)


def build_protocol_body(raw, name, state):
    """Build the assembled protocol body for a protocol name (B3)."""
    proto_url = protocol_base_url(raw, name)
    body = fetch_with_retries(proto_url)
    body = strip_internal_comment(body)

    if name == "wf-ladder":
        # protocol-header.md + body from the first '## ' heading onward.
        header_url = base_url(raw, "templates/commands/wf-ladder/protocol-header.md")
        try:
            header = strip_internal_comment(fetch_with_retries(header_url))
        except RuntimeError:
            header = ""
        m = re.search(r"^## ", body, flags=re.MULTILINE)
        rest = body[m.start():] if m else body
        return (header + "\n\n" + rest).strip()

    if name == "wf-tdd":
        tdd_mode = get_state_value(state, "answers.tdd_mode") or \
                   get_state_value(state, "testing.tdd_mode") or "standard"
        variant_url = base_url(raw, "templates/commands/wf-tdd/variants/%s.md" % (tdd_mode))
        try:
            variant = fetch_with_retries(variant_url)
        except RuntimeError:
            variant = ""
        # Replace the TDD_MODE_VARIANT marker (HTML comment form) with the variant body.
        body = re.sub(
            r"<!--\s*\{\{TDD_MODE_VARIANT[^}]*\}\}.*?-->",
            lambda m: variant.strip(),
            body,
            flags=re.DOTALL,
        )
        # Resolve semantic <if ...>: blocks against layers.
        body = resolve_if_blocks(body, state, raw)
        return body.strip()

    return body


# ---------------------------------------------------------------------------
# Semantic <if ...>: block resolution (wf-tdd, quality-guard)
# ---------------------------------------------------------------------------

def resolve_if_blocks(text, state, raw=None):
    """Resolve `<if CONDITION>:` blocks (marker line + block) from semantic text.

    The marker form is `<if CONDITION>:` on its own line. The block ends at the
    next marker line, a non-empty line less indented than the first content
    line, or (for YAML step lists) the next `- ` item at the same indent as the
    first content line — whichever comes first. The YAML step-list boundary
    keeps steps that follow a conditional block (e.g. Build after a conditional
    Sanitization step) OUT of the conditional block.
    """
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^\s*<if (.+)>:\s*\n$", line)
        if m:
            cond = m.group(1).strip()
            block_start = i + 1
            # First non-empty content line establishes the block's base indent.
            first_idx = None
            for k in range(block_start, len(lines)):
                if lines[k].strip():
                    first_idx = k
                    break
            first_indent = len(lines[first_idx]) - len(lines[first_idx].lstrip()) if first_idx is not None else 0
            first_is_yaml_list = first_idx is not None and \
                lines[first_idx].lstrip().startswith("- ") and \
                first_indent == (len(line) - len(line.lstrip()))
            j = block_start
            while j < len(lines):
                nxt = lines[j]
                if re.match(r"^\s*<if .+>:\s*\n$", nxt):
                    break
                if nxt.strip() and first_idx is not None and j > first_idx:
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt_indent < first_indent:
                        break
                    # YAML step lists: the next `- ` item at the same indent is a
                    # new step, NOT part of the conditional block.
                    if first_is_yaml_list and nxt_indent == first_indent and nxt.lstrip().startswith("- "):
                        break
                j += 1
            block = "".join(lines[block_start:j])
            if eval_semantic_cond(cond, state, raw):
                out.append(block)
            i = j
            continue
        out.append(line)
        i += 1
    return "".join(out)


def eval_semantic_cond(cond, state, raw=None):
    """Evaluate a semantic condition string used in <if> markers.

    Supports both `state.a.b` paths and known semantic phrases.
    """
    cond = cond.strip()
    # state.path conditions -> boolean path lookup.
    if cond.startswith("state."):
        return bool(get_state_value(state, cond[len("state."):], False))

    # Known semantic phrases used in templates.
    layers = normalize_layers(state)
    c = cond.lower()

    # MUST stay ABOVE the generic "e2e layer" phrases: this condition string
    # contains "e2e layer active" as a substring, and the layers-only rules
    # below would otherwise swallow it. Mirrors the documented intent
    # (archived subagent-builder-heavy.md): include E2E CI steps only when the
    # layer is active AND ci.e2e_in_ci is not false. Missing key defaults to
    # True ("!= false"); states written by migrate_state always set it.
    if "e2e layer active in ci" in c or "e2e in ci" in c:
        return ("e2e" in layers) and bool(get_state_value(state, "ci.e2e_in_ci", True))
    if "at least one layer" in c or "any layer" in c:
        return bool(layers)
    if "e2e layer active" in c or "e2e layer is active" in c or "e2e layer" in c:
        return "e2e" in layers
    if "unit or integration layer is active" in c or "unit or integration" in c:
        return ("unit" in layers) or ("integration" in layers)
    if "type-check script or tsconfig.json exists" in c:
        if raw:
            # `raw` points at the wizard repo; the project root is not available
            # from a deterministic script, so fall back to layers/state evidence.
            pass
        return bool(get_state_value(state, "discovery.has_typescript", True))
    if "test:sanitization script exists" in c:
        return bool(get_state_value(state, "testing.has_sanitization", False))

    # Fallback: boolean literal phrases.
    if c in ("true", "yes", "1"):
        return True
    if c in ("false", "no", "0"):
        return False
    raise ValueError("unrecognized semantic condition: %s" % cond)


# ---------------------------------------------------------------------------
# B5. AGENTS.md router rendering (full boolean evaluator)
# ---------------------------------------------------------------------------

def truthy(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.lower() not in ("", "false", "no", "0", "null", "none")
    if isinstance(value, (list, dict, tuple)):
        return len(value) > 0
    return bool(value)


def eval_boolean(expr, state):
    """Evaluate a boolean expression over state paths.

    Supports `or`, `and`, `not`, `!= null`, `not empty`, and parenthesized
    sub-expressions.  Every `state.a.b` token resolves through truthy().
    """
    # Normalize tokens into a Python-safe expression.
    safe = expr

    # Replace `X != null` / `X == null` with raw-value null checks.
    def _ne_null_repl(m):
        return "__GV_RAW('%s') is not None" % m.group(1)

    def _eq_null_repl(m):
        return "__GV_RAW('%s') is None" % m.group(1)

    safe = re.sub(r"state\.([A-Za-z0-9_.]+)\s*!=\s*null\b", _ne_null_repl, safe)
    safe = re.sub(r"state\.([A-Za-z0-9_.]+)\s*==\s*null\b", _eq_null_repl, safe)

    # Replace `X not empty` phrase with a callable emptiness check.
    def _not_empty_repl(m):
        return "__NE__('%s')" % m.group(1)

    safe = re.sub(r"state\.([A-Za-z0-9_.]+)\s+not empty\b", _not_empty_repl, safe)

    # Replace state paths with a lookup call.
    def _path_repl(m):
        path = m.group(1)
        return "__GV('%s')" % path

    safe = re.sub(r"state\.([A-Za-z0-9_.]+)", _path_repl, safe)

    # Replace operators.
    safe = safe.replace("__NE_NULL__", "is not None")
    safe = safe.replace("__EQ_NULL__", "is None")

    # Guard: allow only whitelisted tokens.
    allowed = re.compile(r"^[A-Za-z0-9_\.'\(\)\s\|\&!<>=+\-\*/]+$")
    if not allowed.match(safe):
        raise ValueError("unsafe boolean expression: %s" % expr)

    namespace = {
        "__GV": lambda p: truthy(get_state_value(state, p)),
        "__GV_RAW": lambda p: get_state_value(state, p, None),
        "__NE__": lambda p: bool(get_state_value(state, p, None)),
        "None": None,
        "True": True,
        "False": False,
    }
    try:
        return bool(eval(safe, {"__builtins__": {}}, namespace))
    except Exception as exc:
        raise ValueError("failed to evaluate condition %r: %s" % (expr, exc)) from exc


def normalize_layers(state):
    """Normalize testing.layers into a list of active layer names.

    Accepts the current array shape, the legacy dict shape
    ({"unit": true, "integration": false, ...}), or a comma string.
    """
    layers = get_state_value(state, "testing.layers", None)
    if layers is None:
        return []
    if isinstance(layers, dict):
        return [k for k, v in layers.items() if v]
    if isinstance(layers, str):
        return [x.strip() for x in layers.split(",") if x.strip()]
    if isinstance(layers, list):
        return [x for x in layers if isinstance(x, str)]
    return []


def detect_package_scripts():
    """Detect npm scripts from package.json in the project root (cwd).

    Returns a comma-joined command list, or None when the project has no
    package.json / no scripts. Used to re-discover `discovery.commands`
    during refresh instead of guessing from the stack key.
    """
    try:
        with open(os.path.join(os.getcwd(), "package.json"), "r", encoding="utf-8") as fh:
            pkg = json.load(fh)
        scripts = pkg.get("scripts", {})
    except (OSError, ValueError):
        return None
    if not isinstance(scripts, dict) or not scripts:
        return None
    # List ALL scripts (F4): the old build-only / names[:6] behavior silently
    # flattened the Commands section and dropped dev, test:ui, etc.
    names = sorted(scripts.keys())
    return ", ".join("npm run %s" % n for n in names)


def _warn_fallback(key, value):
    print("WARNING: %s is empty in state — using fallback %r. Re-run /wf-init phase1 discovery or set state.%s." % (key, value, key), file=sys.stderr)


def infer_placeholder(state, key):
    """Resolve placeholders that have no state field, deterministically.

    These five are documented as inference-resolved from state + manifest in
    openspec/changes/fix-judgment-day-v070/tasks.md.
    """
    layers = normalize_layers(state)

    if key == "discovery.commands":
        # Commands discovered in phase1; re-detect from package.json on refresh.
        # Priority: state (agent-enriched) > detected scripts with heuristic > fallback
        commands = get_state_value(state, "discovery.commands", None)
        stack = stack_key(state)
        if commands is not None:
            if isinstance(commands, str):
                return commands
            lines = []
            for c in commands:
                # Extract script name (after "npm run " or just the command)
                script_name = c.replace("- npm run ", "").replace("npm run ", "").strip()
                desc = describe_command(script_name, stack)
                lines.append("- %s — %s" % (c, desc))
            return "\n".join(lines)
        detected = detect_package_scripts()
        if detected:
            # Convert comma-separated to bulleted format with heuristic descriptions
            bulleted_lines = []
            for c in detected.split(","):
                c = c.strip()
                script_name = c.replace("npm run ", "").strip()
                desc = describe_command(script_name, stack)
                bulleted_lines.append("- %s — %s" % (c, desc))
            bulleted = "\n".join(bulleted_lines)
            _warn_fallback(key, bulleted)
            return bulleted
        _warn_fallback(key, "- npm run build — Build for production")
        return "- npm run build — Build for production"

    if key == "discovery.conventions.code_style":
        # FU3b: Compose code_style from structured conventions fields.
        # When any of naming, components, imports, tests, css, state are present,
        # emit bullets: "- Naming: <value>", "- Components: <value>", etc.
        # Fall back to preserving AGENTS.md section verbatim (from R1 backfill)
        # when ALL structured fields are absent, then to naming, then camelCase.
        conventions = get_state_value(state, "discovery.conventions", {}) or {}
        fields = [
            ("Naming", "naming"),
            ("Components", "components"),
            ("Imports", "imports"),
            ("Tests", "tests"),
            ("CSS", "css"),
            ("State", "state"),
        ]
        bullets = []
        for label, field_key in fields:
            val = conventions.get(field_key)
            if val:
                bullets.append("- %s: %s" % (label, val))
        if bullets:
            return "\n".join(bullets)
        # Fallback 1: pre-existing rich code_style from R1 backfill (preserves AGENTS.md section)
        existing = get_state_value(state, "discovery.conventions.code_style", None)
        if existing and isinstance(existing, str) and existing not in ("camelCase", "flat", ""):
            return existing
        # Fallback 2: naming convention
        naming = conventions.get("naming")
        if naming:
            return naming
        _warn_fallback(key, "camelCase")
        return "camelCase"

    if key == "discovery.conventions.structure":
        # Priority: state (agent-enriched with # purpose) > filesystem scan
        structure = get_state_value(state, "discovery.conventions.structure", None)
        if structure and isinstance(structure, str) and "\n" in structure:
            # Already enriched by agent (has newlines = tree format with comments)
            return structure
        # Fallback: scan actual filesystem
        project_root = os.getcwd()
        return detect_project_structure(project_root)

    if key == "testing.checks_before_done":
        # Gate on the active test layers, not features.testing (which the state
        # schema does not define). lint + build are always part of the done gate;
        # test / test:e2e follow the unit/integration/e2e layers.
        checks = ["lint", "build"]
        if "unit" in layers or "integration" in layers:
            checks.append("test")
        if "e2e" in layers:
            checks.append("test:e2e")
        # Bulleted list (one command per line) instead of a comma join: the
        # comma form was unreadable and lost the run-these-before-done framing.
        return "\n".join("- `npm run %s`" % c for c in checks)

    if key == "mcps.table":
        mcps = get_state_value(state, "mcps", []) or []
        if not isinstance(mcps, list):
            mcps = [mcps]
        if not mcps:
            _warn_fallback(key, "None configured")
            return "None configured"
        
        # Deduplicate MCPs by lowercased name (case-insensitive merge).
        # Keep the entry with purpose/setup if present; otherwise first occurrence.
        seen = {}
        for mcp in mcps:
            if isinstance(mcp, dict):
                name = mcp.get("name", "?")
                lname = name.lower()
                if lname not in seen or (not seen[lname].get("purpose") and mcp.get("purpose")):
                    seen[lname] = mcp
            else:
                lname = str(mcp).lower()
                if lname not in seen:
                    seen[lname] = mcp
        deduped = list(seen.values())
        
        # Check if any MCP has purpose (3-col table)
        has_purpose = any(isinstance(m, dict) and m.get("purpose") for m in deduped)
        
        if has_purpose:
            # 3-column table: | MCP | Purpose | Required setup |
            rows = []
            for mcp in deduped:
                if isinstance(mcp, dict):
                    name = mcp.get("name", "?")
                    purpose = mcp.get("purpose", "")
                    setup = mcp.get("setup", "")
                    rows.append("| %s | %s | %s |" % (name, purpose, setup))
                else:
                    rows.append("| %s | | |" % str(mcp))
            return "\n".join(["| MCP | Purpose | Required setup |", "|---|---|---|"] + rows)
        else:
            # 2-column fallback: | MCP | Active |
            rows = []
            for mcp in deduped:
                if isinstance(mcp, dict):
                    name = mcp.get("name", "?")
                    active = mcp.get("active", True)
                    rows.append("| %s | %s |" % (name, "yes" if active else "no"))
                else:
                    rows.append("| %s | yes |" % str(mcp))
            return "\n".join(["| MCP | Active |", "|---|---|"] + rows)

    return None


def resolve_placeholder(state, key):
    """Resolve a single {{key}} placeholder, including _yesno suffix and inference."""
    if key == "PLACEHOLDERS":
        # Documental keyword in the router header, not a state placeholder.
        return "placeholders"
    if key.endswith("_yesno"):
        base = key[: -len("_yesno")]
        return "yes" if truthy(get_state_value(state, base)) else "no"
    if key in ("discovery.stack_key", "discovery.stack.stack_key"):
        # Defensive alias: resolve through the nested-first helper so BOTH the
        # legacy flat and the nested schema forms follow the canonical key
        # (Bug 2, PR #88). Legacy states may carry only one of the two shapes.
        return stack_key(state)
    value = get_state_value(state, key, None)
    if value is not None:
        if key == "discovery.commands" and isinstance(value, list):
            # Apply descriptions for commands from state (same as infer_placeholder)
            stack = stack_key(state)
            lines = []
            for v in value:
                script_name = v.replace("- npm run ", "").replace("npm run ", "").strip()
                desc = describe_command(script_name, stack)
                lines.append("- %s — %s" % (v, desc))
            return "\n".join(lines)
        if isinstance(value, list):
            # Markdown bullets (UTF-8): list-typed placeholders such as
            # answers.critical_constraints must render as readable rule
            # lists. The previous json.dumps() wrote escaped JSON arrays
            # ("aprobaci\u00f3n") straight into AGENTS.md (field report B12).
            # Fix: unescape JSON strings (e.g., \u0027 -> ')
            import codecs
            def unescape_json(s):
                # Only decode when actual \u escapes are present.
                # Applying unicode_escape to valid UTF-8 corrupts non-ASCII chars
                # (e.g. "aprobación" -> "aprobaciÃ³n") because it interprets
                # UTF-8 bytes as escape sequences.
                if '\\u' in s:
                    try:
                        return codecs.decode(s, 'unicode_escape')
                    except Exception:
                        pass
                return s
            return "\n".join("- " + unescape_json(str(v)) for v in value)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    inferred = infer_placeholder(state, key)
    if inferred is not None:
        return inferred
    raise ValueError("unresolved placeholder: %s" % key)


def resolve_gh_escapes(text, resolve=None):
    """Resolve `${{ '{{' }}X{{ '}}' }}` GH-Actions escape patterns.

    The inner X may be:
      - a literal `secrets.<NAME>` reference      -> wrapped as `${{ secrets.<NAME> }}`
      - a wizard placeholder `{{key}}`            -> resolved, then kept literal
      - a bare placeholder name (`provider_cli`)  -> resolved through `resolve`

    `resolve` is an optional callable mapping a placeholder name to its value;
    unknown names should raise KeyError.
    """
    def _repl(m):
        inner = m.group(1).strip()
        resolver = resolve
        if resolver is not None:
            # Resolve nested {{key}} placeholders inside the inner text.
            def _nested(mm):
                return str(resolver(mm.group(1)))

            inner = re.sub(r"\{\{([A-Za-z0-9_.]+)\}\}", _nested, inner)
        if inner.startswith("secrets."):
            return "${{ %s }}" % inner
        # Bare placeholder name (template pattern like `provider_cli`).
        if resolver is not None and re.match(r"^[A-Za-z0-9_.]+$", inner):
            try:
                return str(resolver(inner))
            except KeyError:
                pass
        return inner

    return re.sub(r"\$\{\{\s*'\{\{'\s*\}\}(.*?)\{\{\s*'\}\}'\s*\}\}", _repl, text, flags=re.DOTALL)


def resolve_router_ifs(text, state):
    """Resolve nested `<if COND>...</if>` blocks with a stack parser.

    Supports arbitrary nesting (e.g. routing wrapping tdd, inline table cells).
    """
    stack = []  # list of [condition, buffer]
    out = []
    i = 0
    n = len(text)
    while i < n:
        m_open = re.match(r"<if\s+(.+?)>", text[i:])
        m_close = re.match(r"</if>", text[i:])
        if m_open is None:
            if m_close is None:
                ch = text[i]
                if stack:
                    stack[-1][1].append(ch)
                else:
                    out.append(ch)
                i += 1
                continue
            # Only a closing tag here.
            if not stack:
                raise ValueError("unbalanced </if> in router")
            cond, buf = stack.pop()
            body = "".join(buf)
            kept = body if eval_boolean(cond, state) else ""
            if stack:
                stack[-1][1].append(kept)
            else:
                out.append(kept)
            i += m_close.end()
            if i < n and text[i] == "\n":
                i += 1
            continue
        # m_open is not None.
        cond_text = m_open.group(1)
        if m_close is not None and m_close.end() < m_open.end():
            # Closing tag appears before the opener ends; treat as close.
            if not stack:
                raise ValueError("unbalanced </if> in router")
            cond, buf = stack.pop()
            body = "".join(buf)
            kept = body if eval_boolean(cond, state) else ""
            if stack:
                stack[-1][1].append(kept)
            else:
                out.append(kept)
            i += m_close.end()
            if i < n and text[i] == "\n":
                i += 1
            continue
        if "state." in cond_text:
            stack.append([cond_text.strip(), []])
            i += m_open.end()
            if i < n and text[i] == "\n":
                i += 1
            continue
        # Not a real conditional (documentation mention like `<if ...>`);
        # emit it literally.
        if stack:
            stack[-1][1].append(text[i:i + m_open.end()])
        else:
            out.append(text[i:i + m_open.end()])
        i += m_open.end()
    if stack:
        raise ValueError("unbalanced <if> in router")
    return "".join(out)


def testing_approach_section(state, raw=None):
    """Generate the Testing Approach section body from the active test layers.

    Replaces inlining the raw `testing-approach.section.md` instruction
    fragment: the resolved section is derived from `testing.layers`, so the
    shipped AGENTS.md always shows the tests that actually exist. The router
    already provides the `## Testing Approach` heading, so this returns the
    body only (no duplicate heading).

    Rich deterministic content modeled on the canonical fragment: per-layer
    blocks carry the file-placement and naming conventions (unit tests next to
    the code under test, integration in a dedicated folder, e2e specs named by
    user flow), not just the run commands. Runner brand names are deliberately
    omitted — they belong to the Commands section, which the discovery merge
    keeps accurate.
    """
    layers = normalize_layers(state)
    has_unit = "unit" in layers or "integration" in layers
    has_e2e = "e2e" in layers
    lines = []
    if has_unit:
        lines += [
            "### Unit & Integration",
            "",
            "Run the unit/integration suite before considering a change done:",
            "",
            "```bash",
            "npm run test",
            "```",
            "",
            "- Unit: one test file next to the code it covers (`Component.test.tsx` next to the component).",
            "- Integration: real render tests in `src/__tests__/integration/` (`*.integration.test.tsx`).",
        ]
    if has_e2e:
        lines += [
            "",
            "### E2E",
            "",
            "Run the end-to-end suite (specs by flow) before merge:",
            "",
            "```bash",
            "npm run test:e2e",
            "```",
            "",
            "- One spec file per user flow, named by the flow — not by the component or hook.",
            "- Specs live in `e2e/<feature-name>.spec.ts` (examples: `persistence.spec.ts`, `task-creation.spec.ts`).",
        ]
        if get_state_value(state, "testing.page_object_model", False):
            lines += [
                "- Page objects live in `e2e/pages/` — one class per screen; specs never hold raw selectors.",
            ]
        # Field report B4: phase 4.6b documents the data-testid convention for
        # e2e projects, but nothing injected it into the generated AGENTS.md
        # and data-testid.section.md sat orphaned. Single source stays the
        # template file; append it verbatim when e2e is active.
        if raw:
            try:
                dt = fetch_with_retries(
                    base_url(raw, "templates/protocols/testing/data-testid.section.md"))
                dt = strip_internal_comment(dt)
                dt = re.sub(r"^\s*<if[^>]*>:\s*\n?", "", dt)
                if dt.strip():
                    lines += ["", dt.strip()]
            except RuntimeError:
                pass
    if not has_unit and not has_e2e:
        lines += [
            "No automated test layers are active. Follow `testing.checks_before_done` "
            "for the manual done-gate instead.",
        ]
    return "\n".join(lines).strip()


def _collapse_blank_lines_outside_fences(text):
    """Collapse 3+ consecutive newlines to one blank line, skipping fenced
    code blocks so their intentional blank lines are preserved."""
    in_fence = False
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not in_fence and stripped.startswith("```"):
            in_fence = True
            out.append(line)
            i += 1
            continue
        if in_fence:
            out.append(line)
            if stripped.startswith("```"):
                in_fence = False
            i += 1
            continue
        # Outside a fence: collapse runs of blank lines to a single blank line.
        if stripped == "":
            out.append(line)
            i += 1
            while i < n and lines[i].strip() == "":
                i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def render_router(raw, state):
    """Render templates/AGENTS.router.md with full placeholder and <if> resolution."""
    router = fetch_with_retries(base_url(raw, "templates/AGENTS.router.md"))

    # Step 1: resolve nested <if CONDITION> ... </if> blocks.
    router = resolve_router_ifs(router, state)

    # Step 2: resolve {{protocols/...}} includes.
    def _proto_repl(m):
        spec = m.group(1).strip()
        # testing-approach.section.md is an instruction fragment, not a
        # template body: generate the resolved section from the active layers.
        if spec == "testing/testing-approach.section.md":
            return testing_approach_section(state, raw)
        # spec may be "templates/commands/wf-ladder/_base.md (protocol-header)"
        # or "testing/testing-approach.section.md" (fragment file). The regex
        # stripped the leading "protocols/" from the include name, so re-add it
        # for relative fragment paths.
        if spec.startswith(("commands/", "protocols/")):
            rel = "templates/%s" % spec.lstrip("/")
        elif "/" in spec:
            rel = "templates/protocols/%s" % spec.lstrip("/")
        else:
            rel = None
        if rel:
            try:
                return fetch_with_retries(base_url(raw, rel))
            except RuntimeError:
                pass
        name_m = re.match(r"templates/(?:commands|protocols)/([^/]+?)/", spec)
        if name_m:
            name = name_m.group(1)
            return build_protocol_body(raw, name, state)
        raise ValueError("cannot parse protocol include: %s" % spec)

    router = re.sub(r"\{\{protocols/([^}]+)\}\}", _proto_repl, router)

    # Step 3: resolve remaining {{key}} placeholders.
    def _ph_repl(m):
        return resolve_placeholder(state, m.group(1).strip())

    router = re.sub(r"\{\{([A-Za-z0-9_.]+)\}\}", _ph_repl, router)

    # Step 4: collapse GH Action escape wrappers (placeholder text resolved first,
    # so inner `secrets.X` references are already literal).
    def _router_resolver(key):
        try:
            return resolve_placeholder(state, key)
        except ValueError:
            raise KeyError(key)

    router = resolve_gh_escapes(router, _router_resolver)

    # Step 5: strip builder-instruction HTML comments from the shipped file,
    # preserving the WF: DO NOT REGENERATE markers (read by /wf-refresh) and
    # the wf-version footer line (read by /wf-settings and /wf-refresh).
    def _keep_comment(m):
        c = m.group(0)
        if "DO NOT REGENERATE" in c or c.startswith("<!-- wf-version:"):
            return c
        return ""

    router = re.sub(r"<!--.*?-->", _keep_comment, router, flags=re.DOTALL)

    # Step 6: collapse 3+ consecutive newlines to one blank line (the <if>/</if>
    # resolver can leave gaps that break markdown tables) and drop trailing
    # whitespace left by stripped instruction comments (two spaces after a
    # placeholder would render as a hard break in CommonMark). The collapse only
    # applies OUTSIDE fenced code blocks, so intentional multi-blank-line
    # content inside ``` fences is preserved.
    router = _collapse_blank_lines_outside_fences(router)
    router = re.sub(r"[ \t]+$", "", router, flags=re.MULTILINE)

    # Step 7: hard-fail on any leftover {{ or }} placeholder residue.
    if re.search(r"\{\{|\}\}", router):
        left = re.findall(r"\{\{[^}]*\}\}", router)[:5]
        raise ValueError("unresolved placeholders remain in AGENTS.md: %s" % left)

    return router


# ---------------------------------------------------------------------------
# B4. Flat protocols + skills
# ---------------------------------------------------------------------------

IDE_PATHS = {
    "claude-code": ".claude/protocols/",
    "opencode": ".opencode/protocols/",
    "cursor": ".cursor/protocols/",
    "codex": ".codex/protocols/",
    "windsurf": ".windsurf/protocols/",
    "gemini-cli": ".gemini/protocols/",
    "kiro": ".kiro/protocols/",
    "vscode-copilot": ".github/protocols/",
    "antigravity": ".agents/protocols/",
}

SKILL_PATHS = {
    "claude-code": ".claude/skills/",
    "opencode": ".opencode/skills/",
    "cursor": ".cursor/skills/",
    "codex": ".codex/skills/",
    "windsurf": ".windsurf/skills/",
    # builder.md B4 table: gemini-cli native skills path. Commands keep the
    # universal .agents/skills fallback (Gemini custom commands are TOML, a
    # different format the Builder does not emit).
    "gemini-cli": ".gemini/skills/",
    "kiro": ".kiro/skills/",
    "vscode-copilot": ".github/skills/",
    "antigravity": ".agents/skills/",
}

DEVIN_SKILLS = ".devin/skills/"


def active_ides(state):
    """Return the list of active IDE keys from answers.ides."""
    ides = get_state_value(state, "answers.ides", []) or []
    if not isinstance(ides, list):
        ides = [ides]
    return [ide for ide in ides if ide in IDE_PATHS]


def active_protocols(state):
    """Return the ordered list of active protocol names."""
    out = []
    # Pure protocols are always active.
    for name in ["architecture", "cicd", "commands", "ides", "testing", "workflow"]:
        out.append(name)
    # sdd is active when a backend was selected.
    backend = get_state_value(state, "sdd.backend", None)
    if backend:
        out.append("sdd")
    # wf protocols follow features.
    ladder = bool_feature(state, "decision_ladder")
    tdd = bool_feature(state, "tdd_protocol")
    routing = bool_feature(state, "routing_abc")
    if ladder:
        out.append("wf-ladder")
    if tdd and (get_state_value(state, "testing.layers", None) or bool_feature(state, "testing")):
        out.append("wf-tdd")
    if routing or ladder or tdd:
        out.append("wf-orchestrator")
    if routing:
        out.append("wf-sdd-trigger")
    return out


def parse_skill_frontmatter(skill_text):
    """Extract name from the SKILL.md frontmatter; default to None."""
    m = re.match(r"^---\s*\n(.*?)\n---", skill_text, flags=re.DOTALL)
    if not m:
        return None
    fm = m.group(1)
    name_m = re.search(r"^name:\s*(.+)$", fm, flags=re.MULTILINE)
    return name_m.group(1).strip() if name_m else None


def write_skills(raw, state, staging):
    """Write skills for every active wizard command that ships a SKILL.md (B4)."""
    commands = [c for c in SPLIT_PROTOCOLS] + MAINTENANCE_COMMANDS
    # Filter SPLIT commands by active protocols; maintenance always ship.
    active = set(active_protocols(state))
    skills_created = []

    for cmd in commands:
        if cmd in SPLIT_PROTOCOLS and cmd not in active:
            continue
        skill_url = base_url(raw, "templates/commands/%s/skill/SKILL.md" % (cmd))
        try:
            skill_text = fetch_with_retries(skill_url)
        except RuntimeError:
            continue  # presence-driven: no SKILL.md -> no skill
        name = parse_skill_frontmatter(skill_text)
        if not name:
            continue
        body = build_protocol_body(raw, cmd, state)
        # Replace {{PROTOCOL_BODY: ...}} marker.
        rendered = re.sub(
            r"\{\{PROTOCOL_BODY:[^}]*\}\}",
            lambda m: body,
            skill_text,
            flags=re.DOTALL,
        )
        rendered = strip_internal_comment(rendered)
        # NOTE: remaining `{{...}}` in the body are RUNTIME literals of the
        # command itself (e.g. `{{sdd.backend}}` used as a sed pattern by
        # wf-settings), not builder placeholders. They must stay verbatim.

        # Universal skill dir (always) + per-IDE dirs.
        targets = [os.path.join(staging, ".agents", "skills", name)]
        for ide in active_ides(state):
            targets.append(os.path.join(staging, SKILL_PATHS[ide], name))
        if "windsurf" in active_ides(state):
            targets.append(os.path.join(staging, DEVIN_SKILLS, name))
        for tgt in dict.fromkeys(targets):
            os.makedirs(tgt, exist_ok=True)
            with open(os.path.join(tgt, "SKILL.md"), "w", encoding="utf-8") as fh:
                # strip_internal_comment() .strip()s the rendered text, so the
                # trailing newline of the source SKILL.md is gone by this
                # point; every other writer appends one explicitly.
                fh.write(rendered.rstrip() + "\n")
            skills_created.append(os.path.relpath(os.path.join(tgt, "SKILL.md"), staging))
    return skills_created


def write_flat_protocols(raw, state, staging):
    """Write flat .agents/protocols/<name>.md files for active protocols (B4)."""
    flat_dir = os.path.join(staging, ".agents", "protocols")
    os.makedirs(flat_dir, exist_ok=True)
    created = []
    for name in active_protocols(state):
        body = build_protocol_body(raw, name, state)
        rel = os.path.join(".agents", "protocols", "%s.md" % name)
        with open(os.path.join(staging, rel), "w", encoding="utf-8") as fh:
            fh.write(body + "\n")
        created.append(rel)
    return created


def write_satellites(raw, state, staging):
    """Write per-IDE satellite files (B6).

    Destinations follow the spec in `wf-init/lib/builder.md` (Step B6 satellite
    table), restored after the 17c5d95 regression introduced `wizard.md`
    destinations and dropped devin.

    Missing templates are a HARD failure collected across all IDEs (field
    report B2): the deterministic contract says the builder never silently
    skips an artifact — opencode.tmpl 404 used to exit 0 with the satellite
    missing.
    """
    created = []
    failures = []
    sat_map = {
        "claude-code": ("claude.tmpl", "CLAUDE.md"),
        "opencode": ("opencode.tmpl", ".opencode/AGENTS.md"),
        "cursor": ("cursor.tmpl", ".cursor/rules/project.mdc"),
        "codex": ("codex.tmpl", ".codex/AGENTS.md"),
        "windsurf": ("windsurf.tmpl", ".windsurf/rules/project.md"),
        "gemini-cli": ("gemini.tmpl", "GEMINI.md"),
        "kiro": ("kiro.tmpl", ".kiro/steering/project-context.md"),
        "vscode-copilot": ("copilot.tmpl", ".github/copilot-instructions.md"),
        "antigravity": ("antigravity.tmpl", "ANTIGRAVITY.md"),
    }
    ides = active_ides(state)
    for ide in ides:
        if ide not in sat_map:
            continue
        tmpl_name, rel = sat_map[ide]
        url = base_url(raw, "templates/satellites/%s" % (tmpl_name))
        try:
            text = fetch_with_retries(url)
        except RuntimeError as exc:
            failures.append("%s: %s" % (ide, exc))
            continue
        rendered = render_satellite(text, state)
        target = os.path.join(staging, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(rendered + "\n")
        created.append(rel)
    # Devin follows the windsurf satellite (spec: .devin/rules/project.md)
    # whenever windsurf is active; it has no IDE_PATHS entry of its own.
    if "windsurf" in ides:
        url = base_url(raw, "templates/satellites/windsurf.tmpl")
        text = None
        try:
            text = fetch_with_retries(url)
        except RuntimeError as exc:
            failures.append("devin: %s" % exc)
        if text:
            rendered = render_satellite(text, state)
            target = os.path.join(staging, ".devin/rules/project.md")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(rendered + "\n")
            created.append(os.path.relpath(target, staging))
    if failures:
        raise RuntimeError("missing satellite templates: %s" % "; ".join(failures))
    return created


def render_satellite(text, state):
    """Resolve placeholders inside a satellite template; fail on leftovers."""
    def _repl(m):
        return resolve_placeholder(state, m.group(1).strip())

    rendered = re.sub(r"\{\{([A-Za-z0-9_.]+)\}\}", _repl, text)
    if re.search(r"\{\{|\}\}", rendered):
        raise ValueError("unresolved placeholders in satellite")
    return rendered.strip()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def record_build_plan(state, staging, core_created, skills_created, wf_dir, phase_now):
    """B6.5: record core build_plan facts into the staged state."""
    build = state.setdefault("build_plan", {})
    build["builder_core"] = {
        "scripts": [
            os.path.relpath(os.path.join(wf_dir, "lib", "builder-core.py")),
            os.path.relpath(os.path.join(wf_dir, "lib", "builder-heavy.py")),
        ],
        "core_generated": sorted(core_created),
        "core_skills": sorted(skills_created),
    }

    def _path_of(entry):
        # Legacy refresh states may store path objects ({path, sha256, ...})
        # instead of plain path strings; normalize before set-union.
        return entry.get("path") if isinstance(entry, dict) else entry

    existing = [_path_of(e) for e in build.get("generated_files", [])]
    build["generated_files"] = sorted(set(p for p in existing if p) | set(core_created) | set(skills_created))
    existing_m = [_path_of(e) for e in build.get("managed_paths", [])]
    build["managed_paths"] = sorted(set(p for p in existing_m if p) | set(core_created) | set(skills_created))
    build["phase_now"] = phase_now
    build["stack_key"] = stack_key(state)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic wizard builder core (B1-B6)")
    parser.add_argument("--state", required=True, help="path to .wizard-state.json")
    parser.add_argument("--staging", required=True, help="staging directory to write files into")
    parser.add_argument("--raw", required=True, help="raw wizard dir (base URL or local path)")
    parser.add_argument("--wf-dir", required=True, help="WF_DIR (wizard install dir)")
    parser.add_argument("--phase-now", default="phase6", help="current phase label for build_plan")
    args = parser.parse_args(argv)

    state = load_state(args.state)
    staging = args.staging
    raw = os.environ.get("WF_BUILDER_RAW", args.raw)
    wf_dir = args.wf_dir
    os.makedirs(staging, exist_ok=True)

    # B2: keys.
    sk = stack_key(state)
    sp = stack_primary(state)

    # B3+B4: flat protocols and skills.
    flat_created = write_flat_protocols(raw, state, staging)
    skills_created = write_skills(raw, state, staging)

    # B5: AGENTS.md (router).
    router_text = render_router(raw, state)
    agents_rel = os.path.join("AGENTS.md")
    with open(os.path.join(staging, agents_rel), "w", encoding="utf-8") as fh:
        fh.write(router_text + "\n")
    core_created = flat_created + [agents_rel]

    # B6: satellites.
    satellites = write_satellites(raw, state, staging)
    core_created += satellites

    # B6.5: record.
    record_build_plan(state, staging, core_created, skills_created, wf_dir, args.phase_now)

    # Persist the updated state back into staging.
    with open(args.state, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)

    print("builder-core: stack_key=%s primary=%s flat=%d skills=%d satellites=%d" % (
        sk, sp, len(flat_created), len(skills_created), len(satellites)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - deterministic hard-fail contract
        print("builder-core ERROR: %s" % exc, file=sys.stderr)
        sys.exit(1)