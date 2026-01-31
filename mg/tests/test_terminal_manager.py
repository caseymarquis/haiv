"""Tests for TerminalManager logic."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mg.helpers.tui.terminal import TerminalManager
from mg.wrappers.wezterm import Pane, PaneSize


def make_pane(
    *,
    pane_id: int = 1,
    tab_title: str = "",
    left_col: int = 0,
    window_id: int = 1,
    tab_id: int = 1,
    workspace: str = "default",
) -> Pane:
    """Create a Pane with sensible defaults for testing."""
    return Pane(
        pane_id=pane_id,
        workspace=workspace,
        tab_title=tab_title,
        left_col=left_col,
        window_id=window_id,
        tab_id=tab_id,
        size=PaneSize(rows=24, cols=80, pixel_width=800, pixel_height=600, dpi=96),
        title="",
        cwd="/home/user",
        cursor_x=0,
        cursor_y=0,
        cursor_shape="Default",
        cursor_visibility="Visible",
        top_row=0,
        window_title="",
        is_active=False,
        is_zoomed=False,
        tty_name="",
    )


@pytest.fixture
def wezterm():
    """Create a mock WezTerm instance."""
    return MagicMock()


@pytest.fixture
def manager(wezterm):
    """Create a TerminalManager with mocked WezTerm."""
    return TerminalManager(wezterm, Path("/home/user/my-project"))


class TestTabTitleNaming:
    def test_hud_tab_title(self, manager):
        assert manager.hud_tab_title == "mg(my-project)"

    def test_buffer_tab_title(self, manager):
        assert manager.buffer_tab_title == "mg(my-project):buffer"


class TestFindHudPane:
    def test_finds_left_pane_in_hud_tab(self, manager, wezterm):
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="mg(my-project)", left_col=0),
            make_pane(pane_id=2, tab_title="mg(my-project)", left_col=40),
        ]

        pane = manager._find_hud_pane()
        assert pane is not None
        assert pane.pane_id == 1

    def test_returns_none_when_no_hud_tab(self, manager, wezterm):
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="other"),
        ]

        assert manager._find_hud_pane() is None

    def test_ignores_right_pane_in_hud_tab(self, manager, wezterm):
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="mg(my-project)", left_col=40),
        ]

        assert manager._find_hud_pane() is None

    def test_ignores_other_projects_hud(self, manager, wezterm):
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="mg(other-project)", left_col=0),
        ]

        assert manager._find_hud_pane() is None


class TestEnsureWorkspace:
    """Tests for the context-dependent startup matrix.

    | In WezTerm? | Window exists? | Action                          |
    |-------------|----------------|---------------------------------|
    | No          | N/A            | Launch WezTerm with 'mg start'  |
    | Yes         | No             | Create new window, set up layout|
    | Yes         | Yes            | Activate hud pane               |
    """

    def test_not_in_wezterm_launches_instance(self, manager, wezterm):
        """Outside WezTerm — launch a new instance."""
        with patch.dict("os.environ", {}, clear=True):
            manager.ensure_workspace()

        wezterm.run_external.assert_called_once()
        args = wezterm.run_external.call_args[0][0]
        assert args[0] == "start"
        assert "mg" in args
        assert "start" in args

    def test_in_wezterm_no_window_creates_one(self, manager, wezterm):
        """Inside WezTerm, no mg window — create new window with layout."""
        wezterm.list_panes.side_effect = [
            # _find_hud_pane — not found
            [make_pane(pane_id=0, tab_title="")],
            # window_id lookup after spawn + split
            [make_pane(pane_id=10, window_id=5)],
        ]
        wezterm.spawn.side_effect = [10, 12]  # hud window pane, buffer tab pane
        wezterm.split_pane.return_value = 11

        with patch.dict("os.environ", {"TERM_PROGRAM": "WezTerm"}):
            manager.ensure_workspace()

        # Created new window
        wezterm.spawn.assert_any_call(new_window=True, cwd="/home/user/my-project")
        # Named hud tab
        wezterm.set_tab_title.assert_any_call("mg(my-project)", pane_id=10)
        # Split for mind pane
        wezterm.split_pane.assert_called_once_with(
            10, direction="right", percent=50, cwd="/home/user/my-project"
        )
        # Created and named buffer tab
        wezterm.spawn.assert_any_call(window_id=5, cwd="/home/user/my-project")
        wezterm.set_tab_title.assert_any_call("mg(my-project):buffer", pane_id=12)
        # Focused hud pane
        wezterm.activate_pane.assert_called_with(10)

    def test_in_wezterm_window_exists_activates_it(self, manager, wezterm):
        """Inside WezTerm, mg window exists — activate hud pane."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=42, tab_title="mg(my-project)", left_col=0),
            make_pane(pane_id=43, tab_title="mg(my-project)", left_col=40),
            make_pane(pane_id=44, tab_title="mg(my-project):buffer"),
        ]

        with patch.dict("os.environ", {"TERM_PROGRAM": "WezTerm"}):
            manager.ensure_workspace()

        wezterm.activate_pane.assert_called_once_with(42)
        wezterm.spawn.assert_not_called()
        wezterm.run_external.assert_not_called()
