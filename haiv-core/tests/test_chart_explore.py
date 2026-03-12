"""Tests for hv chart explore command."""

from unittest.mock import patch

import pytest

from haiv import test
from haiv.errors import CommandError
from haiv.helpers.sessions import create_session
from haiv.paths import MindPaths
from haiv.test import Sandbox


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sandbox():
    """Sandbox with a mind session ready to explore."""
    sb = test.create_sandbox()
    atlas = sb.ctx.paths.atlas

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
    atlas.journeys_dir.mkdir(parents=True)
    atlas.maps_dir.mkdir(parents=True)

    sb._session = session
    return sb


def _run(sandbox, command, capsys=None):
    """Run a chart explore command within the test session."""
    with patch.dict("os.environ", {"HV_SESSION": sandbox._session.id}):
        ctx = sandbox.run(command)
    if capsys:
        return capsys.readouterr().out
    return ctx


def _mind_paths(sandbox: Sandbox) -> MindPaths:
    return MindPaths(
        root=sandbox.ctx.paths.user.minds_dir / "pixel",
        haiv_root=sandbox.ctx.paths.root,
    )


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
        atlas = sandbox.ctx.paths.atlas
        assert (atlas.journeys_dir / "test-journey").is_dir()

    def test_creates_research_log(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey --goal "test"')
        atlas = sandbox.ctx.paths.atlas
        log = atlas.journeys_dir / "test-journey" / "001-research-log.md"
        assert log.exists()
        content = log.read_text()
        assert "pixel" in content
        assert "Research Log" in content

    def test_creates_exploration_state(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey --goal "test"')
        mind = _mind_paths(sandbox)
        assert mind.work.exploration_file.exists()

    def test_errors_if_journey_exists(self, sandbox: Sandbox):
        atlas = sandbox.ctx.paths.atlas
        (atlas.journeys_dir / "existing").mkdir(parents=True)
        with pytest.raises(CommandError, match="already exists"):
            _run(sandbox, "chart explore --name existing")

    def test_shows_example_journey(self, sandbox: Sandbox, capsys):
        output = _run(sandbox, 'chart explore --name test-journey', capsys)
        assert "examples" in output
        assert "001-research-log.md" in output

    def test_populates_examples_from_bundled_assets(self, sandbox: Sandbox):
        _run(sandbox, 'chart explore --name test-journey')
        atlas = sandbox.ctx.paths.atlas
        assert atlas.examples_dir.is_dir()
        example_files = list(atlas.examples_dir.glob("*.md"))
        assert len(example_files) > 0

    def test_preserves_existing_examples(self, sandbox: Sandbox, capsys):
        atlas = sandbox.ctx.paths.atlas
        atlas.examples_dir.mkdir(parents=True)
        custom = atlas.examples_dir / "custom-example.md"
        custom.write_text("# Custom example\n")

        output = _run(sandbox, 'chart explore --name test-journey', capsys)
        assert "custom-example.md" in output
        # Should not have copied bundled files over custom content
        assert not (atlas.examples_dir / "001-research-log.md").exists()


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
        atlas = sandbox.ctx.paths.atlas
        entry = atlas.journeys_dir / "test-journey" / "002.md"
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
        mind = _mind_paths(sandbox)
        assert not mind.work.exploration_file.exists()

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
