"""Tests for hv start {mind} command."""

from pathlib import Path
from typing import Any
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from haiv import test
from haiv._infrastructure.args import ResolveRequest
from haiv.helpers.minds import Mind, MindPaths


# =============================================================================
# Helpers
# =============================================================================


def _mind(tmp_path: Path) -> Mind:
    mind_dir = tmp_path / "wren"
    mind_dir.mkdir(exist_ok=True)
    return Mind(paths=MindPaths(root=mind_dir))


def _resolve(tmp_path: Path):
    def resolve(req: ResolveRequest) -> Any:
        if req.resolver == "mind":
            return _mind(tmp_path)
        return req.value
    return resolve


def _setup(tmp_path: Path):
    def setup(ctx):
        ctx.paths._hv_root = tmp_path
    return setup


# =============================================================================
# Routing Tests
# =============================================================================


class TestStartRouting:
    """Test that 'start {mind}' routes correctly."""

    def test_routes_to_mind_file(self):
        """'start wren' routes to start/_mind_.py."""
        match = test.require_routes_to("start wren")
        assert match.file.name == "_mind_.py"
        assert "start" in str(match.file)

    def test_captures_mind_param(self):
        """Mind name is captured as param."""
        match = test.require_routes_to("start wren")
        assert "mind" in match.params
        assert match.params["mind"].value == "wren"


# =============================================================================
# Parsing Tests
# =============================================================================


class TestStartParsing:
    """Test start command argument parsing."""

    def test_parses_mind_name(self):
        """Mind name is accessible via args."""
        def mock_resolve(req: ResolveRequest) -> Any:
            return req.value

        ctx = test.parse("start wren", resolve=mock_resolve)
        assert ctx.args.get_one("mind") == "wren"

    def test_parses_task_flag(self):
        """--task flag is parsed."""
        def mock_resolve(req: ResolveRequest) -> Any:
            return req.value

        ctx = test.parse("start wren --task 'Fix bug'", resolve=mock_resolve)
        assert ctx.args.has("task")


# =============================================================================
# Execution Tests
# =============================================================================


class TestStartExecution:
    """Test that execute() delegates to ctx.tui.mind_launch()."""

    def test_calls_mind_launch(self, tmp_path):
        """Calls mind_launch with the mind name."""
        result = test.execute(
            "start wren",
            resolve=_resolve(tmp_path),
            setup=_setup(tmp_path),
        )
        mock_tui = cast(MagicMock, result.ctx.tui)
        mock_tui.mind_launch.assert_called_once()
        assert mock_tui.mind_launch.call_args[0][0] == "wren"

    def test_passes_task_when_provided(self, tmp_path):
        """Task flag is forwarded to mind_launch."""
        result = test.execute(
            'start wren --task "Fix bug"',
            resolve=_resolve(tmp_path),
            setup=_setup(tmp_path),
        )
        mock_tui = cast(MagicMock, result.ctx.tui)
        kwargs = mock_tui.mind_launch.call_args[1]
        assert kwargs["task"] == "Fix bug"

    def test_passes_none_task_when_omitted(self, tmp_path):
        """Task is None when --task flag not provided."""
        result = test.execute(
            "start wren",
            resolve=_resolve(tmp_path),
            setup=_setup(tmp_path),
        )
        mock_tui = cast(MagicMock, result.ctx.tui)
        kwargs = mock_tui.mind_launch.call_args[1]
        assert kwargs["task"] is None

    def test_passes_parent_from_env(self, tmp_path):
        """Parent session id is read from HV_SESSION env var."""
        with patch.dict("os.environ", {"HV_SESSION": "parent-123"}):
            result = test.execute(
                "start wren",
                resolve=_resolve(tmp_path),
                setup=_setup(tmp_path),
            )
        mock_tui = cast(MagicMock, result.ctx.tui)
        kwargs = mock_tui.mind_launch.call_args[1]
        assert kwargs["parent_id"] == "parent-123"

    def test_passes_empty_parent_when_no_env(self, tmp_path):
        """Parent is empty string when HV_SESSION not set."""
        with patch.dict("os.environ", {}, clear=True):
            result = test.execute(
                "start wren",
                resolve=_resolve(tmp_path),
                setup=_setup(tmp_path),
            )
        mock_tui = cast(MagicMock, result.ctx.tui)
        kwargs = mock_tui.mind_launch.call_args[1]
        assert kwargs["parent_id"] == ""
