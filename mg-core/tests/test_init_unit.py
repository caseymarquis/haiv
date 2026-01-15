"""Unit tests for mg init command.

These test routing and flag parsing without executing the command.
Integration tests are in test_init.py.
"""

import pytest

from mg import cmd, test


class TestInitRouting:
    """Test that 'init' routes to init.py."""

    def test_init_routes(self):
        """'init' routes to init.py."""
        match = test.require_routes_to("init")
        assert match.file.name == "init.py"

    def test_init_with_flags_routes(self):
        """'init --force' still routes to init.py."""
        match = test.require_routes_to("init --force")
        assert match.file.name == "init.py"


class TestInitFlagParsing:
    """Test flag parsing for init command."""

    def test_parses_without_flags(self):
        """'init' parses successfully with no flags."""
        ctx = test.parse("init")
        assert ctx.args is not None

    def test_force_flag_parsed(self):
        """--force flag is parsed."""
        ctx = test.parse("init --force")
        assert ctx.args.has("force")
        assert ctx.args.get_one("force") is True

    def test_force_flag_absent(self):
        """Without --force, flag is absent."""
        ctx = test.parse("init")
        assert not ctx.args.has("force")

    def test_branch_flag_parsed(self):
        """--branch flag takes a value."""
        ctx = test.parse("init --branch develop")
        assert ctx.args.get_one("branch") == "develop"

    def test_branch_flag_with_equals(self):
        """--branch=value syntax works."""
        ctx = test.parse("init --branch=feature-x")
        assert ctx.args.get_one("branch") == "feature-x"

    def test_empty_flag_parsed(self):
        """--empty flag is parsed."""
        ctx = test.parse("init --empty")
        assert ctx.args.has("empty")
        assert ctx.args.get_one("empty") is True

    def test_quiet_flag_parsed(self):
        """--quiet flag is parsed."""
        ctx = test.parse("init --quiet")
        assert ctx.args.has("quiet")
        assert ctx.args.get_one("quiet") is True

    def test_multiple_flags_combined(self):
        """Multiple flags can be combined."""
        ctx = test.parse("init --force --branch main --quiet")
        assert ctx.args.get_one("force") is True
        assert ctx.args.get_one("branch") == "main"
        assert ctx.args.get_one("quiet") is True

    def test_unknown_flag_raises(self):
        """Unknown flags raise an error."""
        with pytest.raises(ValueError, match="Unknown flag"):
            test.parse("init --invalid")
