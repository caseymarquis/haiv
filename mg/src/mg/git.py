"""Thin git subprocess wrapper with educational output.

By default, prints commands as they run. On failure, provides a prompt
that encourages Claude to analyze and help fix the error.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from mg.errors import GitError


class Git:
    """Thin wrapper around git commands.

    Args:
        path: Working directory for git commands.
        quiet: If True, suppress output and Claude prompts.
    """

    def __init__(self, path: Path, quiet: bool = False):
        self.path = Path(path)
        self.quiet = quiet

    def run(self, cmd: str, *, intent: str | None = None) -> str:
        """Run a git command.

        Args:
            cmd: Git command without 'git' prefix (e.g., "init --bare").
            intent: Optional description of what we're trying to accomplish.

        Returns:
            stdout from the command.

        Raises:
            GitError: If the command fails.
        """
        full_cmd = f"git {cmd}"

        if not self.quiet:
            print(f"→ {full_cmd}")

        result = subprocess.run(
            full_cmd,
            shell=True,
            cwd=self.path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            if not self.quiet:
                # Print raw git error
                if result.stderr.strip():
                    print(result.stderr.rstrip())

                # Optional intent line
                if intent:
                    print(f"\nWhile trying to: {intent}")

                # Claude prompt
                print(
                    "\nAnalyze the above error, explain what happened, "
                    "and suggest a fix."
                )

            raise GitError(
                f"git command failed: {full_cmd}",
                stderr=result.stderr,
            )

        return result.stdout

    def branch_current(self, *, intent: str | None = "get current branch name") -> str:
        """Get the current branch name."""
        return self.run("rev-parse --abbrev-ref HEAD", intent=intent).strip()

    def commit_count(self, *, intent: str | None = "count commits on current branch") -> int:
        """Get the number of commits on the current branch."""
        output = self.run("rev-list --count HEAD", intent=intent).strip()
        return int(output)
