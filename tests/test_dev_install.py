"""Tests for mg dev install command."""

import stat

import pytest


class TestDevInstall:
    """Tests for dev install command."""

    def test_routes_to_dev_install(self):
        """Command routes to dev/install.py."""
        from mg import test

        match = test.routes_to("dev install", expected="dev/install.py")
        assert match.file is not None

    def test_errors_if_worktree_missing(self, monkeypatch, tmp_path):
        """Errors if specified worktree doesn't exist."""
        from mg import test
        from mg.errors import CommandError

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            ctx.paths.worktrees.mkdir(parents=True)

        with pytest.raises(CommandError, match="Worktree not found"):
            test.execute("dev install --branch nonexistent", setup=setup)

    def test_errors_if_mg_cli_missing(self, monkeypatch, tmp_path):
        """Errors if worktree exists but doesn't have mg-cli."""
        from mg import test
        from mg.errors import CommandError

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "main").mkdir(parents=True)

        with pytest.raises(CommandError, match="mg-cli not found"):
            test.execute("dev install", setup=setup)

    def test_errors_if_already_installed(self, monkeypatch, tmp_path):
        """Errors if mg already installed (without --force)."""
        from mg import test
        from mg.errors import CommandError

        # Create existing mg installation
        bin_dir = tmp_path / ".local" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "mg").write_text("#!/bin/bash\necho old")

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "main" / "mg-cli").mkdir(parents=True)

        with pytest.raises(CommandError, match="already installed"):
            test.execute("dev install", setup=setup)

    def test_force_overwrites_existing(self, monkeypatch, tmp_path):
        """--force overwrites existing installation."""
        from mg import test

        # Create existing mg installation
        bin_dir = tmp_path / ".local" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "mg").write_text("#!/bin/bash\necho old")

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "main" / "mg-cli").mkdir(parents=True)

        test.execute("dev install --force", setup=setup)

        # Should be overwritten
        content = (bin_dir / "mg").read_text()
        assert "old" not in content
        assert "uv run" in content

    def test_creates_executable_script(self, monkeypatch, tmp_path):
        """Creates an executable shell script."""
        from mg import test

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "main" / "mg-cli").mkdir(parents=True)

        test.execute("dev install", setup=setup)

        mg_path = tmp_path / ".local" / "bin" / "mg"
        assert mg_path.exists()
        assert mg_path.stat().st_mode & stat.S_IXUSR  # Is executable

    def test_script_contains_correct_paths(self, monkeypatch, tmp_path):
        """Script references correct mg_root and branch."""
        from mg import test

        monkeypatch.setenv("HOME", str(tmp_path))

        mg_root_path = None

        def setup(ctx):
            nonlocal mg_root_path
            mg_root_path = ctx.paths.root
            (ctx.paths.worktrees / "main" / "mg-cli").mkdir(parents=True)

        test.execute("dev install --branch main", setup=setup)

        content = (tmp_path / ".local" / "bin" / "mg").read_text()
        assert str(mg_root_path) in content
        assert "worktrees/main" in content
        assert "mg-cli" in content

    def test_uses_specified_branch(self, monkeypatch, tmp_path):
        """Uses --branch to specify which worktree."""
        from mg import test

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "feature-x" / "mg-cli").mkdir(parents=True)

        test.execute("dev install --branch feature-x", setup=setup)

        content = (tmp_path / ".local" / "bin" / "mg").read_text()
        assert "worktrees/feature-x" in content

    def test_creates_bin_directory(self, monkeypatch, tmp_path):
        """Creates ~/.local/bin if it doesn't exist."""
        from mg import test

        monkeypatch.setenv("HOME", str(tmp_path))

        # Ensure .local/bin doesn't exist
        assert not (tmp_path / ".local" / "bin").exists()

        def setup(ctx):
            (ctx.paths.worktrees / "main" / "mg-cli").mkdir(parents=True)

        test.execute("dev install", setup=setup)

        assert (tmp_path / ".local" / "bin" / "mg").exists()
