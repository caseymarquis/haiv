"""Integration tests for mg minds new command.

Tests the full execute() behavior including:
- Directory structure creation
- Name generation when not provided
- Name validation
- Template creation
- Output prompts
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from mg import test
from mg.errors import CommandError
from mg.test import Sandbox


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sandbox():
    """Sandbox for minds new tests."""
    return test.create_sandbox()


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
        sandbox.run("minds new --name robin")
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin").is_dir()

    def test_generates_name_when_not_provided(self, sandbox: Sandbox):
        """Generates a name when --name not provided."""
        with patch("mg.helpers.minds.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "sparrow\n"
            mock_run.return_value.returncode = 0
            sandbox.run("minds new")
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
            sandbox.run("minds new --name robin")

    def test_rejects_duplicate_in_new_folder(self, sandbox: Sandbox):
        """Rejects name that exists in _new/ folder."""
        (sandbox.ctx.paths.user.minds_dir / "_new" / "robin").mkdir(parents=True)
        with pytest.raises(CommandError, match="already exists"):
            sandbox.run("minds new --name robin")


# =============================================================================
# Directory Structure Tests
# =============================================================================


class TestDirectoryStructure:
    """Test that correct directory structure is created."""

    def test_creates_in_new_folder(self, sandbox: Sandbox):
        """Creates mind folder in _new/ subdirectory."""
        sandbox.run("minds new --name robin")
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin").is_dir()

    def test_creates_startup_directory(self, sandbox: Sandbox):
        """Creates startup/ directory."""
        sandbox.run("minds new --name robin")
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "startup").is_dir()

    def test_creates_docs_directory(self, sandbox: Sandbox):
        """Creates docs/ directory."""
        sandbox.run("minds new --name robin")
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "docs").is_dir()

    def test_creates_welcome_md(self, sandbox: Sandbox):
        """Creates startup/welcome.md template."""
        sandbox.run("minds new --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "startup" / "welcome.md"
        assert path.is_file()
        content = path.read_text()
        assert "Task Assignment" in content

    def test_creates_immediate_plan_md(self, sandbox: Sandbox):
        """Creates startup/immediate-plan.md template."""
        sandbox.run("minds new --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "startup" / "immediate-plan.md"
        assert path.is_file()

    def test_creates_long_term_vision_md(self, sandbox: Sandbox):
        """Creates startup/long-term-vision.md template."""
        sandbox.run("minds new --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "startup" / "long-term-vision.md"
        assert path.is_file()

    def test_creates_my_process_md(self, sandbox: Sandbox):
        """Creates startup/my-process.md template."""
        sandbox.run("minds new --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "startup" / "my-process.md"
        assert path.is_file()

    def test_creates_scratchpad_md(self, sandbox: Sandbox):
        """Creates startup/scratchpad.md template."""
        sandbox.run("minds new --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "startup" / "scratchpad.md"
        assert path.is_file()

    def test_creates_references_toml(self, sandbox: Sandbox):
        """Creates startup/references.toml template."""
        sandbox.run("minds new --name robin")
        path = sandbox.ctx.paths.user.minds_dir / "_new" / "robin" / "startup" / "references.toml"
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
        sandbox.run("minds new --name robin")
        output = capsys.readouterr().out
        assert "robin" in output

    def test_outputs_welcome_edit_instruction(self, sandbox: Sandbox, capsys):
        """Output instructs to edit welcome.md."""
        sandbox.run("minds new --name robin")
        output = capsys.readouterr().out
        assert "welcome.md" in output.lower()

    def test_outputs_suggest_role_command(self, sandbox: Sandbox, capsys):
        """Output includes suggest_role command."""
        sandbox.run("minds new --name robin")
        output = capsys.readouterr().out
        assert "mg minds suggest_role" in output

    def test_outputs_start_command(self, sandbox: Sandbox, capsys):
        """Output includes the start command."""
        sandbox.run("minds new --name robin")
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
        sandbox.run("minds new --name robin")
        assert sandbox.ctx.paths.user.minds_dir.exists()
        assert (sandbox.ctx.paths.user.minds_dir / "_new" / "robin").is_dir()

    def test_name_validation_lowercase(self, sandbox: Sandbox):
        """Name must be lowercase."""
        with pytest.raises(CommandError, match="lowercase"):
            sandbox.run("minds new --name Robin")

    def test_name_validation_no_underscore_start(self, sandbox: Sandbox):
        """Name cannot start with underscore."""
        with pytest.raises(CommandError, match="underscore"):
            sandbox.run("minds new --name _robin")
