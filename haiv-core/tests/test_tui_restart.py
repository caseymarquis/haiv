"""Tests for hv tui restart."""

from haiv import test


class TestRestartRouting:

    def test_routes_to_restart_file(self):
        match = test.require_routes_to("tui restart")
        assert match.file.name == "restart.py"


class TestRestartExecution:

    def test_runs_without_error(self, capsys):
        test.execute("tui restart")
        captured = capsys.readouterr()
        assert "Not yet wired" in captured.out
