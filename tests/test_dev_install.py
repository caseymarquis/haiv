"""Tests for hv dev install command."""

import stat

import pytest


class TestDevInstall:
    """Tests for dev install command."""

    def test_routes_to_dev_install(self):
        """Command routes to dev/install.py."""
        from haiv import test

        match = test.routes_to("dev install", expected="dev/install.py")
        assert match.file is not None

    def test_errors_if_worktree_missing(self, monkeypatch, tmp_path):
        """Errors if specified worktree doesn't exist."""
        from haiv import test
        from haiv.errors import CommandError

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            ctx.paths.worktrees.mkdir(parents=True)

        with pytest.raises(CommandError, match="Worktree not found"):
            test.execute("dev install --branch nonexistent", setup=setup)

    def test_errors_if_haiv_cli_missing(self, monkeypatch, tmp_path):
        """Errors if worktree exists but doesn't have haiv-cli."""
        from haiv import test
        from haiv.errors import CommandError

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "main").mkdir(parents=True)

        with pytest.raises(CommandError, match="haiv-cli not found"):
            test.execute("dev install", setup=setup)

    def test_errors_if_already_installed(self, monkeypatch, tmp_path):
        """Errors if hv already installed (without --force)."""
        from haiv import test
        from haiv.errors import CommandError

        # Create existing hv installation
        bin_dir = tmp_path / ".local" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "hv").write_text("#!/bin/bash\necho old")

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "main" / "haiv-cli").mkdir(parents=True)

        with pytest.raises(CommandError, match="already installed"):
            test.execute("dev install", setup=setup)

    def test_force_overwrites_existing(self, monkeypatch, tmp_path):
        """--force overwrites existing installation."""
        from haiv import test

        # Create existing hv installation
        bin_dir = tmp_path / ".local" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "hv").write_text("#!/bin/bash\necho old")

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "main" / "haiv-cli").mkdir(parents=True)

        test.execute("dev install --force", setup=setup)

        # Should be overwritten
        content = (bin_dir / "hv").read_text()
        assert "old" not in content
        assert "uv run" in content

    def test_creates_executable_script(self, monkeypatch, tmp_path):
        """Creates an executable shell script."""
        from haiv import test

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "main" / "haiv-cli").mkdir(parents=True)

        test.execute("dev install", setup=setup)

        haiv_path = tmp_path / ".local" / "bin" / "hv"
        assert haiv_path.exists()
        assert haiv_path.stat().st_mode & stat.S_IXUSR  # Is executable

    def test_script_contains_correct_paths(self, monkeypatch, tmp_path):
        """Script references correct haiv_root and branch."""
        from haiv import test

        monkeypatch.setenv("HOME", str(tmp_path))

        haiv_root_path = None

        def setup(ctx):
            nonlocal haiv_root_path
            haiv_root_path = ctx.paths.root
            (ctx.paths.worktrees / "main" / "haiv-cli").mkdir(parents=True)

        test.execute("dev install --branch main", setup=setup)

        content = (tmp_path / ".local" / "bin" / "hv").read_text()
        assert str(haiv_root_path) in content
        assert "worktrees/main" in content
        assert "haiv-cli" in content

    def test_uses_specified_branch(self, monkeypatch, tmp_path):
        """Uses --branch to specify which worktree."""
        from haiv import test

        monkeypatch.setenv("HOME", str(tmp_path))

        def setup(ctx):
            (ctx.paths.worktrees / "feature-x" / "haiv-cli").mkdir(parents=True)

        test.execute("dev install --branch feature-x", setup=setup)

        content = (tmp_path / ".local" / "bin" / "hv").read_text()
        assert "worktrees/feature-x" in content

    def test_creates_bin_directory(self, monkeypatch, tmp_path):
        """Creates ~/.local/bin if it doesn't exist."""
        from haiv import test

        monkeypatch.setenv("HOME", str(tmp_path))

        # Ensure .local/bin doesn't exist
        assert not (tmp_path / ".local" / "bin").exists()

        def setup(ctx):
            (ctx.paths.worktrees / "main" / "haiv-cli").mkdir(parents=True)

        test.execute("dev install", setup=setup)

        assert (tmp_path / ".local" / "bin" / "hv").exists()
