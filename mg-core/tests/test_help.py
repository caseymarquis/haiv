"""Tests for hv help command."""

from haiv import test


class TestHelpRouting:
    """Test that 'help' routes correctly."""

    def test_routes_to_help_file(self):
        """'help' routes to help.py."""
        match = test.require_routes_to("help")
        assert match.file.name == "help.py"


class TestHelpListing:
    """Test help command listing."""

    def test_shows_available_commands(self, capsys):
        """help lists available commands."""
        test.execute("help")

        captured = capsys.readouterr()
        assert "help" in captured.out
        assert "List available commands" in captured.out

    def test_shows_hint_for_detailed_help(self, capsys):
        """help shows hint about --for flag."""
        test.execute("help")

        captured = capsys.readouterr()
        assert "--for" in captured.out

    def test_groups_by_package(self, capsys):
        """help groups commands by package."""
        test.execute("help")

        captured = capsys.readouterr()
        assert "haiv_core" in captured.out

    def test_shows_numbered_ids(self, capsys):
        """help shows numbered IDs for commands."""
        test.execute("help")

        captured = capsys.readouterr()
        # Should have IDs like 1.1, 1.2, etc.
        assert "1.1" in captured.out
        assert "1.2" in captured.out


class TestHelpForNumericId:
    """Test --for with numeric ID."""

    def test_shows_command_detail(self, capsys):
        """--for with valid ID shows command detail."""
        test.execute("help --for 1.2")

        captured = capsys.readouterr()
        assert "Description:" in captured.out
        assert "Flags:" in captured.out
        assert "Module:" in captured.out
        assert "File:" in captured.out
        assert "Full path:" in captured.out

    def test_invalid_id_shows_error(self, capsys):
        """--for with invalid ID shows error."""
        test.execute("help --for 99.99")

        captured = capsys.readouterr()
        assert "No command with ID" in captured.out


class TestHelpForPattern:
    """Test --for with pattern matching."""

    def test_single_match_shows_detail(self, capsys):
        """--for with pattern matching one command shows detail."""
        test.execute("help --for ^help$")

        captured = capsys.readouterr()
        assert "Description:" in captured.out
        assert "List available commands" in captured.out

    def test_multiple_matches_shows_list(self, capsys):
        """--for with pattern matching multiple commands shows list."""
        test.execute("help --for session")

        captured = capsys.readouterr()
        assert "Multiple commands matching" in captured.out
        assert "sessions" in captured.out

    def test_no_matches_shows_error(self, capsys):
        """--for with no matches shows error."""
        test.execute("help --for xyznonexistent")

        captured = capsys.readouterr()
        assert "No commands matching" in captured.out

    def test_invalid_regex_shows_error(self, capsys):
        """--for with invalid regex shows error."""
        test.execute("help --for '[invalid'")

        captured = capsys.readouterr()
        assert "Invalid pattern" in captured.out
