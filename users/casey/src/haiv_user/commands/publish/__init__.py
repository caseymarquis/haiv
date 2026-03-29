"""Publish commands for haiv packages.

Each file in this directory is a publishable package.
Shared logic lives here.

Prerequisites (one-time setup):
    1. Install the keyring CLI:
       $ uv tool install keyring

    2. Store your PyPI API token in the system keyring:
       $ echo "pypi-YOUR_TOKEN_HERE" | keyring set https://upload.pypi.org/legacy/ __token__

    3. Verify it's stored:
       $ keyring get https://upload.pypi.org/legacy/ __token__

    4. Enable the keyring provider for uv globally (optional, commands pass it explicitly):
       $ mkdir -p ~/.config/uv
       $ echo 'keyring-provider = "subprocess"' >> ~/.config/uv/uv.toml
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def publish_package(package_dir: Path, *, dry_run: bool = False, print_fn=print) -> None:
    """Build and publish a package to PyPI.

    Args:
        package_dir: Absolute path to the package directory (contains pyproject.toml)
        dry_run: If True, build only — don't publish
        print_fn: Output function (typically ctx.print)
    """
    _check_tag(package_dir, print_fn)

    # Build
    print_fn(f"Building {package_dir.name}...")
    result = subprocess.run(
        ["uv", "build"],
        cwd=package_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print_fn("Build failed.")
        print_fn(result.stderr)
        sys.exit(1)

    # Parse built file paths from uv build output
    built_files = [
        line.removeprefix("Successfully built ").strip()
        for line in result.stderr.splitlines()
        if line.startswith("Successfully built ")
    ]

    if not built_files:
        print_fn("No files built.")
        sys.exit(1)

    for f in built_files:
        print_fn(f"  {f}")

    if dry_run:
        print_fn("Dry run — skipping publish.")
        return

    # Publish — credentials come from the system keyring
    # Service: https://upload.pypi.org/legacy/
    # Username: __token__ (PyPI API token convention)
    # Password: the actual token, stored via:
    #   echo "pypi-..." | keyring set https://upload.pypi.org/legacy/ __token__
    print_fn("Publishing to PyPI...")
    result = subprocess.run([
        "uv", "publish",
        "--keyring-provider", "subprocess",
        "--username", "__token__",
        *built_files,
    ], cwd=package_dir)

    if result.returncode != 0:
        print_fn("Publish failed. Check that your keyring has the token:")
        print_fn("  keyring get https://upload.pypi.org/legacy/ __token__")
        sys.exit(1)

    print_fn("Published.")


def _check_tag(package_dir: Path, print_fn) -> None:
    """Verify HEAD has a tag. Refuse to publish untagged commits.

    Tags are how we version releases. If HEAD isn't tagged,
    we don't know what version we're publishing and shouldn't proceed.
    """
    result = subprocess.run(
        ["git", "tag", "--points-at", "HEAD"],
        cwd=package_dir,
        capture_output=True,
        text=True,
    )
    tags = result.stdout.strip()

    if not tags:
        print_fn("HEAD has no tag. Tag the release before publishing:")
        print_fn("")
        print_fn("  git tag v0.2.0")
        print_fn("  git push origin v0.2.0")
        print_fn("")
        print_fn("The tag should match the version in pyproject.toml.")
        sys.exit(1)

    print_fn(f"Tagged: {tags}")
