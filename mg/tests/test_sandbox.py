"""Tests for sandbox integration testing infrastructure."""

import gc
from pathlib import Path

import pytest

from mg import test
from mg.test import Sandbox, SandboxConfig, create_sandbox
from mg.paths import Paths


class TestCreateSandbox:
    def test_returns_sandbox(self):
        sandbox = create_sandbox()
        assert isinstance(sandbox, Sandbox)

    def test_accepts_config(self):
        config = SandboxConfig(explicit=True)
        sandbox = create_sandbox(config)
        assert sandbox._config.explicit is True

    def test_default_config_when_none(self):
        sandbox = create_sandbox()
        assert sandbox._config.explicit is False


class TestSandboxStructure:
    def test_root_is_nested_three_levels(self):
        sandbox = create_sandbox()
        # temp_dir/grandparent/parent/root
        assert sandbox._root.parent.name == "parent"
        assert sandbox._root.parent.parent.name == "grandparent"
        assert sandbox._root.parent.parent.parent == sandbox._temp_dir

    def test_root_directory_exists(self):
        sandbox = create_sandbox()
        assert sandbox._root.is_dir()

    def test_cwd_starts_at_root(self):
        sandbox = create_sandbox()
        assert sandbox._cwd == sandbox._root


class TestSandboxCtx:
    def test_ctx_has_paths(self):
        sandbox = create_sandbox()
        assert sandbox.ctx.paths is not None
        assert isinstance(sandbox.ctx.paths, Paths)

    def test_ctx_paths_root_matches_sandbox_root(self):
        sandbox = create_sandbox()
        assert sandbox.ctx.paths.root == sandbox._root

    def test_ctx_has_container(self):
        sandbox = create_sandbox()
        assert sandbox.ctx.container is not None

    def test_ctx_has_empty_args(self):
        sandbox = create_sandbox()
        assert sandbox.ctx.args.route == []
        assert sandbox.ctx.args.rest == []

    def test_ctx_has_called_from(self):
        sandbox = create_sandbox()
        assert sandbox.ctx.paths.called_from is not None
        assert sandbox.ctx.paths.called_from == sandbox._root

    def test_ctx_called_from_reflects_cd(self):
        sandbox = create_sandbox()
        subdir = sandbox._root / "subdir"
        subdir.mkdir()
        sandbox.cd("subdir")
        assert sandbox.ctx.paths.called_from == subdir


class TestSandboxCd:
    def test_cd_absolute_path(self):
        sandbox = create_sandbox()
        new_path = sandbox._temp_dir / "somewhere"
        new_path.mkdir()
        sandbox.cd(new_path)
        assert sandbox._cwd == new_path

    def test_cd_relative_path(self):
        sandbox = create_sandbox()
        subdir = sandbox._root / "subdir"
        subdir.mkdir()
        sandbox.cd("subdir")
        assert sandbox._cwd == subdir

    def test_cd_parent_relative(self):
        sandbox = create_sandbox()
        original = sandbox._cwd
        sandbox.cd("..")
        assert sandbox._cwd == original.parent

    def test_cd_accepts_string(self):
        sandbox = create_sandbox()
        subdir = sandbox._root / "mydir"
        subdir.mkdir()
        sandbox.cd("mydir")
        assert sandbox._cwd == subdir


class TestSandboxRun:
    @pytest.fixture
    def commands(self):
        from tests.fixtures.fake_commands import commands
        return commands

    def test_run_returns_ctx(self, commands):
        sandbox = create_sandbox()
        ctx = sandbox.run("simple", commands)
        assert ctx is not None

    def test_run_ctx_has_parsed_args(self, commands):
        sandbox = create_sandbox()
        ctx = sandbox.run("alice greet", commands)
        assert ctx.args.get_one("name") == "alice"

    def test_run_ctx_has_paths(self, commands):
        sandbox = create_sandbox()
        ctx = sandbox.run("simple", commands)
        assert ctx.paths is not None
        assert ctx.paths.root == sandbox._root

    def test_run_ctx_shares_container(self, commands):
        sandbox = create_sandbox()
        ctx = sandbox.run("simple", commands)
        assert ctx.container is sandbox.ctx.container

    def test_run_ctx_has_called_from(self, commands):
        sandbox = create_sandbox()
        ctx = sandbox.run("simple", commands)
        assert ctx.paths.called_from == sandbox._root

    def test_run_ctx_called_from_reflects_cd(self, commands):
        sandbox = create_sandbox()
        subdir = sandbox._root / "subdir"
        subdir.mkdir()
        sandbox.cd("subdir")
        ctx = sandbox.run("simple", commands)
        assert ctx.paths.called_from == subdir


class TestSandboxCleanup:
    def test_cleanup_removes_temp_dir(self):
        import subprocess
        import sys

        # Run in subprocess to ensure clean gc
        code = """
from mg.test import create_sandbox
sandbox = create_sandbox()
print(sandbox._temp_dir)
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
        )
        temp_dir = Path(result.stdout.strip())

        # After subprocess exits, temp dir should be cleaned up
        assert not temp_dir.exists()

    def test_cleanup_removes_nested_content(self):
        import subprocess
        import sys

        code = """
from mg.test import create_sandbox
sandbox = create_sandbox()
nested = sandbox._root / "test.txt"
nested.write_text("hello")
print(sandbox._temp_dir)
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
        )
        temp_dir = Path(result.stdout.strip())

        assert not temp_dir.exists()
