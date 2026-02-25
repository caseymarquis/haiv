"""Thin git subprocess wrapper with educational output.

By default, prints commands as they run. On failure, provides a prompt
that encourages Claude to analyze and help fix the error.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from mg.errors import CommandError


@dataclass
class BranchStats:
    """Git stats for a branch relative to its base."""

    ahead: int = -1
    behind: int = -1
    changed_files: int = -1


class GitError(CommandError):
    """Raised when a git command fails.

    Attributes:
        stderr: The stderr output from the git command.
    """

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


class Git:
    """Thin wrapper around git commands.

    Args:
        path: Working directory for git commands.
        quiet: If True, suppress output and Claude prompts.
    """

    def __init__(self, path: Path, quiet: bool = False):
        self.path = Path(path)
        self.quiet = quiet

    def at_path(self, path: Path | str) -> Git:
        """Return a Git instance for a different working directory.

        Relative paths are resolved against this instance's path.
        """
        return Git(self.path / path, quiet=self.quiet)

    def at_worktree(self, branch: str) -> Git:
        """Return a Git instance for the worktree where a branch is checked out.

        Raises:
            GitError: If the branch is not checked out in any worktree.
        """
        path = self.worktree_path_for_branch(branch)
        if path is None:
            raise GitError(f"No worktree found for branch '{branch}'")
        return self.at_path(path)

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
            encoding="utf-8",
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

    def config(self, key: str) -> str | None:
        """Get a git config value, or None if not set."""
        try:
            return self.run(f"config {key}").strip() or None
        except Exception:
            return None

    def branch_stats(self, branch: str, base_branch: str) -> BranchStats:
        """Compute ahead/behind/changed_files for a branch relative to its base.

        Runs in the worktree for the given branch.

        Args:
            branch: The branch to check.
            base_branch: The branch to compare against.

        Returns:
            BranchStats with computed values.
        """
        wt = self.at_worktree(branch)

        ahead, behind = 0, 0
        if base_branch:
            output = wt.run(f"rev-list --count --left-right {base_branch}...{branch}")
            parts = output.strip().split()
            behind, ahead = int(parts[0]), int(parts[1])

        output = wt.run("status --porcelain")
        changed_files = sum(1 for line in output.splitlines() if line.strip())

        return BranchStats(ahead=ahead, behind=behind, changed_files=changed_files)

    def worktree_path_for_branch(self, branch: str) -> Path | None:
        """Find the worktree path for a given branch, or None if not checked out."""
        output = Git(self.path, quiet=True).run(
            "worktree list --porcelain", intent="list worktrees"
        )
        current_path = None
        for line in output.splitlines():
            if line.startswith("worktree "):
                current_path = Path(line[len("worktree "):])
            elif line.startswith("branch refs/heads/"):
                branch_name = line[len("branch refs/heads/"):]
                if branch_name == branch:
                    return current_path
        return None
