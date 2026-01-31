"""Tests for mg start command (no args)."""

from unittest.mock import MagicMock, patch

from mg import test


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
            ctx.paths._mg_root = tmp_path

        with patch("mg.cmd.Tui") as mock_tui_class:
            mock_tui = MagicMock()
            mock_tui_class.return_value = mock_tui

            test.execute("start", setup=setup)

            mock_tui.start.assert_called_once()
