"""Integration tests for mg minds new command.

Tests the full execute() behavior including:
- Directory structure creation
- Name generation when not provided
- Name validation
- Template creation
- Output prompts
- Worktree creation
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from mg import test
from mg.errors import CommandError
from mg.test import Sandbox
from mg.wrappers.git import Git


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sandbox():
    """Sandbox for minds new tests."""
    return test.create_sandbox()


@pytest.fixture
def git_sandbox():
    """Sandbox with git repo initialized for worktree tests."""
    sb = test.create_sandbox()
    root = sb.ctx.paths.root
    git = Git(root, quiet=True)

    # Initialize git repo with explicit main branch
    git.run("init -b main")
    git.run("config user.email test@test.com")
    git.run("config user.name Test")

    # Create initial commit (required for worktrees)
    (root / "README.md").write_text("# Test\n")
    git.run("add .")
    git.run("commit -m 'Initial commit'")

    return sb


# =============================================================================
# Command Routing Tests
# =============================================================================


class TestRouting:
    """Test command routes correctly."""

    def test_routes_to_minds_new(self):
        """mg minds new routes to correct file."""
        match = test.require_routes_to("minds new")
        assert match.file.name == "new.py"
        assert "minds" in str(match.file.parent)


# =============================================================================
# Name Handling Tests
# =============================================================================


class TestNameHandling:
    """Test name handling (provided vs generated)."""

    def test_uses_provided_name(self, sandbox: Sandbox):
        """Uses --name when provided."""
        sandbox.run("minds new --no-worktree --name robin")
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin").is_dir()

    def test_generates_name_when_not_provided(self, sandbox: Sandbox):
        """Generates a name when --name not provided."""
        with patch("mg.helpers.minds.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "sparrow\n"
            mock_run.return_value.returncode = 0
            sandbox.run("minds new --no-worktree")
        # Check that a mind folder was created in _new/
        new_dir = sandbox.ctx.paths.user.minds_dir / "_new"
        assert new_dir.exists()
        minds = [d.name for d in new_dir.iterdir() if d.is_dir()]
        assert len(minds) == 1
        assert minds[0] == "sparrow"

    def test_rejects_duplicate_name(self, sandbox: Sandbox):
        """Rejects name that already exists."""
        # Create existing mind
        (sandbox.ctx.paths.user.minds_dir / "robin").mkdir(parents=True)
        with pytest.raises(CommandError, match="already exists"):
            sandbox.run("minds new --no-worktree --name robin")

    def test_rejects_duplicate_in_new_folder(self, sandbox: Sandbox):
        """Rejects name that exists in _new/ folder."""
        (sandbox.ctx.paths.user.minds_dir / "_new" / "robin").mkdir(parents=True)
        with pytest.raises(CommandError, match="already exists"):
            sandbox.run("minds new --no-worktree --name robin")


# =============================================================================
# Directory Structure Tests
# =============================================================================


class TestDirectoryStructure:
    """Test that correct directory structure is created."""

    def test_creates_in_new_folder(self, sandbox: Sandbox):
        """Creates mind folder in _new/ subdirectory."""
        sandbox.run("minds new --no-worktree --name robin")
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin").is_dir()

    def test_creates_work_directory(self, sandbox: Sandbox):
        """Creates work/ directory."""
        sandbox.run("minds new --no-worktree --name robin")
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work").is_dir()

    def test_creates_home_directory(self, sandbox: Sandbox):
        """Creates home/ directory."""
        sandbox.run("minds new --no-worktree --name robin")
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "home").is_dir()

    def test_creates_work_docs_directory(self, sandbox: Sandbox):
        """Creates work/docs/ directory."""
        sandbox.run("minds new --no-worktree --name robin")
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work" / "docs").is_dir()

    def test_creates_welcome_md(self, sandbox: Sandbox):
        """Creates work/welcome.md template."""
        sandbox.run("minds new --no-worktree --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work" / "welcome.md"
        assert path.is_file()
        content = path.read_text()
        assert "Task Assignment" in content

    def test_creates_immediate_plan_md(self, sandbox: Sandbox):
        """Creates work/immediate-plan.md template."""
        sandbox.run("minds new --no-worktree --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work" / "immediate-plan.md"
        assert path.is_file()

    def test_creates_long_term_vision_md(self, sandbox: Sandbox):
        """Creates work/long-term-vision.md template."""
        sandbox.run("minds new --no-worktree --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work" / "long-term-vision.md"
        assert path.is_file()

    def test_creates_my_process_md(self, sandbox: Sandbox):
        """Creates work/my-process.md template."""
        sandbox.run("minds new --no-worktree --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work" / "my-process.md"
        assert path.is_file()

    def test_creates_scratchpad_md(self, sandbox: Sandbox):
        """Creates work/scratchpad.md template."""
        sandbox.run("minds new --no-worktree --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work" / "scratchpad.md"
        assert path.is_file()

    def test_creates_references_toml(self, sandbox: Sandbox):
        """Creates references.toml at root level."""
        sandbox.run("minds new --no-worktree --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "references.toml"
        assert path.is_file()
        content = path.read_text()
        assert "references" in content.lower()


# =============================================================================
# Output Tests
# =============================================================================


class TestOutput:
    """Test command output."""

    def test_outputs_mind_name(self, sandbox: Sandbox, capsys):
        """Output includes the mind name."""
        sandbox.run("minds new --no-worktree --name robin")
        output = capsys.readouterr().out
        assert "robin" in output

    def test_outputs_welcome_edit_instruction(self, sandbox: Sandbox, capsys):
        """Output instructs to edit welcome.md."""
        sandbox.run("minds new --no-worktree --name robin")
        output = capsys.readouterr().out
        assert "welcome.md" in output.lower()

    def test_outputs_suggest_role_command(self, sandbox: Sandbox, capsys):
        """Output includes suggest_role command."""
        sandbox.run("minds new --no-worktree --name robin")
        output = capsys.readouterr().out
        assert "mg minds suggest_role" in output

    def test_outputs_start_command(self, sandbox: Sandbox, capsys):
        """Output includes the start command."""
        sandbox.run("minds new --no-worktree --name robin")
        output = capsys.readouterr().out
        assert "mg start robin" in output


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_creates_minds_dir_if_not_exists(self, sandbox: Sandbox):
        """Creates minds/ directory if it doesn't exist."""
        # Ensure minds dir doesn't exist
        assert not sandbox.ctx.paths.user.minds_dir.exists()
        sandbox.run("minds new --no-worktree --name robin")
        assert sandbox.ctx.paths.user.minds_dir.exists()
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin").is_dir()

    def test_name_validation_lowercase(self, sandbox: Sandbox):
        """Name must be lowercase."""
        with pytest.raises(CommandError, match="lowercase"):
            sandbox.run("minds new --no-worktree --name Robin")

    def test_name_validation_no_underscore_start(self, sandbox: Sandbox):
        """Name cannot start with underscore."""
        with pytest.raises(CommandError, match="underscore"):
            sandbox.run("minds new --no-worktree --name _robin")


