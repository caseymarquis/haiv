"""Tests for hv start command (no args)."""

from typing import cast
from unittest.mock import MagicMock

from haiv import test


class TestStartRouting:
    """Test that 'start' (no args) routes correctly."""

    def test_routes_to_index_file(self):
        """'start' routes to start/_index_.py."""
        match = test.require_routes_to("start")
        assert match.file.name == "_index_.py"
        assert "start" in str(match.file)


class TestStartParsing:
    """Test start command parses correctly."""

    def test_parses_without_args(self):
        """Command parses with no arguments."""
        ctx = test.parse("start")
        # No args expected - just verify it parses
        assert ctx is not None


class TestStartExecution:
    """Test start command execution."""

    def test_calls_tui_start(self, tmp_path):
        """Execution calls ctx.tui.start()."""

        def setup(ctx):
            ctx.paths._haiv_root = tmp_path

        result = test.execute("start", setup=setup)
        mock_tui = cast(MagicMock, result.ctx.tui)
        mock_tui.start.assert_called_once()
