"""Tests for hv init command.

Modes:
1. Fresh mode (not in a git repo)
   - Empty directory → create haiv structure
   - Non-empty directory → require --force, move files to worktree

2. Peer mode (in a git repo)
   - Create peer `project-hv/` alongside existing checkout
   - Requires remote configured
   - Requires clean working tree (unless --force)

Implementation requirement: All sandboxes MUST be created inside a wrapper
directory. This enables testing peer mode (peer dir appears in parent) and
ensures single-cleanup semantics.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from haiv import test
from haiv.errors import CommandError
from haiv.wrappers.git import Git
from haiv.test import SandboxConfig, Sandbox


# =============================================================================
# Test Types
# =============================================================================

@dataclass
class InitResult:
    """Convenience wrapper for hv init test results."""
    sandbox: Sandbox

    def init(self, args=""):
        """Run hv init with optional args. Returns self for chaining."""
        cmd = f"init {args}".strip()
        self.sandbox.run(cmd)
        return self

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def ctx(self):
        return self.sandbox.ctx

    @property
    def paths(self):
        return self.sandbox.ctx.paths

    @property
    def git(self):
        return self.sandbox.ctx.git

    @property
    def main_worktree(self):
        return self.paths.worktrees_dir / "main"

    @property
    def develop_worktree(self):
        return self.paths.worktrees_dir / "develop"

    @property
    def peer_dir(self):
        return self.paths.root.parent / f"{self.paths.root.name}-hv"


# =============================================================================
# Fixtures (starting states)
# =============================================================================

@pytest.fixture
def empty_sandbox():
    """Empty directory - for fresh mode tests."""
    sandbox = test.create_sandbox(SandboxConfig(explicit=True))
    return InitResult(sandbox=sandbox)


@pytest.fixture
def nonempty_sandbox():
    """Non-empty directory - for fresh mode --force tests."""
    sandbox = test.create_sandbox(SandboxConfig(explicit=True))
    result = InitResult(sandbox=sandbox)
    (result.paths.root / "README.md").write_text("# My Project\n")
    (result.paths.root / "src").mkdir()
    (result.paths.root / "src" / "main.py").write_text("print('hello')\n")
    return result


@pytest.fixture
def fresh_init(empty_sandbox):
    """Empty sandbox with default hv init already run."""
    return empty_sandbox.init()


@pytest.fixture
def in_repo():
    """Inside a git repo with remote - for peer mode tests."""
    # Create bare repo to act as "remote"
    remote = test.create_sandbox(SandboxConfig(explicit=True))
    Git(remote.ctx.paths.root, quiet=True).run("init --bare")

    # Create working repo pointing to local "remote"
    sandbox = test.create_sandbox(SandboxConfig(explicit=True))
    result = InitResult(sandbox=sandbox)
    git = Git(result.paths.root, quiet=True)
    git.run("init")
    git.run("branch -m main")  # Ensure branch is named "main"
    git.run(f"remote add origin {remote.ctx.paths.root}")
    (result.paths.root / "README.md").write_text("# Test\n")
    git.run("add .")
    git.run("commit -m 'Initial commit'")
    git.run("push -u origin main")
    return result


@pytest.fixture
def in_repo_no_remote():
    """Inside a git repo without remote - for testing remote requirement."""
    sandbox = test.create_sandbox(SandboxConfig(explicit=True))
    result = InitResult(sandbox=sandbox)
    git = Git(result.paths.root, quiet=True)
    git.run("init")
    git.run("branch -m main")  # Ensure branch is named "main"
    (result.paths.root / "README.md").write_text("# Test\n")
    git.run("add .")
    git.run("commit -m 'Initial commit'")
    return result


# =============================================================================
# Fresh Mode: Empty Directory
# =============================================================================

class TestInitFreshEmpty:
    """Fresh mode in an empty directory."""

    def test_creates_git_directory(self, fresh_init):
        assert fresh_init.paths.git_dir.is_dir()

    def test_creates_worktrees_directory(self, fresh_init):
        assert fresh_init.paths.worktrees_dir.is_dir()

    def test_creates_claude_md(self, fresh_init):
        assert (fresh_init.paths.root / "CLAUDE.md").exists()

    def test_creates_pyproject_toml(self, fresh_init):
        assert (fresh_init.paths.root / "pyproject.toml").exists()

    def test_creates_claude_dir(self, fresh_init):
        assert (fresh_init.paths.root / ".claude").is_dir()

    def test_creates_hv_project_package(self, fresh_init):
        hv_project = fresh_init.paths.root / "src" / "hv_project"
        assert hv_project.is_dir()
        assert (hv_project / "__init__.py").exists()

    def test_creates_tests_dir(self, fresh_init):
        assert (fresh_init.paths.root / "tests").is_dir()

    def test_creates_users_dir(self, fresh_init):
        assert (fresh_init.paths.root / "users").is_dir()

    def test_creates_hv_state_orphan_branch(self, fresh_init):
        assert fresh_init.git.branch_current() == "haiv"

    def test_creates_main_worktree_by_default(self, fresh_init):
        assert fresh_init.main_worktree.is_dir()

    def test_main_worktree_has_readme(self, fresh_init):
        assert (fresh_init.main_worktree / "README.md").exists()

    def test_main_worktree_has_initial_commit(self, fresh_init):
        git = Git(fresh_init.main_worktree)
        assert git.commit_count() >= 1

    def test_branch_flag_overrides_default(self, empty_sandbox):
        empty_sandbox.init("--branch develop")

        assert empty_sandbox.develop_worktree.is_dir()
        assert not empty_sandbox.main_worktree.exists()

    def test_empty_flag_skips_readme_but_commits(self, empty_sandbox):
        """--empty creates worktree with empty initial commit, no README."""
        empty_sandbox.init("--empty")

        # Worktree is created
        assert empty_sandbox.main_worktree.is_dir()
        # No README
        assert not (empty_sandbox.main_worktree / "README.md").exists()
        # But has an initial commit
        worktree_git = Git(empty_sandbox.main_worktree)
        assert worktree_git.commit_count() >= 1

    def test_prints_git_commands(self, empty_sandbox, capsys):
        empty_sandbox.init()

        out = capsys.readouterr().out
        assert "git init" in out
        assert "git checkout --orphan" in out or "orphan" in out.lower()

    def test_prints_next_steps(self, empty_sandbox, capsys):
        empty_sandbox.init()

        out = capsys.readouterr().out
        assert "worktree" in out.lower()


# =============================================================================
# Fresh Mode: Non-Empty Directory
# =============================================================================

class TestInitFreshNonEmpty:
    """Fresh mode in a non-empty directory."""

    def test_fails_without_force(self, nonempty_sandbox):
        with pytest.raises(CommandError):
            nonempty_sandbox.init()

    def test_error_message_suggests_force(self, nonempty_sandbox):
        with pytest.raises(CommandError) as exc_info:
            nonempty_sandbox.init()

        assert "--force" in str(exc_info.value)

    def test_force_creates_structure(self, nonempty_sandbox):
        nonempty_sandbox.init("--force")

        assert nonempty_sandbox.paths.git_dir.is_dir()
        assert nonempty_sandbox.paths.worktrees_dir.is_dir()

    def test_force_moves_files_to_worktree(self, nonempty_sandbox):
        nonempty_sandbox.init("--force")

        assert (nonempty_sandbox.main_worktree / "README.md").exists()
        assert not (nonempty_sandbox.paths.root / "README.md").exists()

    def test_force_with_branch_moves_to_named_worktree(self, nonempty_sandbox):
        nonempty_sandbox.init("--force --branch develop")

        assert nonempty_sandbox.develop_worktree.is_dir()
        assert not nonempty_sandbox.main_worktree.exists()

    def test_moved_files_are_committed(self, nonempty_sandbox):
        nonempty_sandbox.init("--force")

        git = Git(nonempty_sandbox.main_worktree)
        assert git.commit_count() >= 1

    def test_nested_directories_preserved(self, nonempty_sandbox):
        nonempty_sandbox.init("--force")

        assert (nonempty_sandbox.main_worktree / "src" / "main.py").exists()


# =============================================================================
# Peer Mode: Basic
# =============================================================================

class TestInitPeerBasic:
    """Peer mode creates hv repo alongside existing checkout.

    Note: Sandboxes are nested inside a wrapper directory, so the peer
    directory created in parent is automatically cleaned up.
    """

    def test_creates_peer_directory(self, in_repo):
        in_repo.init()

        assert in_repo.peer_dir.is_dir()

    def test_peer_named_with_hv_suffix(self, in_repo):
        in_repo.init()

        assert in_repo.peer_dir.name.endswith("-hv")

    def test_peer_has_git_directory(self, in_repo):
        in_repo.init()

        assert (in_repo.peer_dir / ".git").is_dir()

    def test_peer_has_worktrees_directory(self, in_repo):
        in_repo.init()

        assert (in_repo.peer_dir / "worktrees").is_dir()

    def test_peer_has_hv_state_orphan_branch(self, in_repo):
        in_repo.init()

        git = Git(in_repo.peer_dir)
        assert git.branch_current() == "haiv"

    def test_creates_worktree_for_current_branch(self, in_repo):
        in_repo.init()

        # Default branch is main, so worktree should be created for it
        assert (in_repo.peer_dir / "worktrees" / "main").is_dir()

    def test_branch_flag_overrides_current_branch(self, in_repo):
        # Create develop branch on remote first
        git = Git(in_repo.paths.root, quiet=True)
        git.run("checkout -b develop")
        git.run("push -u origin develop")
        git.run("checkout main")

        in_repo.init("--branch develop")

        assert (in_repo.peer_dir / "worktrees" / "develop").is_dir()
        assert not (in_repo.peer_dir / "worktrees" / "main").exists()

    def test_original_repo_unchanged(self, in_repo):
        original_files = set(in_repo.paths.root.iterdir())

        in_repo.init()

        assert set(in_repo.paths.root.iterdir()) == original_files


# =============================================================================
# Peer Mode: Prerequisites
# =============================================================================

class TestInitPeerPrerequisites:
    """Peer mode requires remote and clean state."""

    def test_fails_without_remote(self, in_repo_no_remote):
        with pytest.raises(CommandError):
            in_repo_no_remote.init()

    def test_no_remote_error_has_guidance(self, in_repo_no_remote):
        with pytest.raises(CommandError) as exc_info:
            in_repo_no_remote.init()

        assert "remote" in str(exc_info.value).lower()

    def test_fails_with_staged_changes(self, in_repo):
        (in_repo.paths.root / "new.txt").write_text("staged")
        Git(in_repo.paths.root, quiet=True).run("add new.txt")

        with pytest.raises(CommandError):
            in_repo.init()

    def test_fails_with_unstaged_changes(self, in_repo):
        (in_repo.paths.root / "README.md").write_text("modified")

        with pytest.raises(CommandError):
            in_repo.init()

    def test_fails_with_untracked_files(self, in_repo):
        (in_repo.paths.root / "untracked.txt").write_text("untracked")

        with pytest.raises(CommandError):
            in_repo.init()

    def test_dirty_error_suggests_force(self, in_repo):
        (in_repo.paths.root / "untracked.txt").write_text("untracked")

        with pytest.raises(CommandError) as exc_info:
            in_repo.init()

        assert "--force" in str(exc_info.value)

    def test_force_bypasses_dirty_check(self, in_repo):
        (in_repo.paths.root / "untracked.txt").write_text("untracked")

        in_repo.init("--force")

        assert in_repo.peer_dir.is_dir()

    def test_force_warns_about_uncommitted(self, in_repo, capsys):
        (in_repo.paths.root / "untracked.txt").write_text("untracked")

        in_repo.init("--force")

        out = capsys.readouterr().out
        assert "uncommitted" in out.lower() or "untracked" in out.lower()

    def test_ignored_files_dont_cause_error(self, in_repo):
        git = Git(in_repo.paths.root, quiet=True)
        (in_repo.paths.root / ".gitignore").write_text("*.log\n")
        git.run("add .gitignore")
        git.run("commit -m 'Add gitignore'")
        git.run("push")
        (in_repo.paths.root / "debug.log").write_text("ignored content")

        in_repo.init()

        assert in_repo.peer_dir.is_dir()

    def test_fails_when_branch_ahead_of_remote(self, in_repo):
        # Create a local commit that isn't pushed
        git = Git(in_repo.paths.root, quiet=True)
        (in_repo.paths.root / "local.txt").write_text("local only")
        git.run("add local.txt")
        git.run("commit -m 'Local commit'")

        with pytest.raises(CommandError) as exc_info:
            in_repo.init()

        assert "ahead" in str(exc_info.value).lower() or "push" in str(exc_info.value).lower()

    def test_force_bypasses_branch_ahead_check(self, in_repo):
        # Create a local commit that isn't pushed
        git = Git(in_repo.paths.root, quiet=True)
        (in_repo.paths.root / "local.txt").write_text("local only")
        git.run("add local.txt")
        git.run("commit -m 'Local commit'")

        in_repo.init("--force")

        assert in_repo.peer_dir.is_dir()


# =============================================================================
# Peer Mode: Edge Cases
# =============================================================================

class TestInitPeerEdgeCases:
    """Peer mode edge cases."""

    def test_nonexistent_branch_fails(self, in_repo):
        with pytest.raises(CommandError) as exc_info:
            in_repo.init("--branch nonexistent")

        assert "nonexistent" in str(exc_info.value).lower()
        # Peer dir should not be created
        assert not in_repo.peer_dir.exists()

    def test_works_from_subdirectory(self, in_repo):
        subdir = in_repo.paths.root / "src"
        subdir.mkdir()
        in_repo.sandbox.cd(subdir)

        in_repo.init()

        assert in_repo.peer_dir.is_dir()

    def test_peer_directory_already_exists_fails(self, in_repo):
        in_repo.peer_dir.mkdir(parents=True)

        with pytest.raises(CommandError):
            in_repo.init()

    def test_existing_peer_error_message(self, in_repo):
        in_repo.peer_dir.mkdir(parents=True)

        with pytest.raises(CommandError) as exc_info:
            in_repo.init()

        assert "already exists" in str(exc_info.value).lower()


# =============================================================================
# Educational Output
# =============================================================================

class TestInitEducationalOutput:
    """Verify 'educate, don't obscure' principle."""

    def test_shows_git_init_command(self, empty_sandbox, capsys):
        empty_sandbox.init()

        out = capsys.readouterr().out
        assert "git init" in out

    def test_shows_git_worktree_command(self, empty_sandbox, capsys):
        empty_sandbox.init()

        out = capsys.readouterr().out
        assert "git worktree" in out

    def test_explains_orphan_branch_purpose(self, empty_sandbox, capsys):
        empty_sandbox.init()

        out = capsys.readouterr().out
        assert "orphan" in out.lower()

    def test_quiet_flag_suppresses_output(self, empty_sandbox, capsys):
        empty_sandbox.init("--quiet")

        out = capsys.readouterr().out
        assert out == ""
