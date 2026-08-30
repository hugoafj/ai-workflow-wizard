#!/usr/bin/env python3
"""
recompute-managed.py — Deterministic managed files recomputation.

Replaces the fragile NUL-delimited bash loop in phase8.md §8.1 and §8.3.
Reads .wizard-state.json, computes SHA256 for each managed path, and outputs
updated state JSON to stdout (or writes in-place with --in-place).

Stdlib only. No external dependencies.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Compute SHA256 of a file, reading in chunks for memory efficiency."""
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def recompute(state_path: Path) -> dict:
    """Recompute generated_files and managed_paths from state."""
    with state_path.open("r", encoding="utf-8") as f:
        state = json.load(f)

    managed_paths = state.get("build_plan", {}).get("managed_paths", [])
    generated_files = []

    for rel_path in managed_paths:
        path = Path(rel_path)
        if path.is_file():
            hash_val = sha256_file(path)
            if hash_val:
                generated_files.append({
                    "path": rel_path,
                    "hash": hash_val,
                    "managed": True
                })

    state.setdefault("build_plan", {})["generated_files"] = generated_files
    state["build_plan"]["managed_paths"] = managed_paths
    return state


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Recompute wizard managed files and hashes"
    )
    parser.add_argument(
        "--state",
        default=".wizard-state.json",
        help="Path to .wizard-state.json (default: .wizard-state.json)"
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write updated state back to the input file atomically"
    )
    parser.add_argument(
        "--output",
        help="Write updated state to a different file (used with --in-place for atomic rename)"
    )
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    if not state_path.exists():
        print(f"ERROR: state file not found: {state_path}", file=sys.stderr)
        return 1

    try:
        new_state = recompute(state_path)
    except Exception as exc:
        print(f"ERROR: recompute failed: {exc}", file=sys.stderr)
        return 1

    if args.in_place:
        # Atomic write: temp file + validate + rename
        output_path = Path(args.output) if args.output else state_path
        tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(new_state, f, indent=2, ensure_ascii=False)
            # Validate JSON is well-formed before replacing
            with tmp_path.open("r", encoding="utf-8") as f:
                json.load(f)
            tmp_path.replace(output_path)
        except Exception as exc:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            print(f"ERROR: atomic write failed: {exc}", file=sys.stderr)
            return 1
    else:
        # Default: emit to stdout for pipe-friendly usage
        json.dump(new_state, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())