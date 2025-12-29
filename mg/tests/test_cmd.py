"""Tests for cmd module - Args, Ctx, Def."""

import pytest
from mg import cmd


class TestArgs:
    """Tests for Args class."""

    def test_has_returns_false_when_missing(self):
        """has() returns False for missing argument."""
        args = cmd.Args()
        assert args.has("missing") is False

    def test_has_returns_true_when_present(self):
        """has() returns True for present argument."""
        args = cmd.Args()
        args._values["present"] = ["value"]
        assert args.has("present") is True

    def test_get_list_raises_when_missing_no_default(self):
        """get_list() raises KeyError when missing and no default."""
        args = cmd.Args()
        with pytest.raises(KeyError, match="Required argument 'missing'"):
            args.get_list("missing")

    def test_get_list_returns_default_when_missing(self):
        """get_list() returns default when missing."""
        args = cmd.Args()
        result = args.get_list("missing", default_value=["default"])
        assert result == ["default"]

    def test_get_list_returns_values_when_present(self):
        """get_list() returns values when present."""
        args = cmd.Args()
        args._values["files"] = ["a.txt", "b.txt"]
        result = args.get_list("files")
        assert result == ["a.txt", "b.txt"]

    def test_get_one_raises_when_missing_no_default(self):
        """get_one() raises KeyError when missing and no default."""
        args = cmd.Args()
        with pytest.raises(KeyError, match="Required argument 'missing'"):
            args.get_one("missing")

    def test_get_one_returns_default_when_missing(self):
        """get_one() returns default when missing."""
        args = cmd.Args()
        result = args.get_one("name", default_value="default")
        assert result == "default"

    def test_get_one_returns_value_when_exactly_one(self):
        """get_one() returns single value."""
        args = cmd.Args()
        args._values["name"] = ["alice"]
        result = args.get_one("name")
        assert result == "alice"

    def test_get_one_raises_when_multiple(self):
        """get_one() raises ValueError when multiple values."""
        args = cmd.Args()
        args._values["name"] = ["alice", "bob"]
        with pytest.raises(ValueError, match="Expected exactly one"):
            args.get_one("name")

    def test_get_first_raises_when_missing_no_default(self):
        """get_first() raises KeyError when missing and no default."""
        args = cmd.Args()
        with pytest.raises(KeyError, match="Required argument 'missing'"):
            args.get_first("missing")

    def test_get_first_returns_default_when_missing(self):
        """get_first() returns default when missing."""
        args = cmd.Args()
        result = args.get_first("name", default_value="default")
        assert result == "default"

    def test_get_first_returns_first_when_multiple(self):
        """get_first() returns first value when multiple."""
        args = cmd.Args()
        args._values["name"] = ["alice", "bob"]
        result = args.get_first("name")
        assert result == "alice"

    def test_get_first_raises_when_empty_list(self):
        """get_first() raises ValueError when empty list."""
        args = cmd.Args()
        args._values["name"] = []
        with pytest.raises(ValueError, match="Expected at least one"):
            args.get_first("name")

    def test_default_value_none_is_valid(self):
        """None can be a valid default value."""
        args = cmd.Args()
        result = args.get_one("missing", default_value=None)
        assert result is None


class TestCtx:
    """Tests for Ctx class."""

    def test_ctx_has_args(self):
        """Ctx has args property."""
        args = cmd.Args()
        ctx = cmd.Ctx(args=args)
        assert ctx.args is args

    def test_ctx_has_container(self):
        """Ctx has container for dependency injection."""
        from punq import Container

        ctx = cmd.Ctx(args=cmd.Args())
        assert isinstance(ctx.container, Container)

    def test_ctx_container_can_register_and_resolve(self):
        """Container supports register/resolve."""
        ctx = cmd.Ctx(args=cmd.Args())

        class MockDB:
            pass

        ctx.container.register(MockDB)
        resolved = ctx.container.resolve(MockDB)
        assert isinstance(resolved, MockDB)

    def test_ctx_print_outputs(self, capsys):
        """Ctx.print() outputs text."""
        ctx = cmd.Ctx(args=cmd.Args())
        ctx.print("hello")
        captured = capsys.readouterr()
        assert captured.out == "hello\n"


class TestDef:
    """Tests for Def class."""

    def test_def_has_description(self):
        """Def has description."""
        d = cmd.Def(description="Do something")
        assert d.description == "Do something"
