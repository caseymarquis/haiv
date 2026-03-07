"""Tests for sandbox package discovery."""

from pathlib import Path

import pytest

from haiv import test
from haiv.test import SandboxConfig, create_sandbox
from haiv.paths import PkgPaths


class TestSandboxPkgDiscovery:
    """Tests for automatic package discovery in sandbox."""

    def test_sandbox_has_pkg_paths(self):
        """Sandbox ctx.paths.pkgs.current is a PkgPaths instance."""
        sandbox = create_sandbox()
        assert isinstance(sandbox.ctx.paths.pkgs.current, PkgPaths)

    def test_pkg_root_points_to_module(self):
        """pkg.root points to a module directory (contains __init__.py or is importable).

        Note: This is a bit of a hack. The haiv repo isn't a haiv-structured package
        (no commands folder, etc.), but it does have src/haiv/ with __init__.py.
        Good enough to verify auto-discovery logic without complex scaffolding.
        """
        sandbox = create_sandbox()
        # Should point to src/haiv/ since this test is in haiv/tests/
        assert sandbox.ctx.paths.pkgs.current.root.parent.name == "src"
        assert sandbox.ctx.paths.pkgs.current.root.name == "haiv"
        assert (sandbox.ctx.paths.pkgs.current.root / "__init__.py").exists()

    def test_pkg_assets_derived_from_root(self):
        """pkg.assets_dir is __assets__ under pkg.root."""
        sandbox = create_sandbox()
        assert sandbox.ctx.paths.pkgs.current.assets_dir == sandbox.ctx.paths.pkgs.current.root / "__assets__"


class TestSandboxPkgOverride:
    """Tests for explicit pkg_root override."""

    def test_pkg_root_override(self, tmp_path):
        """Can override pkg_root via SandboxConfig."""
        custom_pkg = tmp_path / "custom_module"
        custom_pkg.mkdir()

        sandbox = create_sandbox(SandboxConfig(pkg_root=custom_pkg))

        assert sandbox.ctx.paths.pkgs.current.root == custom_pkg

    def test_pkg_assets_with_override(self, tmp_path):
        """pkg.assets_dir works with overridden pkg_root."""
        custom_pkg = tmp_path / "custom_module"
        custom_pkg.mkdir()

        sandbox = create_sandbox(SandboxConfig(pkg_root=custom_pkg))

        assert sandbox.ctx.paths.pkgs.current.assets_dir == custom_pkg / "__assets__"
