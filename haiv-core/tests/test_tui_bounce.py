"""Tests for hv tui bounce."""

from haiv import test


class TestBounceRouting:

    def test_routes_to_bounce_file(self):
        match = test.require_routes_to("tui bounce")
        assert match.file.name == "bounce.py"

    def test_parses(self):
        test.parse("tui bounce")
