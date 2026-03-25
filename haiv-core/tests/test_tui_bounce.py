"""Tests for hv tui bounce."""

from haiv import test


class TestBounceRouting:

    def test_routes_to_bounce_file(self):
        match = test.require_routes_to("tui bounce")
        assert match.file.name == "bounce.py"


class TestBounceExecution:

    def test_runs_without_error(self, capsys):
        test.execute("tui bounce")
        captured = capsys.readouterr()
        assert "Not yet wired" in captured.out
