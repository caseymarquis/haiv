"""Tests for hv chart command."""

from haiv import test


class TestChartRouting:
    """Test that 'chart' routes correctly."""

    def test_routes_to_chart_file(self):
        """'chart' routes to chart/_index_.py."""
        match = test.require_routes_to("chart")
        assert match.file.name == "_index_.py"


class TestChartOutput:
    """Test chart command output."""

    def test_shows_atlas_location(self, capsys):
        """chart shows where the atlas lives."""
        test.execute("chart")

        captured = capsys.readouterr()
        assert "atlas" in captured.out

    def test_shows_finding_advice(self, capsys):
        """chart shows the finding-what-you-need path."""
        test.execute("chart")

        captured = capsys.readouterr()
        assert "FINDING WHAT YOU NEED" in captured.out
        assert "Check the maps" in captured.out
        assert "quest board" in captured.out
        assert "journals" in captured.out

    def test_shows_charting_rules(self, capsys):
        """chart shows the rules for exploration."""
        test.execute("chart")

        captured = capsys.readouterr()
        assert "RULES FOR CHARTING NEW TERRITORY" in captured.out
        assert "No silent reads" in captured.out
        assert "research log" in captured.out

    def test_shows_mystery_guidance(self, capsys):
        """chart tells explorers about mysteries."""
        test.execute("chart")

        captured = capsys.readouterr()
        assert "mystery" in captured.out

    def test_shows_rewards(self, capsys):
        """chart shows available rewards."""
        test.execute("chart")

        captured = capsys.readouterr()
        assert "REWARDS" in captured.out
        assert "Landmark" in captured.out
        assert "Trade Route" in captured.out
        assert "Compass" in captured.out
        assert "Inbeeyana Combs" in captured.out


class TestChartWithGoal:
    """Test chart command with --goal flag."""

    def test_includes_goal_in_output(self, capsys):
        """chart --goal shows the goal."""
        test.execute('chart --goal "understand resolvers"')

        captured = capsys.readouterr()
        assert "understand resolvers" in captured.out


class TestChartCreatesAtlas:
    """Test that chart creates the atlas structure."""

    def test_creates_atlas_directories(self):
        """chart creates atlas/, journeys/, and maps/ if missing."""
        result = test.execute("chart")

        atlas_dir = result.ctx.paths.root / "atlas"
        assert atlas_dir.is_dir()
        assert (atlas_dir / "journeys").is_dir()
        assert (atlas_dir / "maps").is_dir()
