"""Tests for hv tui restart."""

from haiv import test


class TestRestartRouting:

    def test_routes_to_restart_file(self):
        match = test.require_routes_to("tui restart")
        assert match.file.name == "restart.py"

    def test_parses(self):
        test.parse("tui restart")
