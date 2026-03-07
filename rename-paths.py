#!/usr/bin/env python3
"""Rename files and directories matching a regex pattern using git mv.

Dry-run by default (shows diff). Pass --write to execute.
Renames are applied to each path's basename only, sorted longest-to-shortest
so children are always renamed before parents.
"""

import argparse
import os
import re
import subprocess
import sys

EXCLUDE = {".venv", ".git", "__pycache__"}

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"


def collect_paths(root: str) -> list[str]:
    """Collect all relative paths (dirs and files), excluding noise."""
    paths: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE]
        rel = os.path.relpath(dirpath, root)
        if rel != ".":
            paths.append(rel)
        for f in filenames:
            if f == "uv.lock":
                continue
            paths.append(f if rel == "." else os.path.join(rel, f))
    return paths


def compute_renames(paths: list[str], regex: re.Pattern, replacement: str) -> list[tuple[str, str]]:
    """Find paths whose basename matches the regex. Return (old, new) pairs."""
    renames: list[tuple[str, str]] = []
    seen: set[str] = set()

    for path in paths:
        parts = path.split(os.sep)
        basename = parts[-1]
        new_basename = regex.sub(replacement, basename)
        if new_basename != basename and path not in seen:
            seen.add(path)
            parent = os.sep.join(parts[:-1])
            new_path = os.path.join(parent, new_basename) if parent else new_basename
            renames.append((path, new_path))

    # Longest first: children before parents
    renames.sort(key=lambda x: len(x[0]), reverse=True)
    return renames


def main():
    parser = argparse.ArgumentParser(description="Rename paths matching a regex via git mv")
    parser.add_argument("pattern", help="Regex to match against each path component's basename")
    parser.add_argument("replacement", help="Replacement text")
    parser.add_argument("--write", action="store_true", help="Actually perform git mv")
    parser.add_argument("--root", default=".", help="Root directory to search (default: cwd)")
    args = parser.parse_args()

    regex = re.compile(args.pattern)
    paths = collect_paths(args.root)
    renames = compute_renames(paths, regex, args.replacement)

    if not renames:
        print("No matches found.")
        return

    for old, new in renames:
        print(f"{RED}- {old}{RESET}")
        print(f"{GREEN}+ {new}{RESET}")

    print(f"\n{len(renames)} rename(s)")

    if args.write:
        for old, new in renames:
            result = subprocess.run(
                ["git", "mv", old, new],
                cwd=args.root,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"{RED}FAILED: git mv {old} {new}{RESET}")
                print(f"  {result.stderr.strip()}")
                sys.exit(1)
        print(f"\nCompleted {len(renames)} git mv operations.")
    else:
        print("\nDry run. Use --write to apply.")


if __name__ == "__main__":
    main()
