"""Tests for sandbox package discovery."""

from pathlib import Path

import pytest

from mg import test
from mg.test import SandboxConfig, create_sandbox
from mg.paths import PkgPaths


class TestSandboxPkgDiscovery:
    """Tests for automatic package discovery in sandbox."""

    def test_sandbox_has_pkg_paths(self):
        """Sandbox ctx.paths.pkg is a PkgPaths instance."""
        sandbox = create_sandbox()
        assert isinstance(sandbox.ctx.paths.pkg, PkgPaths)

    def test_pkg_root_points_to_module(self):
        """pkg.root points to a module directory (contains __init__.py or is importable).

        Note: This is a bit of a hack. The mg repo isn't an mg-structured package
        (no commands folder, etc.), but it does have src/mg/ with __init__.py.
        Good enough to verify auto-discovery logic without complex scaffolding.
        """
        sandbox = create_sandbox()
        # Should point to src/mg/ since this test is in mg/tests/
        assert sandbox.ctx.paths.pkg.root.parent.name == "src"
        assert sandbox.ctx.paths.pkg.root.name == "mg"
        assert (sandbox.ctx.paths.pkg.root / "__init__.py").exists()

    def test_pkg_assets_derived_from_root(self):
        """pkg.assets is __assets__ under pkg.root."""
        sandbox = create_sandbox()
        assert sandbox.ctx.paths.pkg.assets == sandbox.ctx.paths.pkg.root / "__assets__"


class TestSandboxPkgOverride:
    """Tests for explicit pkg_root override."""

    def test_pkg_root_override(self, tmp_path):
        """Can override pkg_root via SandboxConfig."""
        custom_pkg = tmp_path / "custom_module"
        custom_pkg.mkdir()

        sandbox = create_sandbox(SandboxConfig(pkg_root=custom_pkg))

        assert sandbox.ctx.paths.pkg.root == custom_pkg

    def test_pkg_assets_with_override(self, tmp_path):
        """pkg.assets works with overridden pkg_root."""
        custom_pkg = tmp_path / "custom_module"
        custom_pkg.mkdir()

        sandbox = create_sandbox(SandboxConfig(pkg_root=custom_pkg))

        assert sandbox.ctx.paths.pkg.assets == custom_pkg / "__assets__"
