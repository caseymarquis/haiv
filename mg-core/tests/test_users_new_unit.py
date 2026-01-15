"""Unit tests for mg users new command.

These test routing and flag parsing without executing the command.
Integration tests are in test_users_new.py.
"""

import pytest

from mg import test


class TestUsersNewRouting:
    """Test that 'users new' routes to users/new.py."""

    def test_routes(self):
        """'users new' routes to users/new.py."""
        match = test.require_routes_to("users new")
        assert match.file.name == "new.py"

    def test_routes_with_flags(self):
        """'users new --name foo' still routes to users/new.py."""
        match = test.require_routes_to("users new --name foo")
        assert match.file.name == "new.py"


class TestUsersNewFlagParsing:
    """Test flag parsing for users new command."""

    def test_parses_without_flags(self):
        """'users new' parses (name validated in execute)."""
        ctx = test.parse("users new")
        assert ctx.args is not None

    def test_name_flag_parsed(self):
        """--name flag takes a value."""
        ctx = test.parse("users new --name casey")
        assert ctx.args.get_one("name") == "casey"

    def test_name_flag_with_equals(self):
        """--name=value syntax works."""
        ctx = test.parse("users new --name=casey")
        assert ctx.args.get_one("name") == "casey"

    def test_replace_flag_parsed(self):
        """--replace flag is parsed."""
        ctx = test.parse("users new --name casey --replace")
        assert ctx.args.has("replace")
        assert ctx.args.get_one("replace") is True

    def test_merge_flag_parsed(self):
        """--merge flag is parsed."""
        ctx = test.parse("users new --name casey --merge")
        assert ctx.args.has("merge")
        assert ctx.args.get_one("merge") is True

    def test_quiet_flag_parsed(self):
        """--quiet flag is parsed."""
        ctx = test.parse("users new --name casey --quiet")
        assert ctx.args.has("quiet")
        assert ctx.args.get_one("quiet") is True

    def test_replace_and_merge_mutually_exclusive(self):
        """--replace and --merge cannot be used together."""
        # This will be enforced in execute(), not parse()
        # So both flags can be present after parsing
        ctx = test.parse("users new --name casey --replace --merge")
        assert ctx.args.has("replace")
        assert ctx.args.has("merge")

    def test_unknown_flag_raises(self):
        """Unknown flags raise an error."""
        with pytest.raises(ValueError, match="Unknown flag"):
            test.parse("users new --name casey --invalid")
