"""Tests for hv chart explore command."""

from unittest.mock import patch

import pytest

from haiv import test
from haiv.errors import CommandError
from haiv.helpers.sessions import create_session
from haiv.test import Sandbox


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sandbox():
    """Sandbox with a mind session ready to explore."""
    sb = test.create_sandbox()
    root = sb.ctx.paths.root

    # Create minds directory for our test mind
    mind_dir = sb.ctx.paths.user.minds_dir / "pixel"
    (mind_dir / "work").mkdir(parents=True)

    # Create a session for the mind
    session = create_session(
        sb.ctx.paths.user.sessions_file,
        "test exploration",
        "pixel",
    )

    # Create atlas structure
    atlas = root / "atlas"
    (atlas / "journeys").mkdir(parents=True)
    (atlas / "maps").mkdir(parents=True)

    sb._session = session
    return sb


def _run(sandbox, command, capsys=None):
    """Run a chart explore command within the test session."""
    with patch.dict("os.environ", {"HV_SESSION": sandbox._session.id}):
        ctx = sandbox.run(command)
    if capsys:
        return capsys.readouterr().out
    return ctx


# =============================================================================
# Routing
# =============================================================================


class TestRouting:
    def test_routes_to_explore(self):
        match = test.require_routes_to("chart explore")
        assert match.file.name == "explore.py"


# =============================================================================
# Starting a journey
# =============================================================================


class TestStart:
    def test_prompts_for_name_when_none_given(self, sandbox: Sandbox, capsys):
        output = _run(sandbox, "chart explore", capsys)
        assert "--name" in output

    def test_prompts_for_name_preserving_goal(self, sandbox: Sandbox, capsys):
        output = _run(sandbox, 'chart explore --goal "understand hooks"', capsys)
        assert "--name" in output
        assert "understand hooks" in output

    def test_creates_journey_directory(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey --goal "test"')
        journey_dir = sandbox.ctx.paths.root / "atlas" / "journeys" / "test-journey"
        assert journey_dir.is_dir()

    def test_creates_research_log(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey --goal "test"')
        journey_dir = sandbox.ctx.paths.root / "atlas" / "journeys" / "test-journey"
        log = journey_dir / "001-research-log.md"
        assert log.exists()
        content = log.read_text()
        assert "pixel" in content
        assert "Research Log" in content

    def test_creates_exploration_state(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey --goal "test"')
        state_file = sandbox.ctx.paths.user.minds_dir / "pixel" / "work" / "exploration.json"
        assert state_file.exists()

    def test_errors_if_journey_exists(self, sandbox: Sandbox):
        journey_dir = sandbox.ctx.paths.root / "atlas" / "journeys" / "existing"
        journey_dir.mkdir(parents=True)
        with pytest.raises(CommandError, match="already exists"):
            _run(sandbox, "chart explore --name existing")

    def test_shows_example_journey(self, sandbox: Sandbox, capsys):
        output = _run(sandbox, 'chart explore --name test-journey', capsys)
        assert "example-journey" in output


# =============================================================================
# The cycle
# =============================================================================


class TestLog:
    def test_advances_to_research_logged(self, sandbox: Sandbox, capsys):
        _run(sandbox, 'chart explore --name test-journey')
        output = _run(sandbox, 'chart explore --log', capsys)
        assert "Research log recorded" in output

    def test_fails_without_active_journey(self, sandbox: Sandbox):
        with pytest.raises(CommandError, match="No active journey"):
            _run(sandbox, "chart explore --log")


class TestPlan:
    def test_advances_to_planned(self, sandbox: Sandbox, capsys):
        _run(sandbox, 'chart explore --name test-journey')
        _run(sandbox, 'chart explore --log')
        output = _run(sandbox, 'chart explore --plan', capsys)
        assert "--embark" in output

    def test_fails_from_wrong_state(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey')
        with pytest.raises(CommandError, match="Can't plan"):
            _run(sandbox, 'chart explore --plan')


class TestEmbark:
    def test_creates_entry_file(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey')
        _run(sandbox, 'chart explore --log')
        _run(sandbox, 'chart explore --plan')
        _run(sandbox, 'chart explore --embark src/haiv/cmd.py')
        entry = sandbox.ctx.paths.root / "atlas" / "journeys" / "test-journey" / "002.md"
        assert entry.exists()
        assert "cmd.py" in entry.read_text()

    def test_shows_slow_down_guidance(self, sandbox: Sandbox, capsys):
        _run(sandbox, 'chart explore --name test-journey')
        _run(sandbox, 'chart explore --log')
        _run(sandbox, 'chart explore --plan')
        output = _run(sandbox, 'chart explore --embark src/haiv/cmd.py', capsys)
        assert "Just this one" in output
        assert "--reflect" in output


class TestReflect:
    def test_advances_to_reflected(self, sandbox: Sandbox, capsys):
        _run(sandbox, 'chart explore --name test-journey')
        _run(sandbox, 'chart explore --log')
        _run(sandbox, 'chart explore --plan')
        _run(sandbox, 'chart explore --embark src/haiv/cmd.py')
        output = _run(sandbox, 'chart explore --reflect', capsys)
        assert "--plan" in output
        assert "--return" in output

    def test_fails_from_wrong_state(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey')
        _run(sandbox, 'chart explore --log')
        with pytest.raises(CommandError, match="Can't reflect"):
            _run(sandbox, 'chart explore --reflect')


class TestReturn:
    def test_clears_exploration_state(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey')
        _run(sandbox, 'chart explore --log')
        _run(sandbox, 'chart explore --plan')
        _run(sandbox, 'chart explore --embark src/haiv/cmd.py')
        _run(sandbox, 'chart explore --reflect')
        _run(sandbox, 'chart explore --return')
        state_file = sandbox.ctx.paths.user.minds_dir / "pixel" / "work" / "exploration.json"
        assert not state_file.exists()

    def test_shows_review_guidance(self, sandbox: Sandbox, capsys):
        _run(sandbox, 'chart explore --name test-journey')
        _run(sandbox, 'chart explore --log')
        _run(sandbox, 'chart explore --plan')
        _run(sandbox, 'chart explore --embark src/haiv/cmd.py')
        _run(sandbox, 'chart explore --reflect')
        output = _run(sandbox, 'chart explore --return', capsys)
        assert "annotations" in output
        assert "maps" in output.lower()
        assert "quest" in output.lower()


# =============================================================================
# Status
# =============================================================================


class TestStatus:
    def test_shows_current_state(self, sandbox: Sandbox, capsys):
        _run(sandbox, 'chart explore --name test-journey')
        _run(sandbox, 'chart explore --log')
        output = _run(sandbox, 'chart explore', capsys)
        assert "test-journey" in output
        assert "--plan" in output
