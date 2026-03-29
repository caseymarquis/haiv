"""Integration tests for venv relay.

These tests create real project directories with venvs to prove
that venv detection works end-to-end. They are SLOW and must be
run explicitly:

    uv run pytest tests/integration/test_venv_relay.py -v

They are excluded from the normal test suite via conftest marker.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from haiv._infrastructure.venv_resolver import (
    PyprojectVenvResolver,
    VenvMatch,
    _find_project_root,
    _is_current_venv,
)

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def fake_project(tmp_path: Path) -> Path:
    """Create a minimal project with its own venv."""
    project = tmp_path / "fake-project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "fake-project"\nversion = "0.1.0"\n'
        'requires-python = ">=3.12"\n'
    )
    # Create a real venv via uv
    subprocess.run(
        ["uv", "venv", str(project / ".venv")],
        check=True,
        capture_output=True,
    )
    return project


@pytest.fixture
def command_file(fake_project: Path) -> Path:
    """Create a command file inside the fake project."""
    commands = fake_project / "src" / "commands"
    commands.mkdir(parents=True)
    cmd_file = commands / "hello.py"
    cmd_file.write_text("# a command\n")
    return cmd_file


class TestFindProjectRoot:
    def test_finds_project_with_venv(self, fake_project: Path, command_file: Path):
        result = _find_project_root(command_file)
        assert result == fake_project

    def test_returns_none_without_pyproject(self, tmp_path: Path):
        (tmp_path / ".venv").mkdir()
        cmd = tmp_path / "foo.py"
        cmd.write_text("")
        assert _find_project_root(cmd) is None

    def test_returns_none_without_venv(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
        cmd = tmp_path / "foo.py"
        cmd.write_text("")
        assert _find_project_root(cmd) is None


class TestIsCurrentVenv:
    def test_current_venv_matches(self):
        assert _is_current_venv(Path(sys.prefix))

    def test_different_venv_does_not_match(self, fake_project: Path):
        assert not _is_current_venv(fake_project / ".venv")


class TestPyprojectVenvResolver:
    def test_detects_different_venv(self, fake_project: Path, command_file: Path):
        resolver = PyprojectVenvResolver()
        result = resolver.resolve(command_file)
        assert isinstance(result, VenvMatch)
        assert result.project_root == fake_project

    def test_returns_none_for_current_venv(self, tmp_path: Path):
        """Command in a project whose venv is the current one returns None."""
        # Point a pyproject.toml at our actual venv
        project = tmp_path / "current"
        project.mkdir()
        (project / "pyproject.toml").write_text('[project]\nname = "x"\n')
        # Symlink .venv to our actual prefix
        (project / ".venv").symlink_to(sys.prefix)
        cmd = project / "cmd.py"
        cmd.write_text("")

        resolver = PyprojectVenvResolver()
        assert resolver.resolve(cmd) is None

    def test_returns_none_for_no_project(self, tmp_path: Path):
        """Command not inside any project returns None."""
        cmd = tmp_path / "orphan.py"
        cmd.write_text("")

        resolver = PyprojectVenvResolver()
        assert resolver.resolve(cmd) is None
