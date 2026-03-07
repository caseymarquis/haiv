"""Tests for TerminalManager logic."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from haiv.errors import CommandError
from haiv.helpers.tui.terminal import TerminalManager
from haiv.wrappers.wezterm import Pane, PaneSize


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
    return TerminalManager(wezterm, Path("/home/user/my-project"), ["hv-tui"])


class TestTabTitleNaming:
    def test_hud_tab_prefix(self, manager):
        assert manager.hud_tab_prefix == "hv(my-project)"

    def test_hud_tab_title_with_mind(self, manager):
        assert manager._hud_tab_title("wren") == "hv(my-project):wren"

    def test_hud_tab_title_without_mind(self, manager):
        assert manager._hud_tab_title() == "hv(my-project)"

    def test_parked_tab_title(self, manager):
        assert manager._parked_tab_title("wren") == "~wren"


class TestFindHudPane:
    def test_finds_left_pane_in_hud_tab(self, manager, wezterm):
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="hv(my-project)", left_col=0),
            make_pane(pane_id=2, tab_title="hv(my-project)", left_col=40),
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
            make_pane(pane_id=1, tab_title="hv(my-project)", left_col=40),
        ]

        assert manager._find_hud_pane() is None

    def test_ignores_other_projects_hud(self, manager, wezterm):
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="hv(other-project)", left_col=0),
        ]

        assert manager._find_hud_pane() is None


class TestEnsureWorkspace:
    """Tests for the context-dependent startup matrix.

    | In WezTerm? | Window exists? | Action                          |
    |-------------|----------------|---------------------------------|
    | No          | N/A            | Launch WezTerm with 'hv start'  |
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
        assert "hv" in args
        assert "start" in args

    def test_in_wezterm_no_window_creates_one(self, manager, wezterm):
        """Inside WezTerm, no haiv window — create new window with layout."""
        wezterm.list_panes.return_value = [
            # _find_hud_pane — not found
            make_pane(pane_id=0, tab_title=""),
        ]
        wezterm.spawn.return_value = 10  # hud window pane
        wezterm.split_pane.return_value = 11

        with patch.dict("os.environ", {"TERM_PROGRAM": "WezTerm"}):
            manager.ensure_workspace()

        # Created new window with TUI command + project name
        wezterm.spawn.assert_called_once_with(
            new_window=True, cwd="/home/user/my-project", command=["hv-tui", "my-project"],
        )
        # Named hud tab
        wezterm.set_tab_title.assert_called_once_with("hv(my-project)", pane_id=10)
        # Split right for mind pane
        wezterm.split_pane.assert_called_once_with(
            10, direction="right", percent=50, cwd="/home/user/my-project",
        )
        # Focused hud pane
        wezterm.activate_pane.assert_called_with(10)

    def test_in_wezterm_window_exists_activates_it(self, manager, wezterm):
        """Inside WezTerm, haiv window exists — activate hud pane."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=42, tab_title="hv(my-project)", left_col=0),
            make_pane(pane_id=43, tab_title="hv(my-project)", left_col=40),
            make_pane(pane_id=44, tab_title="hv(my-project):buffer"),
        ]

        with patch.dict("os.environ", {"TERM_PROGRAM": "WezTerm"}):
            manager.ensure_workspace()

        wezterm.activate_pane.assert_called_once_with(42)
        wezterm.spawn.assert_not_called()
        wezterm.run_external.assert_not_called()


class TestGetActiveMindName:
    """Tests for TerminalManager.get_active_mind_name()."""

    def test_returns_mind_name_from_hud_tab(self, manager, wezterm):
        """Extracts mind name from 'hv(project):mind' tab title."""
        wezterm.list_panes.return_value = [
            make_pane(tab_title="hv(my-project):wren"),
        ]

        assert manager.get_active_mind_name() == "wren"

    def test_returns_none_when_no_mind_active(self, manager, wezterm):
        """Returns None when hud tab has no mind suffix."""
        wezterm.list_panes.return_value = [
            make_pane(tab_title="hv(my-project)"),
        ]

        assert manager.get_active_mind_name() is None

    def test_returns_none_when_no_hud_tab(self, manager, wezterm):
        """Returns None when no hud tab exists."""
        wezterm.list_panes.return_value = [
            make_pane(tab_title="other"),
        ]

        assert manager.get_active_mind_name() is None


class TestTrySendTextToMind:
    """Tests for try_send_text_to_mind — returns bool, never raises."""

    def test_sends_to_active_mind(self, manager, wezterm):
        """Finds the active mind's pane (right side of hud) and sends text."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="hv(my-project):wren", left_col=0),
            make_pane(pane_id=2, tab_title="hv(my-project):wren", left_col=40),
        ]

        result = manager.try_send_text_to_mind("wren", "hello")

        assert result is True
        wezterm.send_text.assert_called_once_with(2, "hello")

    def test_sends_to_parked_mind(self, manager, wezterm):
        """Finds a parked mind's pane by tab title ~{mind}."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="hv(my-project)", left_col=0),
            make_pane(pane_id=5, tab_title="~wren"),
        ]

        result = manager.try_send_text_to_mind("wren", "hello")

        assert result is True
        wezterm.send_text.assert_called_once_with(5, "hello")

    def test_returns_false_when_mind_not_found(self, manager, wezterm):
        """Returns False when no pane exists for the mind."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="hv(my-project)", left_col=0),
        ]

        result = manager.try_send_text_to_mind("wren", "hello")

        assert result is False
        wezterm.send_text.assert_not_called()

    def test_prefers_active_over_parked(self, manager, wezterm):
        """When mind is both active and parked (shouldn't happen), uses active."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="hv(my-project):wren", left_col=0),
            make_pane(pane_id=2, tab_title="hv(my-project):wren", left_col=40),
            make_pane(pane_id=5, tab_title="~wren"),
        ]

        manager.try_send_text_to_mind("wren", "hello")

        wezterm.send_text.assert_called_once_with(2, "hello")

    def test_submit_false_uses_bracketed_paste(self, manager, wezterm):
        """submit=False sends text with bracketed paste (no no_paste flag)."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=5, tab_title="~wren"),
        ]

        manager.try_send_text_to_mind("wren", "hello", submit=False)

        wezterm.send_text.assert_called_once_with(5, "hello")

    def test_submit_true_sends_text_then_newline(self, manager, wezterm):
        """submit=True sends text via paste, then \\n with no_paste to press Enter."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=5, tab_title="~wren"),
        ]

        manager.try_send_text_to_mind("wren", "hello", submit=True)

        assert wezterm.send_text.call_count == 2
        # First call: text via bracketed paste
        wezterm.send_text.assert_any_call(5, "hello")
        # Second call: newline with no_paste to trigger submit
        wezterm.send_text.assert_any_call(5, "\n", no_paste=True)

    def test_does_not_match_wrong_mind(self, manager, wezterm):
        """Active mind 'spark' doesn't match when looking for 'wren'."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="hv(my-project):spark", left_col=0),
            make_pane(pane_id=2, tab_title="hv(my-project):spark", left_col=40),
        ]

        result = manager.try_send_text_to_mind("wren", "hello")

        assert result is False
        wezterm.send_text.assert_not_called()


class TestSendTextToMind:
    """Tests for send_text_to_mind — raises CommandError on failure."""

    def test_sends_to_found_mind(self, manager, wezterm):
        """Delegates to try_send_text_to_mind on success."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=5, tab_title="~wren"),
        ]

        manager.send_text_to_mind("wren", "hello")

        wezterm.send_text.assert_called_once_with(5, "hello")

    def test_raises_when_mind_not_found(self, manager, wezterm):
        """Raises CommandError when no pane exists for the mind."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=1, tab_title="hv(my-project)", left_col=0),
        ]

        with pytest.raises(CommandError, match="wren"):
            manager.send_text_to_mind("wren", "hello")

    def test_passes_submit_flag_through(self, manager, wezterm):
        """submit flag is forwarded to the underlying send."""
        wezterm.list_panes.return_value = [
            make_pane(pane_id=5, tab_title="~wren"),
        ]

        manager.send_text_to_mind("wren", "hello", submit=True)

        assert wezterm.send_text.call_count == 2
