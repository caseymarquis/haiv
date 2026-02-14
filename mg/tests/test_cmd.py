"""Tests for cmd module - Args, Ctx, Def."""

from pathlib import Path

import pytest
from mg import cmd
from mg.paths import Paths


def make_paths() -> Paths:
    """Create a minimal Paths for testing."""
    return Paths(
        _called_from=Path("/test/cwd"),
        _pkg_root=Path("/test/pkg"),
        _mg_root=None,
    )


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
        ctx = cmd.Ctx(args=args, paths=make_paths())
        assert ctx.args is args

    def test_ctx_has_container(self):
        """Ctx has container for dependency injection."""
        from punq import Container

        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())
        assert isinstance(ctx.container, Container)

    def test_ctx_container_can_register_and_resolve(self):
        """Container supports register/resolve."""
        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())

        class MockDB:
            pass

        ctx.container.register(MockDB)
        resolved = ctx.container.resolve(MockDB)
        assert isinstance(resolved, MockDB)

    def test_ctx_print_outputs(self, capsys):
        """Ctx.print() outputs text."""
        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())
        ctx.print("hello")
        captured = capsys.readouterr()
        assert captured.out == "hello\n"


class TestMindNS:
    """Tests for MindNS class."""

    def test_checklist_prints_items_numbered(self):
        """Items are printed as a numbered list."""
        lines = []
        mind = cmd.MindNS(lines.append)
        mind.checklist(items=["First", "Second", "Third"], preamble=None)

        assert "  1. First" in lines
        assert "  2. Second" in lines
        assert "  3. Third" in lines

    def test_checklist_default_preamble(self):
        """Default preamble encourages task creation."""
        lines = []
        mind = cmd.MindNS(lines.append)
        mind.checklist(items=["Do something"])

        assert any("Create a task for each item" in line for line in lines)
        assert any("genuine consideration" in line for line in lines)

    def test_checklist_custom_preamble(self):
        """Custom preamble replaces the default."""
        lines = []
        mind = cmd.MindNS(lines.append)
        mind.checklist(items=["Do something"], preamble="Custom guidance.")

        assert "Custom guidance." in lines
        assert not any("Create a task" in line for line in lines)

    def test_checklist_preamble_none_omits(self):
        """preamble=None omits the preamble entirely."""
        lines = []
        mind = cmd.MindNS(lines.append)
        mind.checklist(items=["Do something"], preamble=None)

        # First line should be the item, no preamble or blank line
        assert lines[0] == "  1. Do something"

    def test_checklist_postamble(self):
        """Postamble is printed after the items."""
        lines = []
        mind = cmd.MindNS(lines.append)
        mind.checklist(items=["Do something"], preamble=None, postamble="Final thought.")

        assert lines[-1] == "Final thought."

    def test_checklist_postamble_none_omits(self):
        """postamble=None omits the postamble."""
        lines = []
        mind = cmd.MindNS(lines.append)
        mind.checklist(items=["Do something"], preamble=None, postamble=None)

        assert len(lines) == 1
        assert lines[0] == "  1. Do something"

    def test_checklist_full_structure(self):
        """Full output: preamble, blank, items, blank, postamble."""
        lines = []
        mind = cmd.MindNS(lines.append)
        mind.checklist(
            items=["Alpha", "Beta"],
            preamble="Before.",
            postamble="After.",
        )

        assert lines == [
            "Before.",
            "",
            "  1. Alpha",
            "  2. Beta",
            "",
            "After.",
        ]

    def test_ctx_mind_property(self, capsys):
        """ctx.mind returns a MindNS that prints via ctx.print."""
        ctx = cmd.Ctx(args=cmd.Args(), paths=make_paths())
        ctx.mind.checklist(items=["Test"], preamble=None, postamble=None)
        output = capsys.readouterr().out
        assert "1. Test" in output


class TestDef:
    """Tests for Def class."""

    def test_def_has_description(self):
        """Def has description."""
        d = cmd.Def(description="Do something")
        assert d.description == "Do something"