# =============================================================================
# Worktree Flag Tests
# =============================================================================


class TestWorktreeFlags:
    """Test --worktree and --no-worktree flag handling."""

    def test_requires_worktree_flag(self, sandbox: Sandbox):
        """Error when neither --worktree nor --no-worktree provided."""
        with pytest.raises(CommandError, match="Must specify --worktree or --no-worktree"):
            sandbox.run("minds new --name robin")

    def test_rejects_both_flags(self, sandbox: Sandbox):
        """Error when both --worktree and --no-worktree provided."""
        with pytest.raises(CommandError, match="Cannot use both"):
            sandbox.run("minds new --worktree --no-worktree --name robin")

    def test_no_worktree_creates_mind_only(self, sandbox: Sandbox):
        """--no-worktree creates mind without worktree."""
        sandbox.run("minds new --no-worktree --name robin")
        # Mind exists
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin").is_dir()
        # No worktree created
        assert not (sandbox.ctx.paths.root / "worktrees" / "robin").exists()

    def test_no_worktree_welcome_has_no_location(self, sandbox: Sandbox):
        """welcome.md has no location line when --no-worktree used."""
        sandbox.run("minds new --no-worktree --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work" / "welcome.md"
        content = path.read_text()
        assert "**Location:**" not in content


# =============================================================================
# Worktree Creation Tests
# =============================================================================


class TestWorktreeCreation:
    """Test worktree creation with --worktree flag."""

    def test_worktree_creates_mind_and_worktree(self, git_sandbox: Sandbox):
        """--worktree creates both mind and worktree."""
        git_sandbox.run("minds new --worktree --name robin")
        # Mind exists
        assert (git_sandbox.ctx.paths.user.minds_dir / "_new" / "robin").is_dir()
        # Worktree exists
        assert (git_sandbox.ctx.paths.root / "worktrees" / "robin").is_dir()

    def test_worktree_uses_mind_name_by_default(self, git_sandbox: Sandbox):
        """Worktree name defaults to mind name."""
        git_sandbox.run("minds new --worktree --name robin")
        assert (git_sandbox.ctx.paths.root / "worktrees" / "robin").is_dir()

    def test_worktree_custom_name(self, git_sandbox: Sandbox):
        """--worktree with value uses custom worktree name."""
        git_sandbox.run("minds new --worktree feature-x --name robin")
        # Mind still named robin
        assert (git_sandbox.ctx.paths.user.minds_dir / "_new" / "robin").is_dir()
        # Worktree named feature-x
        assert (git_sandbox.ctx.paths.root / "worktrees" / "feature-x").is_dir()

    def test_worktree_welcome_has_location(self, git_sandbox: Sandbox):
        """welcome.md has location populated when --worktree used."""
        git_sandbox.run("minds new --worktree --name robin")
        path = git_sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work" / "welcome.md"
        content = path.read_text()
        assert "**Location:** `worktrees/robin/`" in content

    def test_worktree_custom_name_in_welcome(self, git_sandbox: Sandbox):
        """welcome.md has custom worktree name when provided."""
        git_sandbox.run("minds new --worktree feature-x --name robin")
        path = git_sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "work" / "welcome.md"
        content = path.read_text()
        assert "**Location:** `worktrees/feature-x/`" in content

    def test_rejects_existing_nonempty_worktree_dir(self, sandbox: Sandbox):
        """Error when worktree directory exists and is not empty."""
        # Create non-empty directory (no git needed for this test)
        worktree_dir = sandbox.ctx.paths.root / "worktrees" / "robin"
        worktree_dir.mkdir(parents=True)
        (worktree_dir / "some-file.txt").write_text("content")

        with pytest.raises(CommandError, match="already exists and is not empty"):
            sandbox.run("minds new --worktree --name robin")

    def test_outputs_worktree_location(self, git_sandbox: Sandbox, capsys):
        """Output includes worktree location."""
        git_sandbox.run("minds new --worktree --name robin")
        output = capsys.readouterr().out
        assert "worktrees/robin/" in output
